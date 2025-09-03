# Python 3.8+
from typing import Any, Dict, List, Optional, Union
import requests

SendCreditResult = Dict[str, Any]

async def send_credit(
    connect_sid: str,
    club_id: str,
    amount: int,
    note: str = ""
) -> Optional[SendCreditResult]:
    """
    Send credits to a club via union.clubgg.com/counteru.

    Args:
        connect_sid: The value of the `connect.sid` cookie.
        club_id: Club backend id (string). You may map your public ID to this beforehand.
        amount: Integer amount to send.
        note: Optional note string.

    Returns:
        A dict with:
          - ok: bool
          - message: Optional[str] (HTML stripped)
          - successClubIds: List[str]
          - balance: Optional[Union[int,float]]
          - raw: Any (full JSON response)
        or None on transport-level failure.
    """
    try:
        url = "https://union.clubgg.com/counteru"
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://union.clubgg.com",
            "Referer": "https://union.clubgg.com/counteru",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            "Cookie": f"connect.sid={connect_sid}",
        }

        payload = {
            "iam": "sendout",
            # supports multiple like "id,amt|id,amt" if needed
            "clubstr": f"{club_id},{amount}",
            "note": note,
        }

        import asyncio
        resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Normalize
        raw_msg = data.get("msg")
        if isinstance(raw_msg, list):
            msg = " ".join(str(x) for x in raw_msg)
        else:
            msg = str(raw_msg) if raw_msg is not None else None

        # Strip simple HTML tags if present
        if isinstance(msg, str):
            import re
            msg = re.sub(r"<[^>]*>", "", msg)

        success_list = data.get("success_list") or []
        if not isinstance(success_list, list):
            success_list = []

        ok = (
            (isinstance(data.get("err"), int) and data.get("err") == 0)
            or (club_id in success_list)
        )

        balance = None
        dat = data.get("data")
        if isinstance(dat, dict):
            balance = dat.get("balance", None)

        return {
            "ok": bool(ok),
            "message": msg,
            "successClubIds": success_list,
            "balance": balance,
            "raw": data,
        }

    except Exception as e:
        # Transport / parsing error
        print("Send credit request error:", e)
        return None
