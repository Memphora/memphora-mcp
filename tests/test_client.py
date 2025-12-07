"""Tests for Memphora client."""

import pytest
import os
from unittest.mock import AsyncMock, patch

# Set a dummy API key for tests
os.environ["MEMPHORA_API_KEY"] = "test_key_for_testing"

from memphora_mcp.client import MemphoraClient, Memory, SearchResult


class TestMemphoraClient:
    """Test suite for MemphoraClient."""
    
    def test_init_with_env_var(self):
        """Test client initialization with environment variable."""
        client = MemphoraClient()
        assert client.api_key == "test_key_for_testing"
        assert client.api_url == MemphoraClient.DEFAULT_API_URL
    
    def test_init_with_explicit_key(self):
        """Test client initialization with explicit API key."""
        client = MemphoraClient(api_key="explicit_key")
        assert client.api_key == "explicit_key"
    
    def test_init_without_key_raises(self):
        """Test that missing API key raises ValueError."""
        # Temporarily remove the env var
        old_key = os.environ.pop("MEMPHORA_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="API key required"):
                MemphoraClient(api_key=None)
        finally:
            if old_key:
                os.environ["MEMPHORA_API_KEY"] = old_key
    
    def test_headers(self):
        """Test that headers include authorization."""
        client = MemphoraClient(api_key="test_key")
        headers = client._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key"
        assert headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_search_formats_results(self):
        """Test that search properly formats results."""
        client = MemphoraClient(api_key="test_key")
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {
            "memories": [
                {"id": "mem1", "content": "User likes Python", "similarity": 0.95},
                {"id": "mem2", "content": "User works at Google", "similarity": 0.85}
            ],
            "search_path": "fast"
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await client.search("programming")
        
        assert isinstance(result, SearchResult)
        assert len(result.memories) == 2
        assert result.memories[0].content == "User likes Python"
        assert result.memories[0].similarity == 0.95
    
    @pytest.mark.asyncio
    async def test_store_memory(self):
        """Test storing a memory."""
        client = MemphoraClient(api_key="test_key")
        
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {"id": "new_mem_id", "status": "created"}
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await client.store("I love Python")
        
        assert result["status"] == "created"
        assert "id" in result


class TestMemoryModel:
    """Test Memory model."""
    
    def test_memory_creation(self):
        """Test creating a Memory object."""
        mem = Memory(
            id="test_id",
            content="Test content",
            metadata={"category": "test"},
            similarity=0.9
        )
        assert mem.id == "test_id"
        assert mem.content == "Test content"
        assert mem.similarity == 0.9
    
    def test_memory_optional_fields(self):
        """Test Memory with optional fields."""
        mem = Memory(id="test", content="content")
        assert mem.metadata is None
        assert mem.similarity is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
