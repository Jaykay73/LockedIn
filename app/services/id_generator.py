import hashlib
import re
import secrets
from copy import deepcopy
from typing import Any


def normalize_skill(skill: str) -> str:
    value = " ".join(skill.strip().lower().split())
    value = re.sub(r"^learn\s+", "", value)
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "skill"


def request_hash(payload: dict[str, Any]) -> str:
    encoded = repr(sorted((key, str(value)) for key, value in payload.items())).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def assign_backend_ids(roadmap: dict[str, Any], normalized_skill: str, suffix: str | None = None) -> dict[str, Any]:
    data = deepcopy(roadmap)
    suffix = suffix or secrets.token_hex(3)
    data["roadmap_id"] = f"roadmap_{normalized_skill.replace('-', '_')}_{suffix}"
    data["normalized_skill"] = normalized_skill

    projects: list[dict[str, Any]] = []
    for phase_index, phase in enumerate(data.get("phases", []), start=1):
        phase_id = f"phase_{phase_index}"
        phase["id"] = phase_id
        for node_index, node in enumerate(phase.get("nodes", []), start=1):
            node_id = f"{phase_id}_node_{node_index}"
            node["id"] = node_id
            for resource_index, resource in enumerate(node.get("resources", []), start=1):
                resource["id"] = f"{node_id}_resource_{resource_index}"

        project = phase.get("project", {})
        project["id"] = f"{phase_id}_project_1"
        project["phase_id"] = phase_id
        for resource_index, resource in enumerate(project.get("resources", []), start=1):
            resource["id"] = f"{project['id']}_resource_{resource_index}"
        phase["project"] = project
        projects.append(deepcopy(project))

    data["projects"] = projects
    return data
