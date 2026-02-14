"""Tests for ResearchService (Tavily)."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.research import ResearchService


@pytest.mark.asyncio
async def test_search_success():
    service = ResearchService(api_key="test-key")
    with patch("tavily.TavilyClient") as mock_tavily:
        mock_client = MagicMock()
        mock_tavily.return_value = mock_client
        mock_client.search.return_value = {
            "results": [{"title": "Test", "url": "https://test.com", "content": "Result"}]
        }
        result = await service.search("ADHS Strategien")
        assert result["success"] is True
        assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_search_no_api_key():
    service = ResearchService(api_key="")
    result = await service.search("test")
    assert result["success"] is False
    assert "error" in result
