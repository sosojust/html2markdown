from typing import List, Dict, Any, Optional
import os
import httpx

class NotionClient:
    """
    Client for interacting with Notion API.
    Handles authentication and block appending.
    """
    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    async def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Append blocks to a page or block.
        API: PATCH https://api.notion.com/v1/blocks/{block_id}/children
        """
        url = f"{self.BASE_URL}/blocks/{page_id}/children"
        
        # Notion API limit: 100 blocks per request
        # We need to chunk if > 100
        results = []
        
        for i in range(0, len(blocks), 100):
            chunk = blocks[i:i+100]
            payload = {"children": chunk}
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=payload)
                if response.status_code != 200:
                    raise Exception(f"Notion API Error: {response.status_code} - {response.text}")
                results.append(response.json())
                
        return results[-1] if results else {}

    async def validate_page(self, page_id: str) -> bool:
        """
        Check if page exists and is accessible.
        API: GET https://api.notion.com/v1/blocks/{block_id}
        """
        url = f"{self.BASE_URL}/blocks/{page_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            return response.status_code == 200
