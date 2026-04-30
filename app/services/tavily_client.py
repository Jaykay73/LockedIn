import httpx

from app.core.config import Settings
from app.schemas.roadmap import ResourceType
from app.services.resource_filter import ResourceCandidate


class TavilyClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def search(self, query: str, max_results: int = 5) -> list[ResourceCandidate]:
        if not self.settings.tavily_api_key:
            return []

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        candidates: list[ResourceCandidate] = []
        for item in data.get("results", []):
            title = item.get("title") or "Untitled resource"
            url = item.get("url") or ""
            snippet = item.get("content") or ""
            candidates.append(
                ResourceCandidate(
                    title=title,
                    url=url,
                    type=_infer_resource_type(title, url, snippet),
                    source="Tavily",
                    snippet=snippet,
                )
            )
        return candidates


def _infer_resource_type(title: str, url: str, snippet: str) -> ResourceType:
    haystack = f"{title} {url} {snippet}".lower()
    if "docs" in haystack or "documentation" in haystack:
        return ResourceType.documentation
    if "book" in haystack or "ebook" in haystack:
        return ResourceType.free_book
    if "course" in haystack or "freecodecamp" in haystack or "coursera" in haystack:
        return ResourceType.free_course
    if "exercise" in haystack or "practice" in haystack or "interactive" in haystack:
        return ResourceType.interactive_practice
    return ResourceType.article
