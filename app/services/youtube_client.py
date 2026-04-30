import httpx

from app.core.config import Settings
from app.schemas.roadmap import ResourceType
from app.services.resource_filter import ResourceCandidate


class YouTubeClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def search(self, query: str, max_results: int = 5) -> list[ResourceCandidate]:
        if not self.settings.youtube_api_key:
            return []

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "videoEmbeddable": "true",
            "safeSearch": "moderate",
            "key": self.settings.youtube_api_key,
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://www.googleapis.com/youtube/v3/search", params=params)
            response.raise_for_status()
            data = response.json()

        candidates: list[ResourceCandidate] = []
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            candidates.append(
                ResourceCandidate(
                    title=snippet.get("title") or "YouTube tutorial",
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    type=ResourceType.youtube_video,
                    source="YouTube",
                    snippet=snippet.get("description") or "",
                )
            )
        return candidates
