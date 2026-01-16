from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from ..db import get_db
from ..models.entity import User, ApiKey
from ..repositories.base import UserRepository, ApiKeyRepository
from ..schemas import UserCreate, UserRead, ApiKeyCreate, ApiKeyShow, Token
from ..auth import get_password_hash, verify_password, generate_api_key, hash_api_key, create_access_token
from ..config import ApiConfig
from ..dependencies import get_current_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
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
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
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
    key_id: str,
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
