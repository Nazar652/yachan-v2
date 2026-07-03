import re

# slug is interpolated into raw ddl, so it must be strictly validated here to prevent sql injection
_SLUG_RE = re.compile(r"^[a-z0-9_]{1,20}$")


def post_number_sequence_name(slug: str) -> str:
    if not _SLUG_RE.fullmatch(slug):
        raise ValueError(f"invalid board slug: {slug!r}")
    return f"post_number_seq_{slug}"
