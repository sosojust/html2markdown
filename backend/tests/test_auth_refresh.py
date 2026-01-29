
import pytest
import os
from httpx import AsyncClient, ASGITransport
from backend.api.app import app
from backend.api.db import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

# Setup test DB
TEST_DB_URL = "sqlite+aiosqlite:///./test_refresh.db"

# Override environment variables
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["AUTH_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "test_secret_key_refresh"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1" # Short expiry

# Setup DB Engine
engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    if os.path.exists("./test_refresh.db"):
        os.remove("./test_refresh.db")
    
    import sqlite3
    conn = sqlite3.connect("./test_refresh.db")
    with open("backend/schema/latest_sqlite.sql", "r") as f:
        sql = f.read()
        conn.executescript(sql)
    conn.close()
    
    yield
    
    if os.path.exists("./test_refresh.db"):
        os.remove("./test_refresh.db")

@pytest.mark.asyncio
async def test_refresh_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register
        payload = {"email": "refresh@example.com", "password": "password123"}
        await ac.post("/v1/auth/register", json=payload)
        
        # 2. Login
        login_data = {"username": "refresh@example.com", "password": "password123"}
        response = await ac.post("/v1/auth/token", data=login_data)
        assert response.status_code == 200
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 3. Refresh
        refresh_payload = {"refresh_token": refresh_token}
        response = await ac.post("/v1/auth/refresh", json=refresh_payload)
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != access_token
        
        # 4. Use new token
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        response = await ac.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == "refresh@example.com"
