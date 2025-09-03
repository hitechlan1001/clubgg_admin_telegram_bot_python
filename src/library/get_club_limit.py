# src/library/get_club_limit.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict

import requests


@dataclass
class ClubLimitInfo:
    img: str
    nm: str
    id: str
    master: str
    win: str
    loss: str
    include: Any  # bool or str per backend variability


@dataclass
class ClubLimitResponse:
    INFO: ClubLimitInfo


def _safe_make_info(obj: Dict[str, Any]) -> Optional[ClubLimitInfo]:
    try:
        return ClubLimitInfo(
            img=str(obj.get("img", "")),
            nm=str(obj.get("nm", "")),
            id=str(obj.get("id", "")),
            master=str(obj.get("master", "")),
            win=str(obj.get("win", "")),
            loss=str(obj.get("loss", "")),
            include=obj.get("include"),
        )
    except Exception:
        return None


async def get_club_limit(club_id: str, connect_sid: str) -> Optional[ClubLimitResponse]:
    """
    Fetch weekly club limits (stop-loss, win cap, etc.)
    Mirrors TS getClubLimit(clubId, connectSid).

    Args:
        club_id: Club ID (cno)
        connect_sid: Session cookie value

    Returns:
        ClubLimitResponse or None if request/shape fails.
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
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            ),
            "Cookie": f"connect.sid={connect_sid}",
        }

        payload = {
            "iam": "view",
            "cno": str(club_id),
        }

        # Keep a sane timeout so we don't hang indefinitely
        import asyncio
        resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)

        # API returns JSON with INFO; don't raise_for_status because
        # the server often returns 200 with error payloads.
        data = resp.json()

        if not isinstance(data, dict) or "INFO" not in data:
            print("Unexpected clublimit response shape:", data)
            return None

        info = _safe_make_info(data["INFO"])
        if not info:
            print("Failed to parse INFO object:", data.get("INFO"))
            return None

        return ClubLimitResponse(INFO=info)

    except requests.RequestException as e:
        # Better diagnostics on HTTP layer problems
        try:
            # Attempt to extract partial info if available
            status = getattr(e.response, "status_code", None)
            headers = getattr(e.response, "headers", None)
            body = None
            if e.response is not None:
                ct = e.response.headers.get("content-type", "")
                if ct.startswith("application/json"):
                    body = e.response.json()
                else:
                    body = e.response.text[:500]
            print("Club limit request error:", {"status": status, "headers": headers, "data": body})
        except Exception:
            print("Club limit request error:", str(e))
        return None
    except Exception as e:
        print("Club limit request error:", str(e))
        return None
