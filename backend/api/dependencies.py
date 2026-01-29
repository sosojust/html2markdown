from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .config import ApiConfig
from .ratelimit import RateLimiter
from .auth import hash_api_key
from .db import get_db
from sqlalchemy.future import select
from .models.entity import ApiKey, User
from .repositories.base import ApiKeyRepository, UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Global limiter for now
# We need to load config for limit values, but RateLimiter is stateful?
# If we re-instantiate RateLimiter every time, we lose state (memory storage).
# So RateLimiter MUST be global or singleton.
# But we can load config values dynamically?
# RateLimiter takes limit/window in __init__.
# So we have to initialize it once.
_cfg_for_limiter = ApiConfig.from_env()
limiter = RateLimiter(limit=_cfg_for_limiter.RL_MAX, window_seconds=int(_cfg_for_limiter.RL_WINDOW_MS / 1000))
# Strict limiter for auth endpoints (5 requests per minute)
auth_limiter = RateLimiter(limit=5, window_seconds=60)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    cfg = ApiConfig.from_env()
    if not cfg.AUTH_ENABLED:
        return None
        
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 1. Check Legacy Token
    if cfg.AUTH_TOKEN and token == cfg.AUTH_TOKEN:
        return User(id=uuid.uuid4(), email="legacy@system", tier="admin")

    # 2. Check if API Key (starts with sk_live_)
    if token.startswith("sk_live_"):
        hashed = hash_api_key(token)
        key_repo = ApiKeyRepository(db)
        key_record = await key_repo.get_by_hash(hashed)
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        # Fetch associated user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(key_record.user_id)
        if not user:
             raise HTTPException(status_code=401, detail="User not found")
        return user

    # 3. Check JWT
    try:
        payload = jwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Convert string to UUID object for SQLAlchemy
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def check_rate_limit(request: Request, user=Depends(get_current_user)):
    cfg = ApiConfig.from_env()
    if not cfg.RL_ENABLED:
        return
    
    # Identify by User ID if available, else IP
    identifier = "ip:" + request.client.host
    if user:
        identifier = f"user:{user.id}"

    try:
        allowed = await limiter.is_allowed(identifier)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except Exception as e:
        # Fallback if Redis is down? Or fail open/closed?
        # For MVP, log error and fail open (allow)
        print(f"Rate limit check failed: {e}")
        pass
    
    return identifier

async def check_auth_rate_limit(request: Request):
    """
    Stricter rate limit for authentication endpoints to prevent brute force.
    Always uses IP address as identifier since user might not be logged in.
    """
    cfg = ApiConfig.from_env()
    if not cfg.RL_ENABLED:
        return
        
    identifier = "auth:ip:" + request.client.host
    
    try:
        allowed = await auth_limiter.is_allowed(identifier)
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many authentication attempts. Please try again later.")
    except Exception as e:
        print(f"Auth rate limit check failed: {e}")
        pass
    
    return identifier
