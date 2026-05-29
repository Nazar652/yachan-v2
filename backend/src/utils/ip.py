import hashlib


def hash_ip(raw_ip: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{raw_ip}".encode()).hexdigest()
