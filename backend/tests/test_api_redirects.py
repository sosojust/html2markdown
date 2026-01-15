import os
import importlib
import pytest
from httpx import AsyncClient


class _StubResponse:
    def __init__(self, text="ok", ct="text/html", redirects=10):
        self.text = text
        self.headers = {"content-type": ct}
        self.history = [object()] * redirects


class _StubClient:
    def __init__(self, headers=None):
        self.headers = headers or {}
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def get(self, url, follow_redirects=True):
        return _StubResponse()


@pytest.mark.anyio
async def test_too_many_redirects_returns_400(monkeypatch):
    os.environ["MAX_REDIRECTS"] = "5"
    app_mod = importlib.import_module("api.app")
    importlib.reload(app_mod)
    app = app_mod.app
    def _stub_async_client(**kwargs):
        return _StubClient(headers=kwargs.get("headers"))
    monkeypatch.setattr(app_mod.httpx, "AsyncClient", _stub_async_client)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/v1/convert/by_url", json={"url": "https://example.com"})
        assert r.status_code == 400
        body = r.json()
        assert body["message"] == "too_many_redirects"
