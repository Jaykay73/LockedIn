import asyncio

import httpx

from app.core.config import Settings
from app.services.resource_filter import ResourceCandidate, is_youtube_url


class LinkValidator:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def validate_many(self, candidates: list[ResourceCandidate]) -> list[ResourceCandidate]:
        if not self.settings.enable_link_validation:
            return candidates
        results = await asyncio.gather(*(self.is_valid(candidate.url) for candidate in candidates), return_exceptions=True)
        return [candidate for candidate, valid in zip(candidates, results) if valid is True]

    async def is_valid(self, url: str) -> bool:
        if is_youtube_url(url):
            return True
        timeout = self.settings.link_validation_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                response = await client.head(url)
                if 200 <= response.status_code <= 399:
                    return True
                if response.status_code != 405:
                    return False
            except httpx.HTTPError:
                pass
            try:
                response = await client.get(url)
                return 200 <= response.status_code <= 399
            except httpx.HTTPError:
                return False
