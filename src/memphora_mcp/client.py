"""
Memphora API Client for MCP Server.

Handles all communication with the Memphora backend API.
"""

import os
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Memory(BaseModel):
    """A memory returned from Memphora."""
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None
    created_at: Optional[str] = None


class SearchResult(BaseModel):
    """Search results from Memphora."""
    memories: List[Memory]
    query: str
    search_path: Optional[str] = None
    latency_ms: Optional[float] = None


class MemphoraClient:
    """
    Client for interacting with Memphora API.
    
    Usage:
        client = MemphoraClient(api_key="your_key")
        results = await client.search("What do I like?")
    """
    
    DEFAULT_API_URL = "https://memphora-backend-h7h5s5lkza-uc.a.run.app/api/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Memphora client.
        
        Args:
            api_key: Memphora API key (or set MEMPHORA_API_KEY env var)
            api_url: API base URL (or set MEMPHORA_API_URL env var)
            user_id: Default user ID for operations (or set MEMPHORA_USER_ID env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MEMPHORA_API_KEY")
        self.api_url = api_url or os.getenv("MEMPHORA_API_URL", self.DEFAULT_API_URL)
        self.user_id = user_id or os.getenv("MEMPHORA_USER_ID", "mcp_default_user")
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(
                "Memphora API key required. Set MEMPHORA_API_KEY environment variable "
                "or pass api_key parameter."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "memphora-mcp/0.1.0"
        }
    
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> SearchResult:
        """
        Search memories for relevant information.
        
        Args:
            query: Search query
            user_id: User ID (uses default if not provided)
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            SearchResult with matching memories
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/memories/search",
                headers=self._get_headers(),
                json={
                    "user_id": user_id,
                    "query": query,
                    "limit": limit,
                    "min_similarity": min_similarity
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # API returns list directly, not wrapped in {"memories": [...]}
            memories_data = data if isinstance(data, list) else data.get("memories", [])
            
            memories = [
                Memory(
                    id=m.get("id", ""),
                    content=m.get("content", ""),
                    metadata=m.get("metadata"),
                    similarity=m.get("similarity"),
                    created_at=m.get("created_at")
                )
                for m in memories_data
            ]
            
            return SearchResult(
                memories=memories,
                query=query,
                search_path=data.get("search_path") if isinstance(data, dict) else None,
                latency_ms=data.get("latency_ms") if isinstance(data, dict) else None
            )
    
    async def store(
        self,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a new memory.
        
        Args:
            content: Memory content to store
            user_id: User ID (uses default if not provided)
            metadata: Optional metadata dict
            
        Returns:
            Response with memory ID and status
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/memories",
                headers=self._get_headers(),
                json={
                    "user_id": user_id,
                    "content": content,
                    "metadata": metadata or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def extract_conversation(
        self,
        conversation: List[Dict[str, str]],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract memories from a conversation.
        
        Args:
            conversation: List of messages with 'role' and 'content'
            user_id: User ID (uses default if not provided)
            
        Returns:
            Response with extracted memories count
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/conversations/extract",
                headers=self._get_headers(),
                json={
                    "user_id": user_id,
                    "conversation": conversation
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_memories(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get all memories for a user.
        
        Args:
            user_id: User ID (uses default if not provided)
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/memories",
                headers=self._get_headers(),
                params={"user_id": user_id, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                Memory(
                    id=m.get("id", ""),
                    content=m.get("content", ""),
                    metadata=m.get("metadata"),
                    created_at=m.get("created_at")
                )
                for m in data.get("memories", [])
            ]
    
    async def delete_memory(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete
            user_id: User ID (uses default if not provided)
            
        Returns:
            Response confirming deletion
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.api_url}/memories/{memory_id}",
                headers=self._get_headers(),
                params={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_summary(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of user's memories.
        
        Args:
            user_id: User ID (uses default if not provided)
            
        Returns:
            Summary including memory count and categories
        """
        user_id = user_id or self.user_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/users/{user_id}/summary",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """
        Check if Memphora API is healthy.
        
        Returns:
            True if API is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.api_url}/health/live",
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception:
            return False
