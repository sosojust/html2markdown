import os
import importlib
import pytest
import anyio
from httpx import AsyncClient


@pytest.mark.anyio
async def test_rate_limit_headers_present():
    os.environ["RL_ENABLED"] = "1"
    os.environ["RL_MAX"] = "3"
    os.environ["RL_WINDOW_MS"] = "60000"
    # reload app to apply env
    app_mod = importlib.import_module("api.app")
    importlib.reload(app_mod)
    app = app_mod.app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/v1/convert", json={"html": "<p>a</p>"})
        assert r.status_code == 200
        assert r.headers.get("X-RateLimit-Limit") == "3"
        assert r.headers.get("X-RateLimit-Remaining") is not None
        assert r.headers.get("X-RateLimit-Reset") is not None


@pytest.mark.anyio
async def test_by_url_invalid_scheme():
    os.environ["RL_ENABLED"] = "0"
    app_mod = importlib.import_module("api.app")
    importlib.reload(app_mod)
    app = app_mod.app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/v1/convert/by_url", json={"url": "ftp://example.com"})
        assert r.status_code == 422
        body = r.json()
        assert body["message"] == "invalid_url"
