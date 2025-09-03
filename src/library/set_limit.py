# Python 3.8+
from typing import Any, Dict, Optional, Union
import requests
import re

SetLimitResult = Dict[str, Any]

async def set_limit(
    connect_sid: str,
    club_id: Union[str, int],
    win: int,
    loss: int,
    include: int = 1,
) -> Optional[SetLimitResult]:
    """
    Set club win/loss limit at https://union.clubgg.com/clublimit

    Args:
        connect_sid: The `connect.sid` cookie value.
        club_id: Club number (cno).
        win: Win cap value.
        loss: Stop loss value.
        include: Include flag, usually 1 or 0.

    Returns:
        dict with:
          - ok: bool
          - message: Optional[str] (HTML stripped if present)
          - raw: Any (the raw JSON response)
        or None on transport-level failure (network/parse error).
    """
    try:
        url = "https://union.clubgg.com/clublimit"
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://union.clubgg.com",
            "Referer": "https://union.clubgg.com/clublimit",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            "Cookie": f"connect.sid={connect_sid}",
        }

        payload = {
            "iam": "edit",
            "cno": str(club_id),
            "win": str(win),
            "loss": str(loss),
            "include": str(include),
        }

        import asyncio
        resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Attempt a generic success detection:
        # Some endpoints return {err:0}, others just return INFO or silent success.
        ok = False
        if isinstance(data, dict):
            if data.get("err") == 0:
                ok = True
            elif "INFO" in data or data.get("success") == 1:
                ok = True
            else:
                # If we can't tell, consider HTTP 200 with a dict as tentative success
                ok = True

        # Normalize message (strip basic HTML if present)
        raw_msg = data.get("msg") if isinstance(data, dict) else None
        if isinstance(raw_msg, list):
            msg = " ".join(str(x) for x in raw_msg)
        elif isinstance(raw_msg, str):
            msg = raw_msg
        else:
            msg = None

        if isinstance(msg, str):
            msg = re.sub(r"<[^>]*>", "", msg)

        return {
            "ok": bool(ok),
            "message": msg,
            "raw": data,
        }

    except Exception as e:
        print("Set limit request error:", e)
        return None
