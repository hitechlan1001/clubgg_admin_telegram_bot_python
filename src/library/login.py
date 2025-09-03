# src/library/login.py
import os
import json
import time
import random
import logging
import asyncio
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

# If you implemented the Gmail OTP helper in Python as suggested:
#   src/gmail/mfa.py -> fetch_clubgg_verification_code(since: datetime, timeout_seconds: int) -> str
from datetime import datetime
try:
    from src.library.mfa import fetch_clubgg_verification_code  # noqa: F401
except Exception:
    fetch_clubgg_verification_code = None  # type: ignore

load_dotenv()
logger = logging.getLogger(__name__)

# === ENV / CONSTANTS ===
API_KEY = os.getenv("CAPSOLVER_API_KEY")
SITE_KEY = "6LfGLOwpAAAAAB_yx0Fp06dwDxYIsQ3WD5dSXKbQ"
PAGE_URL = "https://union.clubgg.com/"
PAGE_ACTION = "submit"

LOGIN_URL = "https://union.clubgg.com/login_submit"
LOGIN_ID = os.getenv("UNION_LOGIN_ID")
LOGIN_PWD = os.getenv("UNION_LOGIN_PWD")

UNION_RECAPTCHA_BACKEND = os.getenv("UNION_RECAPTCHA_BACKEND")

BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://union.clubgg.com",
    "Referer": "https://union.clubgg.com/login",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
}

# =========================
# Helpers
# =========================
def _parse_set_cookie_to_map(set_cookie_values: Optional[list[str]]) -> Dict[str, str]:
    """
    Parse Set-Cookie header values into a name->value map.
    NOTE: requests already parses cookies into response.cookies; prefer that.
    This is here only for parity with the TS version.
    """
    out: Dict[str, str] = {}
    if not set_cookie_values:
        return out
    for line in set_cookie_values:
        first_pair = line.split(";")[0]
        if "=" not in first_pair:
            continue
        name, value = first_pair.split("=", 1)
        out[name.strip()] = value.strip()
    return out

def _get_recaptcha_token_from_capsolver() -> Optional[str]:
    """
    Use CapSolver ReCaptchaV3EnterpriseTaskProxyLess to get a token.
    Return None if it fails or times out.
    """
    if not API_KEY:
        return None
    try:
        create_payload = {
            "clientKey": API_KEY,
            "task": {
                "type": "ReCaptchaV3EnterpriseTaskProxyLess",
                "websiteURL": PAGE_URL,
                "websiteKey": SITE_KEY,
                "pageAction": PAGE_ACTION,
            },
        }
        create = requests.post(
            "https://api.capsolver.com/createTask",
            json=create_payload,
            timeout=20,
        ).json()
        task_id = create.get("taskId")
        if not task_id:
            return None

        # poll up to ~90s (every 3s)
        for _ in range(30):
            time.sleep(3)
            res = requests.post(
                "https://api.capsolver.com/getTaskResult",
                json={"clientKey": API_KEY, "taskId": task_id},
                timeout=20,
            ).json()
            if res.get("status") == "ready":
                return (res.get("solution") or {}).get("gRecaptchaResponse")
        return None
    except Exception:
        return None


def _get_recaptcha_token_forever_from_capsolver() -> str:
    attempt = 0
    while True:
        attempt += 1
        token = _get_recaptcha_token_from_capsolver()
        if token:
            return token
        backoff_ms = min(30_000, 1000 * attempt)  # 1s, 2s, … up to 30s
        logger.warning("CapSolver attempt %s failed; retrying in %sms", attempt, backoff_ms)
        time.sleep(backoff_ms / 1000.0)


async def _fetch_email_mfa_code(since: datetime, timeout_ms: int = 120_000) -> str:
    """
    Fetch the ClubGG 6-digit code from Gmail using src/library/mfa.py.
    mfa.fetch_clubgg_verification_code(since, timeout) is blocking → run in thread.
    """
    if not fetch_clubgg_verification_code:
        raise RuntimeError(
            "Gmail MFA helper missing. Implement src/library/mfa.py and export "
            "`fetch_clubgg_verification_code(since, timeout)`."
        )
    # call with positional args: (since, timeout_seconds)
    code = await asyncio.to_thread(fetch_clubgg_verification_code, since, timeout_ms // 1000)
    if not code:
        raise TimeoutError("No verification code received in time")
    return code


def _is_recaptcha_failed(payload: dict) -> bool:
    msg = str(payload.get("msg", ""))
    return (
        payload.get("err") == -2
        or "recaptcha" in msg.lower()
        or "please" in msg.lower() and "recaptcha" in msg.lower()
    )


def _is_mfa_required(payload: dict) -> bool:
    data = payload.get("data") or {}
    return data.get("code") == "REQUIRED_MFA_CODE" or bool(
        (data.get("description") or {}).get("codeSent") is True
    )


def _is_unmatched_verification_code(payload: dict) -> bool:
    data = payload.get("data") or {}
    message = str(data.get("message", ""))
    return data.get("code") == "UNMATCHED_VERIFICATION_CODE" or (
        "unmatched" in message.lower()
        and "verification" in message.lower()
        and "code" in message.lower()
    )


# =========================
# Main login flow
# =========================
async def login_and_get_sid() -> str:
    """
    Performs the 2-step login with reCAPTCHA v3 and optional MFA via email.
    Returns the 'connect.sid' cookie value on success.
    """
    if not LOGIN_ID or not LOGIN_PWD:
        raise RuntimeError("UNION_LOGIN_ID / UNION_LOGIN_PWD not set in environment")

    session = requests.Session()

    # ---- STEP 1: retry UNTIL reCAPTCHA is accepted ----
    step_attempt = 0
    while True:
        step_attempt += 1
        # You can choose either: _get_recaptcha_token_forever_from_capsolver() or _get_recaptcha_token_forever_hybrid()
        recaptcha = _get_recaptcha_token_forever_from_capsolver()

        form = {
            "id": LOGIN_ID,
            "pwd": LOGIN_PWD,
            "recaptcha_res": recaptcha,
            "mfacode": "",
            "os": "Windows",
            "os_ver": "10",
            "method_type": "",
        }

        r1 = session.post(LOGIN_URL, data=form, headers=BASE_HEADERS)
        # Do not raise; we mimic the TS `validateStatus: () => true`
        try:
            step1 = r1.json()
        except Exception:
            # Some unexpected response
            raise RuntimeError(f"Unexpected non-JSON response: {r1.status_code} {r1.text[:500]}")

        if _is_recaptcha_failed(step1):
            backoff = min(5000, 100 * step_attempt)
            logger.warning(
                "Step-1 reCAPTCHA rejected (attempt %s); retrying in %sms",
                step_attempt,
                backoff,
            )
            time.sleep(backoff / 1000.0)
            continue

        # cookies from response (requests parses Set-Cookie)
        connect_sid = r1.cookies.get("connect.sid")
        # If no MFA requested and err==0, we’re done
        if connect_sid and step1.get("err") == 0 and not (step1.get("data") or {}).get("code"):
            return connect_sid

        # If MFA is required, break out to STEP 2
        if _is_mfa_required(step1):
            break

        # Otherwise we don't know this shape
        raise RuntimeError(f"Unexpected login response (step 1): {json.dumps(step1)[:800]}")

    # ---- STEP 2: MFA loop ----
    mfa_requested_at = datetime.now()
    step2_attempt = 0
    mfa_code = None  # Store the MFA code once fetched
    
    while True:
        step2_attempt += 1
        
        # Only fetch MFA code once per login attempt
        if mfa_code is None:
            mfa_code = await _fetch_email_mfa_code(mfa_requested_at)  # waits/polls until code available
            logger.info(f"🔐 MFA code fetched: {mfa_code}")
        
        recaptcha = _get_recaptcha_token_forever_from_capsolver()  # usually ignored in step2, but safe

        form2 = {
            "id": LOGIN_ID,
            "pwd": LOGIN_PWD,
            "recaptcha_res": recaptcha,
            "mfacode": mfa_code,
            "os": "Windows",
            "os_ver": "10",
            "method_type": "",
        }

        r2 = session.post(LOGIN_URL, data=form2, headers=BASE_HEADERS)
        try:
            step2 = r2.json()
        except Exception:
            raise RuntimeError(f"Unexpected non-JSON response (step 2): {r2.status_code} {r2.text[:500]}")

        if _is_recaptcha_failed(step2):
            backoff = min(5000, 100 * step2_attempt)
            logger.warning(
                "Step-2 reCAPTCHA rejected (attempt %s); retrying in %sms",
                step2_attempt,
                backoff,
            )
            time.sleep(backoff / 1000.0)
            continue

        if _is_unmatched_verification_code(step2):
            logger.warning(
                "MFA code unmatched (attempt %s); fetching a new code...",
                step2_attempt,
            )
            time.sleep(2)
            # Reset MFA code to fetch a new one
            mfa_code = None
            mfa_requested_at = datetime.now()
            continue

        # Grab cookies and return
        connect_sid = r2.cookies.get("connect.sid")
        if connect_sid:
            return connect_sid

        # Sometimes Set-Cookie headers may not be parsed (rare); try manual parse
        # NOTE: requests doesn't expose getlist on headers; use raw if available
        try:
            set_cookie_values = r2.raw.headers.get_all("Set-Cookie")  # type: ignore[attr-defined]
        except Exception:
            set_cookie_values = None
        cookie_map = _parse_set_cookie_to_map(set_cookie_values)
        if cookie_map.get("connect.sid"):
            return cookie_map["connect.sid"]

        # If we reach here, response didn't match expected success shape
        raise RuntimeError(f"Unexpected login response (step 2): {json.dumps(step2)[:800]}")


# Optional: quick manual run
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sid = asyncio.run(login_and_get_sid())
    print("connect.sid:", sid)
