# src/library/claim_credit.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Optional

import requests


@dataclass
class ClaimCreditResult:
    ok: bool
    message: Optional[str] = None
    success_club_ids: Optional[List[str]] = None
    raw: Any = None


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]*>", "", s)


async def claim_credit(club_id: str, connect_sid: str, amount: int) -> Optional[ClaimCreditResult]:
    """
    Claim credits from ClubGG union counter.

    Args:
        club_id: Club ID string (e.g., "320052")
        connect_sid: connect.sid cookie value
        amount: integer amount to claim

    Returns:
        ClaimCreditResult on success, or None on request error.
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
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            ),
            "Cookie": f"connect.sid={connect_sid}",
        }

        payload = {
            "iam": "claimback",
            "clubstr": f"{club_id},{amount}",
        }

        # keep timeouts sane to avoid hanging forever
        import asyncio
        resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)
        # don't raise for status; the API sometimes returns 200 with error JSON
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

        msg_field = data.get("msg")
        if isinstance(msg_field, list):
            msg_text = " ".join(map(str, msg_field))
        else:
            msg_text = str(msg_field) if msg_field is not None else None

        success_list = data.get("success_list") or []
        if not isinstance(success_list, list):
            success_list = []

        ok = (isinstance(data.get("err"), int) and data.get("err") == 0) or (
            len(success_list) > 0 and club_id in success_list
        )

        return ClaimCreditResult(
            ok=ok,
            message=_strip_tags(msg_text) if isinstance(msg_text, str) else None,
            success_club_ids=[str(x) for x in success_list],
            raw=data,
        )

    except Exception as e:
        # mirror TS behavior: log and return None
        print("Claim credit request error:", e)
        return None
