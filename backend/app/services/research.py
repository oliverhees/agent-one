"""Research service using Tavily API for web search."""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.tavily_api_key

    async def search(self, query: str, max_results: int = 5) -> dict:
        if not self.api_key:
            return {"success": False, "error": "Tavily API key not configured"}
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.search(query=query, max_results=max_results)
            results = [
                {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:500]}
                for r in response.get("results", [])
            ]
            return {"success": True, "query": query, "results": results}
        except Exception as e:
            logger.error("Tavily search failed: %s", e)
            return {"success": False, "error": str(e)}

    async def extract(self, url: str) -> dict:
        if not self.api_key:
            return {"success": False, "error": "Tavily API key not configured"}
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.extract(urls=[url])
            return {"success": True, "url": url, "content": response}
        except Exception as e:
            logger.error("Tavily extract failed: %s", e)
            return {"success": False, "error": str(e)}
