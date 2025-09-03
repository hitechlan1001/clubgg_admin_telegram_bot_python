# Python 3.8
from typing import Dict, Optional
from telegram import Update

# You should implement these in your Python roles module
# with the same semantics as your TS version.
from src.utils.roles import get_user_role, has_permission
# get_user_role(user_id: int) -> Optional[{"userId": int, "role": str, "clubs": Optional[list[int]]}]
# has_permission(user_id: int, capability: str) -> bool

# Command -> capability mapping (kept 1:1 with your TS)
CAP_MAP: Dict[str, str] = {
    "cl": "view-club-limit",
    "addwl": "set-club-limit",
    "subwl": "set-club-limit",
    "setwl": "set-club-limit",
    "addsl": "set-club-limit",
    "subsl": "set-club-limit",
    "setsl": "set-club-limit",
    "scr": "send-credit",
    "ccr": "claim-credit",
}

def can_manage_club(update: Update, command: str, club_id: int) -> Dict[str, Optional[str]]:
    """
    Authorization + scope check.

    Args:
        update: telegram.Update (to read effective_user)
        command: command key, e.g. "cl", "addwl", "scr", "ccr"
        club_id: numeric backend club id to check (after your resolve/map)

    Returns:
        {"allowed": bool, "reason": Optional[str]}
    """
    user = update.effective_user
    if not user or not getattr(user, "id", None):
        return {"allowed": False, "reason": "User not found"}

    user_id = int(user.id)
    role_obj = get_user_role(user_id)
    if not role_obj:
        return {"allowed": False, "reason": "You are not authorized to use this bot"}

    # Map command to capability and check role permission
    cap = CAP_MAP.get(command, command)
    if not has_permission(user_id, cap):
        return {"allowed": False, "reason": "Command not permitted for your role"}

    # Scope check: Union Head can access all, others must have the club in their list
    if role_obj.get("role") != "Union Head":
        clubs = role_obj.get("clubs") or []
        try:
            # Ensure ints for comparison
            clubs_int = [int(x) for x in clubs]
        except Exception:
            clubs_int = []
        if int(club_id) not in clubs_int:
            return {"allowed": False, "reason": "You do not have permission to access this club"}

    return {"allowed": True, "reason": None}
