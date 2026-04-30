from app.schemas.roadmap import ResourceType
from app.services.resource_filter import ResourceCandidate, filter_free_resources, is_youtube_url


def test_paid_urls_are_filtered():
    candidates = [
        ResourceCandidate("Premium Guitar Course", "https://example.com/guitar", ResourceType.free_course, "Tavily"),
        ResourceCandidate("Free Guitar Guide", "https://example.com/free-guitar", ResourceType.article, "Tavily"),
    ]
    kept = filter_free_resources(candidates)
    assert [item.title for item in kept] == ["Free Guitar Guide"]


def test_pricing_checkout_urls_are_filtered():
    candidates = [
        ResourceCandidate("Excel Guide", "https://example.com/pricing", ResourceType.article, "Tavily"),
        ResourceCandidate("Excel Guide", "https://example.com/checkout", ResourceType.article, "Tavily"),
    ]
    assert filter_free_resources(candidates) == []


def test_valid_free_looking_urls_are_kept():
    candidate = ResourceCandidate("Public Speaking Guide", "https://example.com/public-speaking", ResourceType.article, "Tavily")
    assert filter_free_resources([candidate]) == [candidate]


def test_youtube_urls_are_accepted():
    assert is_youtube_url("https://www.youtube.com/watch?v=abc123")
    assert is_youtube_url("https://youtu.be/abc123")
