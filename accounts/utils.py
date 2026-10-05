def get_user_initials(name: str) -> str:
    """Return up to two initials for a user's display name."""
    parts = name.strip().split()
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][0].upper()
    return f'{parts[0][0]}{parts[-1][0]}'.upper()
