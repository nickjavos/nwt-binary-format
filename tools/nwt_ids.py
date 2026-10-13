"""Instrument IDs for sources that carry none (symbol directories, option series)."""

import hashlib


def instrument_id_for(namespace: str, key: str) -> int:
    """Return the instrument ID for `key` (for example "AAPL") in `namespace` (for example "XNAS").

    Deterministic, non-zero, and unchanged when the source file gains or loses
    other rows. Two keys can collide; the caller checks for collisions.
    """
    # NUL separates the parts because it cannot occur in NWT text, so ("A", "B:C") and ("A:B", "C") differ.
    digest = hashlib.sha256(f"{namespace}\0{key}".encode()).digest()
    # 63 bits: the ID also fits a signed 64-bit integer.
    return (int.from_bytes(digest[:8], "big") >> 1) or 1
