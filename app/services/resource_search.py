import asyncio

from app.core.config import Settings
from app.services.link_validator import LinkValidator
from app.services.resource_filter import ResourceCandidate, filter_free_resources
from app.services.tavily_client import TavilyClient
from app.services.youtube_client import YouTubeClient


class ResourceSearchService:
    def __init__(
        self,
        settings: Settings,
        tavily_client: TavilyClient | None = None,
        youtube_client: YouTubeClient | None = None,
        link_validator: LinkValidator | None = None,
    ):
        self.settings = settings
        self.tavily_client = tavily_client or TavilyClient(settings)
        self.youtube_client = youtube_client or YouTubeClient(settings)
        self.link_validator = link_validator or LinkValidator(settings)

    def build_queries(self, skill: str) -> list[str]:
        clean_skill = " ".join(skill.replace("-", " ").split())
        return [
            f"{clean_skill} for complete beginners tutorial",
            f"{clean_skill} beginner guide fundamentals",
            f"{clean_skill} beginner practice exercises",
            f"free {clean_skill} course beginner",
            f"{clean_skill} beginner project ideas",
            f"{clean_skill} learning roadmap beginner",
        ]

    async def search(self, skill: str) -> list[ResourceCandidate]:
        queries = self.build_queries(skill)
        tasks = []
        for query in queries:
            tasks.append(self.tavily_client.search(query, max_results=4))
            tasks.append(self.youtube_client.search(query, max_results=3))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates: list[ResourceCandidate] = []
        for result in results:
            if isinstance(result, list):
                candidates.extend(result)

        filtered = filter_free_resources(candidates)
        return await self.link_validator.validate_many(filtered)
