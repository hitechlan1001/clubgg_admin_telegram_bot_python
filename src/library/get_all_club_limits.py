# src/library/get_all_club_limits.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests


@dataclass
class ClubLimitData:
    num: str
    uno: str
    cno: int
    non: int
    f1: str  # Public ID
    f2: str  # Club Name
    f3: str  # Owner
    f4: str  # Ring Game P&L
    f4_ty: int
    f5: str  # Tournament P&L
    f5_ty: int
    f6: str  # Loss Limit
    f7: str  # Win Limit
    f8: str  # Include Status
    edit_yn: int


@dataclass
class AllClubLimitsResponse:
    COMM: Dict[str, Any]
    PAGE: Dict[str, Any]
    DATA: List[ClubLimitData]


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


def _safe_make_club_data(obj: Dict[str, Any]) -> Optional[ClubLimitData]:
    try:
        return ClubLimitData(
            num=str(obj.get("num", "")),
            uno=str(obj.get("uno", "")),
            cno=int(obj.get("cno", 0)),
            non=int(obj.get("non", 0)),
            f1=str(obj.get("f1", "")),
            f2=str(obj.get("f2", "")),
            f3=str(obj.get("f3", "")),
            f4=str(obj.get("f4", "")),
            f4_ty=int(obj.get("f4_ty", 0)),
            f5=str(obj.get("f5", "")),
            f5_ty=int(obj.get("f5_ty", 0)),
            f6=str(obj.get("f6", "")),
            f7=str(obj.get("f7", "")),
            f8=str(obj.get("f8", "")),
            edit_yn=int(obj.get("edit_yn", 0)),
        )
    except Exception:
        return None


async def get_all_club_limits(connect_sid: str) -> Optional[AllClubLimitsResponse]:
    """
    Fetch all club limits data from union.clubgg.com/clublimit
    
    Args:
        connect_sid: Session cookie value
        
    Returns:
        AllClubLimitsResponse or None if request fails
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
            "iam": "list",
            "clubnm": "",
            "cur_page": "1",
            "column": "ring",
            "asc": "2",
        }

        import asyncio
        resp = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=30)
        
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}")
            return None

        data = resp.json()
        
        if not isinstance(data, dict) or "DATA" not in data:
            print("Unexpected response shape:", data)
            return None

        # Parse all club data
        club_data_list = []
        for item in data.get("DATA", []):
            club_data = _safe_make_club_data(item)
            if club_data:
                club_data_list.append(club_data)

        return AllClubLimitsResponse(
            COMM=data.get("COMM", {}),
            PAGE=data.get("PAGE", {}),
            DATA=club_data_list
        )

    except Exception as e:
        print("get_all_club_limits error:", e)
        return None
