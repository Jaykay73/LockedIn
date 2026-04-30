import copy

import pytest
from pydantic import ValidationError

from app.schemas.roadmap import Roadmap
from app.services.id_generator import assign_backend_ids


def valid_payload():
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
    phases = []
    for phase_index in range(1, 4):
        nodes = []
        for node_index in range(1, 4):
            nodes.append(
                {
                    "title": f"Node {node_index}",
                    "description": "Learn the core idea with simple examples and short practice tasks.",
                    "estimated_completion_time": "2-3 hours",
                    "resources": [resource_a, resource_b],
                }
            )
        phases.append(
            {
                "title": f"Phase {phase_index}",
                "level": "beginner",
                "goal": "Build practical beginner confidence.",
                "estimated_duration": "2 weeks",
                "nodes": nodes,
                "project": {
                    "title": f"Project {phase_index}",
                    "brief": "Build a small practical project that demonstrates the phase skills.",
                    "tools_needed": ["Browser"],
                    "resources": [resource_a, resource_b],
                },
            }
        )
    payload = {
        "skill": "Python for Beginners",
        "overview": "A beginner roadmap with practical examples and projects for learning step by step.",
        "estimated_total_duration": "6-8 weeks",
        "phases": phases,
        "metadata": {"model_used": "test", "resource_sources": ["test"], "cached": False},
    }
    return assign_backend_ids(payload, "python")


def test_valid_roadmap_passes():
    roadmap = Roadmap.model_validate(valid_payload())
    assert len(roadmap.phases) == 3
    assert len(roadmap.phases[0].nodes) == 3


def test_fewer_than_three_phases_fails():
    payload = valid_payload()
    payload["phases"] = payload["phases"][:2]
    payload["projects"] = payload["projects"][:2]
    with pytest.raises(ValidationError):
        Roadmap.model_validate(payload)


def test_node_with_fewer_than_two_resources_fails():
    payload = valid_payload()
    payload["phases"][0]["nodes"][0]["resources"] = payload["phases"][0]["nodes"][0]["resources"][:1]
    with pytest.raises(ValidationError):
        Roadmap.model_validate(payload)


def test_paid_resource_with_is_free_false_fails():
    payload = valid_payload()
    payload["phases"][0]["nodes"][0]["resources"][0]["is_free"] = False
    with pytest.raises(ValidationError):
        Roadmap.model_validate(payload)


def test_invalid_resource_type_fails():
    payload = copy.deepcopy(valid_payload())
    payload["phases"][0]["nodes"][0]["resources"][0]["type"] = "paid_course"
    with pytest.raises(ValidationError):
        Roadmap.model_validate(payload)
