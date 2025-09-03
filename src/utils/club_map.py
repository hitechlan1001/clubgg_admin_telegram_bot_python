# Python 3.8

# Mapping from publicId (user-facing) -> backendId (cno)
club_id_map = {
    "492536": "320052",
    "205255": "314660",
    "664054": "309432",
    "451214": "320050",
    "865840": "309424",
    "819983": "188141",
    "949506": "250793",
}

def resolve_club_id(user_input: str) -> str:
    """
    Resolve a user-facing club ID into the backend ID.

    Args:
        user_input: str, the ID user typed in.

    Returns:
        str: backend clubId (if mapped) or original user_input.
    """
    return club_id_map.get(user_input, user_input)
