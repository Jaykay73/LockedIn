import copy

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.schemas.requests import GenerateRoadmapRequest
from app.schemas.roadmap import Roadmap
from app.services.id_generator import assign_backend_ids


def sample_roadmap(cached: bool = False) -> Roadmap:
    resource_a = {
        "title": "Python for Beginners",
        "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8",
        "type": "youtube_video",
        "source": "YouTube",
        "is_free": True,
    }
    resource_b = {
        "title": "Python Tutorial",
        "url": "https://www.w3schools.com/python/",
        "type": "article",
        "source": "Tavily",
        "is_free": True,
    }
    payload = {
        "skill": "Python for Beginners",
        "overview": "A practical beginner roadmap for learning Python with short projects and steady practice.",
        "estimated_total_duration": "6-8 weeks",
        "phases": [
            {
                "title": f"Phase {phase}",
                "level": "beginner",
                "goal": "Learn useful basics and apply them.",
                "estimated_duration": "2 weeks",
                "nodes": [
                    {
                        "title": f"Node {node}",
                        "description": "Practice a focused beginner topic with examples and a small exercise.",
                        "estimated_completion_time": "2-3 hours",
                        "resources": [copy.deepcopy(resource_a), copy.deepcopy(resource_b)],
                    }
                    for node in range(1, 4)
                ],
                "project": {
                    "title": f"Project {phase}",
                    "brief": "Build a small project that applies the lessons from this phase.",
                    "tools_needed": ["Browser"],
                    "resources": [copy.deepcopy(resource_a), copy.deepcopy(resource_b)],
                },
            }
            for phase in range(1, 4)
        ],
        "metadata": {"model_used": "mock", "resource_sources": ["mock"], "cached": cached},
    }
    return Roadmap.model_validate(assign_backend_ids(payload, "python", suffix="abc123"))


class FakeGenerator:
    def __init__(self, *, fail: bool = False, cached: bool = False):
        self.fail = fail
        self.cached = cached

    async def generate(self, request: GenerateRoadmapRequest):
        if self.fail:
            raise RuntimeError("model unavailable")
        return sample_roadmap(cached=self.cached)


def test_post_generate_returns_success_with_mocked_generator(monkeypatch):
    monkeypatch.setattr(routes, "generator", FakeGenerator())
    client = TestClient(app)
    response = client.post("/api/v1/roadmaps/generate", json={"skill": "Learn Python"})
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert len(body["data"]["phases"]) == 3


def test_invalid_model_response_triggers_repair_path():
    from app.core.config import Settings
    from app.services.roadmap_generator import RoadmapGenerator
    from app.services.resource_filter import ResourceCandidate
    from app.schemas.roadmap import ResourceType

    class Search:
        async def search(self, skill):
            return [
                ResourceCandidate("Video", "https://www.youtube.com/watch?v=kqtD5dpn9C8", ResourceType.youtube_video, "YouTube"),
                ResourceCandidate("Article", "https://www.w3schools.com/python/", ResourceType.article, "Tavily"),
            ]

    class DeepSeek:
        def __init__(self):
            self.calls = 0

        async def generate_json(self, prompt, model):
            self.calls += 1
            if self.calls == 1:
                return "{bad json"
            return sample_roadmap().model_dump_json()

    class Cache:
        async def get(self, *args):
            return None

        async def set(self, *args):
            return None

    deepseek = DeepSeek()
    generator = RoadmapGenerator(
        settings=Settings(enable_link_validation=False, enable_cache=False, deepseek_api_key="x"),
        search_service=Search(),
        deepseek_client=deepseek,
        cache=Cache(),
    )
    import anyio

    roadmap = anyio.run(generator.generate, GenerateRoadmapRequest(skill="Learn Python"))
    assert roadmap.metadata.model_used == "deepseek-v4-flash"
    assert deepseek.calls == 2


def test_failed_generation_returns_clean_error(monkeypatch):
    monkeypatch.setattr(routes, "generator", FakeGenerator(fail=True))
    client = TestClient(app)
    response = client.post("/api/v1/roadmaps/generate", json={"skill": "Unknown"})
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is False
    assert body["error"]["code"] == "ROADMAP_GENERATION_FAILED"


def test_cached_request_returns_cached_metadata(monkeypatch):
    monkeypatch.setattr(routes, "generator", FakeGenerator(cached=True))
    client = TestClient(app)
    response = client.post("/api/v1/roadmaps/generate", json={"skill": "Learn Python"})
    body = response.json()
    assert body["success"] is True
    assert body["data"]["metadata"]["cached"] is True
