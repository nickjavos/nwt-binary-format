
import hashlib


def instrument_id_for(namespace: str, key: str) -> int:
    digest = hashlib.sha256(f"{namespace}\0{key}".encode()).digest()
    return (int.from_bytes(digest[:8], "big") >> 1) or 1
