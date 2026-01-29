import asyncio
import os
import sys
from datetime import timedelta
import time
import httpx

# Add project root to sys.path
sys.path.append(os.getcwd())

# Mock environment for short expiry
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "0" # Immediate expiry? 
# If 0, it expires immediately.
# But let's set it to a very small value to ensure we can capture the token first.
# Actually, if I set it to 0.01 (0.6 seconds), it might expire by the time I use it.
# Let's use 1 minute, but I don't want to wait 1 minute in test.
# I can mock the time? Or just use a token that I MANUALLY create with past expiry?
# But I want to test the full flow including `login` endpoint.

# Better: Login, get token. 
# Then manually WAIT for it to expire? No.
# I can create a token manually with short expiry using internal function?
# But I want to test the ENDPOINTS.

# So, let's set expiry to 1 second.
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "0.05" # 3 seconds

from backend.api.app import app
from httpx import AsyncClient, ASGITransport

async def test_plugin_flow():
    print("Starting Plugin Flow Test...")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register/Login
        email = f"plugin_test_{int(time.time())}@example.com"
        password = "password123"
        
        print(f"Registering {email}...")
        await ac.post("/v1/auth/register", json={"email": email, "password": password})
        
        print("Logging in...")
        login_data = {"username": email, "password": password}
        response = await ac.post("/v1/auth/token", data=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print("Login successful. Got tokens.")
        
        # 2. Verify Access Token works initially
        print("Verifying initial access token...")
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        convert_payload = {"html": "<h1>Hello</h1>"}
        response = await ac.post("/v1/convert", json=convert_payload, headers=headers)
        if response.status_code != 200:
             print(f"Initial convert failed: {response.status_code} {response.text}")
             # It might have expired already if 3 seconds passed? Unlikely.
        else:
             print("Initial convert successful.")

        # 3. Wait for expiry
        print("Waiting 4 seconds for token expiry...")
        await asyncio.sleep(4)
        
        # 4. Try Convert (Expect 401)
        print("Attempting convert with expired token...")
        response = await ac.post("/v1/convert", json=convert_payload, headers=headers)
        print(f"Convert status: {response.status_code}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        # 5. Try Refresh (Simulate background.js)
        print("Attempting refresh...")
        refresh_payload = {"refresh_token": refresh_token}
        response = await ac.post("/v1/auth/refresh", json=refresh_payload)
        
        if response.status_code != 200:
            print(f"Refresh FAILED: {response.status_code} {response.text}")
            exit(1)
            
        new_tokens = response.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens.get("refresh_token")
        print("Refresh successful. Got new access token.")
        
        # 6. Retry Convert with NEW token
        print("Retrying convert with new token...")
        headers["Authorization"] = f"Bearer {new_access_token}"
        response = await ac.post("/v1/convert", json=convert_payload, headers=headers)
        
        if response.status_code == 200:
            print("Retry convert SUCCESSFUL!")
        else:
            print(f"Retry convert FAILED: {response.status_code} {response.text}")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_plugin_flow())
