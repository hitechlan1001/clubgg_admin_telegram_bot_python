from typing import Dict, List, Optional, TypedDict, Union

# Define Role type
Role = str  # could be Literal["Union Head", "Region Head", "Club Owner"]

class UserRole(TypedDict, total=False):
    userId: int
    role: Role
    clubs: List[int]  # optional: Club IDs this user can manage/view


# Users & their roles
user_roles: List[UserRole] = [
    {"userId": 7978542634, "role": "Union Head"},
    {"userId": 846248501, "role": "Union Head"},
    {"userId": 326695362, "role": "Union Head"},
    {"userId": 7978542634, "role": "Region Head", "clubs": [250793, 102, 103]},
    {"userId": 7978542634, "role": "Club Owner", "clubs": [250793]},
    # Add more as needed
]

# Permissions per role
permissions: Dict[Role, List[str]] = {
    "Union Head": [
        "set-global-limit",
        "set-region-limit",
        "set-club-limit",
        "send-credit",
        "claim-credit",
        "view-club-limit",
    ],
    "Region Head": ["set-region-limit", "set-club-limit", "view-club-limit"],
    "Club Owner": ["view-club-limit"],  # 👈 only this
}

# Command → capability mapping
COMMAND_TO_CAP: Dict[str, str] = {
    "addwl": "set-club-limit",
    "subwl": "set-club-limit",
    "setwl": "set-club-limit",
    "addsl": "set-club-limit",
    "subsl": "set-club-limit",
    "setsl": "set-club-limit",
    "cl": "view-club-limit",   # 👈 map /cl to "view-club-limit"
    "scr": "send-credit",
    "ccr": "claim-credit",
}


def has_permission(user_id: int, command: str) -> bool:
    """
    Check if user has permission to run a given command.
    """
    user = next((u for u in user_roles if u["userId"] == user_id), None)
    if not user:
        return False

    cap = COMMAND_TO_CAP.get(command, command)
    return cap in permissions[user["role"]]


def get_user_role(user_id: int) -> Optional[UserRole]:
    """
    Get the user role definition.
    """
    return next((u for u in user_roles if u["userId"] == user_id), None)
