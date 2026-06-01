from src.utils.ip import hash_ip


def test_hash_is_deterministic():
    assert hash_ip("1.2.3.4", "salt") == hash_ip("1.2.3.4", "salt")


def test_hash_is_sha256_hex():
    digest = hash_ip("1.2.3.4", "salt")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_different_salt_changes_hash():
    assert hash_ip("1.2.3.4", "a") != hash_ip("1.2.3.4", "b")


def test_different_ip_changes_hash():
    assert hash_ip("1.2.3.4", "salt") != hash_ip("5.6.7.8", "salt")
