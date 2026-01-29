from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from uuid import UUID
from ..db import get_db
from ..models.entity import User, ApiKey
from ..repositories.base import UserRepository, ApiKeyRepository
from ..schemas import UserCreate, UserRead, UserUpdate, ApiKeyCreate, ApiKeyShow, Token
from ..auth import get_password_hash, verify_password, generate_api_key, hash_api_key, create_access_token, create_refresh_token
from ..config import ApiConfig
from ..dependencies import get_current_user, check_auth_rate_limit
from jose import jwt, JWTError

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if preferences is being updated
    if user_update.preferences is not None:
        current_user.preferences = user_update.preferences
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db),
    limit_key = Depends(check_auth_rate_limit)
):
    repo = UserRepository(db)
    # OAuth2PasswordRequestForm uses 'username' for the email field
    user = await repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    cfg = ApiConfig.from_env()
    access_token_expires = timedelta(minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=cfg.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(request_data: dict, db: AsyncSession = Depends(get_db)):
    refresh_token = request_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token missing")
    
    cfg = ApiConfig.from_env()
    try:
        payload = jwt.decode(refresh_token, cfg.SECRET_KEY, algorithms=[cfg.ALGORITHM])
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type")
        
        if user_id_str is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token_expires = timedelta(minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, expires_delta=access_token_expires
    )
    
    # Optionally rotate refresh token here
    # For now, just return a new access token and the same refresh token (or new one)
    # Let's issue a new refresh token too to keep it alive? Or keep same?
    # Usually we rotate.
    new_refresh_token_expires = timedelta(days=cfg.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}, expires_delta=new_refresh_token_expires
    )
    
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead)
async def register(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
    limit_key = Depends(check_auth_rate_limit)
):
    repo = UserRepository(db)
    
    # Check existing
    existing = await repo.get_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        tier="free"
    )
    return await repo.create(new_user)

@router.post("/keys", response_model=ApiKeyShow)
async def create_api_key(
    key_info: ApiKeyCreate, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    key_repo = ApiKeyRepository(db)
    
    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)
    
    new_key = ApiKey(
        user_id=user.id,
        key_hash=hashed_key,
        prefix=raw_key[:12] + "...",
        name=key_info.name
    )
    created_key = await key_repo.create(new_key)
    
    # Return schema with raw key
    return ApiKeyShow(
        id=created_key.id,
        prefix=created_key.prefix,
        name=created_key.name,
        created_at=created_key.created_at,
        last_used_at=created_key.last_used_at,
        is_active=created_key.is_active,
        key=raw_key # Show only once
    )

@router.get("/keys", response_model=list[ApiKeyShow])
async def get_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    key_repo = ApiKeyRepository(db)
    keys = await key_repo.get_by_user_id(user.id)
    # Hide raw key in list
    return [
        ApiKeyShow(
            id=k.id,
            prefix=k.prefix,
            name=k.name,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_active=k.is_active,
            key="****************" # Hide
        ) for k in keys
    ]

@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    key_repo = ApiKeyRepository(db)
    # Ensure ownership
    key = await key_repo.get_by_id(key_id)
    if not key or str(key.user_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Key not found")
        
    await key_repo.delete(key_id)
    return {"status": "ok"}
