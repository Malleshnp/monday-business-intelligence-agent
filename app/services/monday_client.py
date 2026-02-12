"""Monday.com GraphQL API client."""
import httpx
import json
from typing import Dict, List, Any, Optional
from app.core.config import settings


class MondayClient:
    """Client for interacting with Monday.com GraphQL API."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.MONDAY_API_TOKEN
        self.api_url = settings.MONDAY_API_URL
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }
    
    async def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against Monday.com API."""
        if not self.api_token:
            raise ValueError("Monday.com API token is required")
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    error_msg = data["errors"][0].get("message", "Unknown error")
                    raise Exception(f"Monday.com API error: {error_msg}")
                
                return data.get("data", {})
            except httpx.HTTPError as e:
                raise Exception(f"HTTP error: {str(e)}")
    
    async def get_boards(self) -> List[Dict[str, Any]]:
        """Get all boards accessible to the user."""
        query = """
        query {
            boards {
                id
                name
                description
                state
                board_folder_id
                board_kind
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        result = await self.execute_query(query)
        return result.get("boards", [])
    
    async def get_board_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a board by its name."""
        boards = await self.get_boards()
        for board in boards:
            if board.get("name", "").lower() == name.lower():
                return board
        return None
    
    async def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get all items from a board with their column values."""
        query = """
        query GetBoardItems($boardId: ID!, $limit: Int!) {
            boards(ids: [$boardId]) {
                id
                name
                items_page(limit: $limit) {
                    items {
                        id
                        name
                        created_at
                        updated_at
                        state
                        column_values {
                            id
                            column {
                                id
                                title
                                type
                            }
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": board_id, "limit": limit}
        result = await self.execute_query(query, variables)
        
        boards = result.get("boards", [])
        if not boards:
            return []
        
        items = boards[0].get("items_page", {}).get("items", [])
        return items
    
    async def get_item_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific item."""
        query = """
        query GetItemDetails($itemId: ID!) {
            items(ids: [$itemId]) {
                id
                name
                created_at
                updated_at
                state
                board {
                    id
                    name
                }
                column_values {
                    id
                    column {
                        id
                        title
                        type
                    }
                    text
                    value
                }
            }
        }
        """
        variables = {"itemId": item_id}
        result = await self.execute_query(query, variables)
        items = result.get("items", [])
        return items[0] if items else None


# Singleton instance
monday_client = MondayClient()