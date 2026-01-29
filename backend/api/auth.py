from passlib.context import CryptContext
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from .config import ApiConfig

# Support multiple schemes for backward compatibility
# pbkdf2_sha256 is the new default
# argon2 and bcrypt are kept for verifying existing users
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "argon2", "bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    cfg = ApiConfig.from_env()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, cfg.SECRET_KEY, algorithm=cfg.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    cfg = ApiConfig.from_env()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=cfg.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, cfg.SECRET_KEY, algorithm=cfg.ALGORITHM)
    return encoded_jwt

def generate_api_key():
    """
    Generate a secure random API key with a prefix.
    Format: sk_live_<48 hex chars>
    """
    random_part = secrets.token_hex(24)
    return f"sk_live_{random_part}"

def hash_api_key(api_key: str):
    """
    Hash the API key for storage.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()
