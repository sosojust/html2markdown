import pytest
from fastapi.testclient import TestClient
from backend.api.app import app
import os

# Disable Auth for these tests to simplify
os.environ["AUTH_ENABLED"] = "false"

client = TestClient(app)

def test_convert_obsidian_target():
    html = "<blockquote><p><strong>Note</strong>: This is a note.</p></blockquote>"
    response = client.post(
        "/v1/convert",
        json={
            "html": html,
            "options": {
                "target": "obsidian"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Expect Obsidian Callout format
    assert "> [!NOTE]" in data["markdown"]
    assert "This is a note." in data["markdown"]

def test_convert_notion_target():
    html = "<h1>Hello</h1>"
    response = client.post(
        "/v1/convert",
        json={
            "html": html,
            "options": {
                "target": "notion"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Expect Notion Blocks (list of dicts)
    blocks = data["markdown"]
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert blocks[0]["type"] == "heading_1"
