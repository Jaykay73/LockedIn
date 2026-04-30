from dataclasses import dataclass
from urllib.parse import urlparse

from app.schemas.roadmap import ResourceType

PAID_PATTERNS = (
    "pricing",
    "checkout",
    "subscribe",
    "subscription",
    "premium",
    "paid",
    "pro plan",
    "membership",
    "cart",
    "payment",
    "buy now",
)


@dataclass(frozen=True)
class ResourceCandidate:
    title: str
    url: str
    type: ResourceType
    source: str
    snippet: str = ""
    is_free: bool = True


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return (host.endswith("youtube.com") and parsed.path == "/watch") or host.endswith("youtu.be")


def looks_paid(candidate: ResourceCandidate) -> bool:
    haystack = " ".join([candidate.title, candidate.url, candidate.snippet]).lower()
    return any(pattern in haystack for pattern in PAID_PATTERNS)


def is_probably_relevant(candidate: ResourceCandidate) -> bool:
    parsed = urlparse(candidate.url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if candidate.type == ResourceType.youtube_video:
        return is_youtube_url(candidate.url)
    return bool(parsed.netloc)


def filter_free_resources(candidates: list[ResourceCandidate]) -> list[ResourceCandidate]:
    seen: set[str] = set()
    kept: list[ResourceCandidate] = []
    for candidate in candidates:
        normalized_url = candidate.url.strip()
        if normalized_url in seen:
            continue
        if not candidate.is_free or looks_paid(candidate) or not is_probably_relevant(candidate):
            continue
        seen.add(normalized_url)
        kept.append(candidate)
    return kept
