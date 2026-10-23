"""Semillas derivadas estables; no utiliza hash() del proceso Python."""
import hashlib


def derive_seed(seed, stream):
    return int.from_bytes(hashlib.sha256(f'oak-v1:{seed}:{stream}'.encode()).digest()[:4], 'big') % 2147483647
