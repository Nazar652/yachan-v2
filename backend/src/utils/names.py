from src.utils.tripcode import compute_tripcode


def parse_name(raw: str | None) -> tuple[str, str | None]:
    """Split a poster name field into (display name, tripcode).

    A `#password` suffix turns into a tripcode; the part before it is the name.
    """
    if not raw:
        return "Anonymous", None

    if "#" in raw:
        name, password = raw.split("#", 1)
        return (name.strip() or "Anonymous"), compute_tripcode(password)

    return (raw.strip() or "Anonymous"), None
