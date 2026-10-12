from fastapi.testclient import TestClient

from app.api import routes
from app.core.config import Settings
from app.main import app
from app.schemas.roadmap import ResourceType
from app.services.cache import RoadmapCache
from app.services.resource_filter import ResourceCandidate
from app.services.roadmap_generator import RoadmapGenerator
from tests.test_api_generate_mocked import sample_roadmap


class SearchStub:
    async def search(self, skill: str) -> list[ResourceCandidate]:
        return [
            ResourceCandidate(
                "Python for Beginners",
                "https://www.youtube.com/watch?v=kqtD5dpn9C8",
                ResourceType.youtube_video,
                "YouTube",
            ),
            ResourceCandidate(
                "Python Tutorial",
                "https://www.w3schools.com/python/",
                ResourceType.article,
                "Tavily",
            ),
        ]


class SkillAwareModelStub:
    def __init__(self) -> None:
        self.calls = 0

    async def generate_json(self, prompt: str, model: str) -> str:
        self.calls += 1
        roadmap = sample_roadmap().model_copy(deep=True)
        roadmap.skill = "C++" if "- skill: Learn C++" in prompt else "C"
        return roadmap.model_dump_json()


def test_distinct_skills_with_the_same_slug_do_not_share_a_cached_roadmap(
    tmp_path, monkeypatch
):
    model = SkillAwareModelStub()
    settings = Settings(
        deepseek_api_key="unused",
        enable_link_validation=False,
        sqlite_db_path=str(tmp_path / "roadmaps.db"),
    )
    monkeypatch.setattr(
        routes,
        "generator",
        RoadmapGenerator(
            settings=settings,
            search_service=SearchStub(),
            deepseek_client=model,
            cache=RoadmapCache(settings),
        ),
    )
    client = TestClient(app)

    cpp_response = client.post("/api/v1/roadmaps/generate", json={"skill": "Learn C++"})
    c_response = client.post("/api/v1/roadmaps/generate", json={"skill": "Learn C"})

    assert cpp_response.status_code == 200
    assert c_response.status_code == 200
    assert cpp_response.json()["data"]["skill"] == "C++"
    assert c_response.json()["data"]["skill"] == "C"
    assert model.calls == 2
