import base64
import hashlib

# a tripcode proves authorship of a name without accounts: the same password
# always yields the same code, so readers can recognise a returning poster
_TRIP_LENGTH = 10


def compute_tripcode(password: str) -> str:
    digest = hashlib.sha256(password.encode()).digest()
    code = base64.b64encode(digest).decode().replace("+", "x").replace("/", "y")
    return "!" + code[:_TRIP_LENGTH]
