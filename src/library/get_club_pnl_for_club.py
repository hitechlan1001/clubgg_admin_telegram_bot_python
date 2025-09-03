# src/library/get_club_pnl_for_club.py
from __future__ import annotations

from typing import Any, Dict, Optional

import requests


def _parse_num(n: Optional[str]) -> float:
    """
    Convert strings like "90,900" -> 90900.0.
    Returns 0 on None/invalid.
    """
    if n is None:
        return 0.0
    try:
        v = float(str(n).replace(",", "").strip())
        return v
    except Exception:
        return 0.0


async def get_club_pnl_for_club(
    backend_id: str,
    connect_sid: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch ring & tournament P&L for a single club by backendId (cno).

    Returns:
        {
          "publicId": str,      # r.f1
          "ringPnl": float,     # r.f4 (Ring Game P&L)
          "tourneyPnl": float,  # r.f5 (Tournament P&L)
        }
        or None if not found / request error.
    """
    try:
        url = "https://union.clubgg.com/clublist"
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://union.clubgg.com",
            "Referer": "https://union.clubgg.com/clublist",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            ),
            "Cookie": f"connect.sid={connect_sid}",
        }

        def _find_in(resp_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            for r in (resp_json.get("DATA") or []):
                # cno is numeric in the API; compare as strings for safety
                if str(r.get("cno")) == str(backend_id):
                    return {
                        "publicId": str(r.get("f1", "")),
                        "ringPnl": _parse_num(r.get("f4")),   # Ring Game P&L
                        "tourneyPnl": _parse_num(r.get("f5")),  # Tournament P&L
                    }
            return None

        # first page
        first_payload = {
            "iam": "list",
            "clubnm": "",
            "cur_page": "1",
            "clubmn": "clubnm",
            "acs": "1",
        }
        import asyncio
        first = await asyncio.to_thread(requests.post, url, headers=headers, data=first_payload, timeout=30)
        data_first = first.json()

        tot_pages = int(data_first.get("PAGE", {}).get("tot_pages") or 1)
        hit = _find_in(data_first)
        if hit:
            return hit

        # subsequent pages
        for p in range(2, tot_pages + 1):
            payload = {
                "iam": "list",
                "clubnm": "",
                "cur_page": str(p),
                "clubmn": "clubnm",
                "acs": "1",
            }
            resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)
            hit = _find_in(resp.json())
            if hit:
                return hit

        return None

    except Exception as e:
        print("get_club_pnl_for_club error:", e)
        return None
