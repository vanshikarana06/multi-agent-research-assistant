# Tavily search service wrapper

from tavily import TavilyClient

from app.core.config import settings


class SearchClient:
    def __init__(self) -> None:
        self._client = TavilyClient(api_key=settings.tavily_api_key)

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        response = self._client.search(query=query, max_results=max_results, timeout=20)
        return response["results"]
