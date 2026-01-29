
import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.api.app import app
from backend.api.db import get_db

# Setup test DB
TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"

# Override environment variables for ApiConfig
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["AUTH_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"

# Setup DB Engine for override
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
    # Remove existing db
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")
    
    # Init schema using sqlite3 (synchronous)
    import sqlite3
    conn = sqlite3.connect("./test_auth.db")
    with open("backend/schema/latest_sqlite.sql", "r") as f:
        sql = f.read()
        conn.executescript(sql)
    conn.close()
    
    yield
    
    # Cleanup
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")

@pytest.mark.asyncio
async def test_register_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register
        payload = {"email": "test@example.com", "password": "password123"}
        response = await ac.post("/v1/auth/register", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        
        # 2. Login
        login_data = {"username": "test@example.com", "password": "password123"}
        response = await ac.post("/v1/auth/token", data=login_data)
        assert response.status_code == 200, response.text
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        
        # 3. Get Me
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await ac.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_api_keys():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login first
        login_data = {"username": "test@example.com", "password": "password123"}
        response = await ac.post("/v1/auth/token", data=login_data)
        access_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Create Key
        key_payload = {"name": "Test Key"}
        response = await ac.post("/v1/auth/keys", json=key_payload, headers=headers)
        assert response.status_code == 200
        key_data = response.json()
        assert "key" in key_data
        assert key_data["name"] == "Test Key"
        key_id = key_data["id"]
        
        # List Keys
        response = await ac.get("/v1/auth/keys", headers=headers)
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) >= 1
        assert keys[0]["key"] == "****************" # Hidden
        
        # Delete Key
        response = await ac.delete(f"/v1/auth/keys/{key_id}", headers=headers)
        assert response.status_code == 200
        
        # List again
        response = await ac.get("/v1/auth/keys", headers=headers)
        assert len(response.json()) == 0

@pytest.mark.asyncio
async def test_login_failure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_data = {"username": "test@example.com", "password": "wrongpassword"}
        response = await ac.post("/v1/auth/token", data=login_data)
        assert response.status_code == 401

