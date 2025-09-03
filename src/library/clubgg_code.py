# Python 3.8+
import base64
import html
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .gmail_auth import gmail_service_from_env

CLUBGG_QUERY = 'from:support@clubgg.com subject:"ClubGG Email Verification Code" newer_than:1d'

def fetch_clubgg_verification_code(since: datetime, timeout_ms: int = 120_000) -> str:
    """
    Poll Gmail for a ClubGG verification email that arrived AFTER `since`
    (with a 10s grace window), and return the 6-digit code.
    Raises RuntimeError on timeout.
    """
    gmail = gmail_service_from_env()
    deadline = time.time() + (timeout_ms / 1000.0)

    # Convert 'since' to epoch ms; accept messages with internalDate > since_ms - 10s
    # to tolerate minor server/client clock skews and delivery jitter.
    since_ms = _to_epoch_ms(since)
    floor_ms = since_ms - 10_000  # 10s grace

    while time.time() < deadline:
        lst = gmail.users().messages().list(
            userId="me",
            q=CLUBGG_QUERY,
            maxResults=10
        ).execute()

        for m in (lst.get("messages") or []):
            msg = gmail.users().messages().get(
                userId="me",
                id=m["id"],
                format="full"
            ).execute()

            internal_ms = int(msg.get("internalDate", "0"))
            if internal_ms <= floor_ms:
                continue  # too old for this login attempt

            text = _extract_text(msg)
            code = _extract_code_from_email_body(text)
            if code:
                return code

        time.sleep(3.0)

    raise RuntimeError("Timed out waiting for ClubGG verification email")


# ---------------- helpers ----------------

def _to_epoch_ms(dt: datetime) -> int:
    """datetime -> epoch ms (UTC). Accept naive as local; convert to UTC."""
    if dt.tzinfo is None:
        # treat naive as local time, convert to UTC ms
        dt = dt.astimezone()
    return int(dt.timestamp() * 1000)

def _extract_code_from_email_body(text: str) -> Optional[str]:
    """
    Prefer the 2nd <strong>...</strong> chunk; then any <strong>; then anywhere.
    """
    strongs = [ _clean_text(_html_decode(m.group(1)))
                for m in re.finditer(r"<strong\b[^>]*>([\s\S]*?)</strong>", text, flags=re.I) ]

    if len(strongs) >= 2:
        maybe = _pick_six_digits(strongs[1])
        if maybe:
            return maybe

    for s in strongs:
        maybe = _pick_six_digits(s)
        if maybe:
            return maybe

    # fallback: anywhere in plain text
    plain = _strip_tags(_html_decode(text))
    return _pick_six_digits(plain)

def _pick_six_digits(s: str) -> Optional[str]:
    m = re.search(r"\b(\d{6})\b", s)
    return m.group(1) if m else None

def _extract_text(msg: Dict[str, Any]) -> str:
    parts: List[str] = []

    def walk(p: Dict[str, Any]):
        if not p:
            return
        mime = p.get("mimeType")
        body = (p.get("body") or {})
        data = body.get("data")
        if mime in ("text/plain", "text/html") and data:
            parts.append(_decode_b64url(data))
        for child in (p.get("parts") or []):
            walk(child)

    payload = msg.get("payload") or {}
    walk(payload)

    subject = ""
    for h in (payload.get("headers") or []):
        if str(h.get("name", "")).lower() == "subject":
            subject = h.get("value") or ""
            break

    snippet = msg.get("snippet") or ""
    return "\n".join([subject] + parts + [snippet])

def _decode_b64url(b64url: str) -> str:
    b64 = b64url.replace("-", "+").replace("_", "/")
    pad = "=" * ((4 - (len(b64) % 4)) % 4)
    return base64.b64decode((b64 + pad).encode("ascii")).decode("utf-8", errors="replace")

def _html_decode(s: str) -> str:
    # handle common entities first, then general decode
    s = s.replace("&nbsp;", " ")
    return html.unescape(s)

def _strip_tags(s: str) -> str:
    return re.sub(r"</?[^>]+>", "", s)

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
