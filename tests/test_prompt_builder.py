from app.prompts.roadmap_prompt import build_roadmap_prompt
from app.schemas.requests import GenerateRoadmapRequest
from app.schemas.roadmap import ResourceType
from app.services.resource_filter import ResourceCandidate


def test_prompt_contains_required_instructions_and_data():
    request = GenerateRoadmapRequest(skill="Learn Guitar")
    resources = [
        ResourceCandidate(
            title="Beginner Guitar Lesson",
            url="https://www.youtube.com/watch?v=abc123",
            type=ResourceType.youtube_video,
            source="YouTube",
        )
    ]
    prompt = build_roadmap_prompt(request, resources)
    assert "Learn Guitar" in prompt
    assert "Beginner Guitar Lesson" in prompt
    assert "Return JSON only" in prompt
    assert "Do not invent URLs" in prompt
    assert "Support non-tech skills" in prompt
