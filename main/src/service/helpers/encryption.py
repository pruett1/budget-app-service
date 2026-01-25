import hashlib

def pwd_encrypt(password: str) -> str:
    sha_signature = hashlib.sha256(password.encode()).hexdigest()
    return sha_signature

def encode_s(data: str) -> str:
    return data

def decode_s(data: str) -> str:
    return data