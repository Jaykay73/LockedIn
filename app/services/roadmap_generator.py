import json
from datetime import datetime, timezone
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import ROADMAP_GENERATION_FAILED, SCHEMA_VALIDATION_FAILED, ServiceError
from app.core.logging import log_failed_generation
from app.prompts.repair_prompt import build_repair_prompt
from app.prompts.roadmap_prompt import build_roadmap_prompt
from app.schemas.requests import GenerateRoadmapRequest
from app.schemas.roadmap import Roadmap, Resource, ResourceType, roadmap_to_jsonable
from app.services.cache import RoadmapCache
from app.services.deepseek_client import DeepSeekClient
from app.services.id_generator import assign_backend_ids, normalize_skill, request_hash
from app.services.resource_filter import ResourceCandidate
from app.services.resource_search import ResourceSearchService


class RoadmapGenerator:
    def __init__(
        self,
        settings: Settings | None = None,
        search_service: ResourceSearchService | None = None,
        deepseek_client: DeepSeekClient | None = None,
        cache: RoadmapCache | None = None,
    ):
        self.settings = settings or get_settings()
        self.search_service = search_service or ResourceSearchService(self.settings)
        self.deepseek_client = deepseek_client or DeepSeekClient(self.settings)
        self.cache = cache or RoadmapCache(self.settings)

    async def generate(self, request: GenerateRoadmapRequest) -> Roadmap:
        normalized = normalize_skill(request.skill)
        req_hash = request_hash(
            {
                "normalized_skill": normalized,
                "user_level": request.user_level,
                "goal": request.goal,
                "time_commitment": request.time_commitment,
                "preferred_resource_types": [item.value for item in request.preferred_resource_types],
                "language": request.language,
            }
        )

        cached = await self.cache.get(normalized, req_hash)
        if cached:
            return Roadmap.model_validate(cached)

        resources: list[ResourceCandidate] = []
        try:
            resources = await self.search_service.search(normalized.replace("-", " "))
            if len(resources) < self.settings.min_resources_per_node:
                resources = _built_in_seed_resources(normalized)

            prompt = build_roadmap_prompt(request, resources)
            raw = await self.deepseek_client.generate_json(prompt, self.settings.deepseek_default_model)
            roadmap = self._parse_validate(raw, normalized, self.settings.deepseek_default_model, resources)
        except Exception as first_error:
            roadmap = await self._repair_or_fallback(request, normalized, resources, first_error)

        jsonable = roadmap_to_jsonable(roadmap)
        await self.cache.set(normalized, req_hash, jsonable, roadmap.metadata.model_used)
        return roadmap

    async def _repair_or_fallback(
        self,
        request: GenerateRoadmapRequest,
        normalized: str,
        resources: list[ResourceCandidate],
        first_error: Exception,
    ) -> Roadmap:
        raw = getattr(first_error, "raw_content", "")
        validation_summary = str(first_error)
        if raw:
            try:
                repair_prompt = build_repair_prompt(raw, validation_summary, resources)
                repaired = await self.deepseek_client.generate_json(repair_prompt, self.settings.deepseek_default_model)
                return self._parse_validate(repaired, normalized, self.settings.deepseek_default_model, resources)
            except Exception as repair_error:
                validation_summary = f"{validation_summary}; repair failed: {repair_error}"

        try:
            prompt = build_roadmap_prompt(request, resources or _built_in_seed_resources(normalized))
            fallback_raw = await self.deepseek_client.generate_json(prompt, self.settings.deepseek_fallback_model)
            return self._parse_validate(
                fallback_raw,
                normalized,
                self.settings.deepseek_fallback_model,
                resources or _built_in_seed_resources(normalized),
            )
        except Exception as fallback_error:
            validation_summary = f"{validation_summary}; fallback model failed: {fallback_error}"

        if self.settings.enable_demo_fallback:
            fallback = self._load_demo_fallback(normalized)
            if fallback:
                return fallback

        log_failed_generation(
            self.settings,
            normalized_skill=normalized,
            stage="roadmap_generation",
            model_used=self.settings.deepseek_fallback_model,
            validation_error_summary=validation_summary,
            raw_model_response=raw or None,
        )
        raise ServiceError(
            code=ROADMAP_GENERATION_FAILED,
            message="We could not generate this roadmap right now. Please try again.",
            stage="roadmap_generation",
            debug={"reason": validation_summary, "stage": "roadmap_generation"},
        )

    def _parse_validate(
        self,
        raw_content: str,
        normalized: str,
        model_used: str,
        resources: list[ResourceCandidate],
    ) -> Roadmap:
        try:
            parsed = json.loads(_strip_markdown_fences(raw_content))
        except json.JSONDecodeError as exc:
            error = ServiceError(SCHEMA_VALIDATION_FAILED, "Invalid JSON returned by model", "json_parse")
            setattr(error, "raw_content", raw_content)
            raise error from exc

        allowed_urls = {resource.url for resource in resources}
        self._reject_unknown_urls(parsed, allowed_urls)
        parsed = _fill_missing_project_resources(parsed)
        parsed = assign_backend_ids(parsed, normalized)
        parsed["metadata"] = {
            "model_used": model_used,
            "resource_sources": sorted({resource.source.lower() for resource in resources}) or ["seed"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }
        try:
            return Roadmap.model_validate(parsed)
        except ValidationError as exc:
            error = ServiceError(SCHEMA_VALIDATION_FAILED, "Roadmap schema validation failed", "schema_validation")
            setattr(error, "raw_content", raw_content)
            raise error from exc

    def _reject_unknown_urls(self, parsed: dict[str, Any], allowed_urls: set[str]) -> None:
        if not allowed_urls:
            return
        for resource in _iter_resources(parsed):
            url = resource.get("url")
            if url not in allowed_urls:
                error = ServiceError(SCHEMA_VALIDATION_FAILED, f"Unknown resource URL: {url}", "resource_validation")
                setattr(error, "raw_content", json.dumps(parsed))
                raise error

    def _load_demo_fallback(self, normalized: str) -> Roadmap | None:
        mapping = {
            "python": "python_for_beginners.json",
            "python-for-beginners": "python_for_beginners.json",
            "data-analysis": "data_analysis_with_excel.json",
            "data-analysis-with-excel": "data_analysis_with_excel.json",
            "excel": "data_analysis_with_excel.json",
            "graphic-design": "graphic_design.json",
            "ui-design": "graphic_design.json",
            "digital-marketing": "digital_marketing.json",
            "public-speaking": "public_speaking.json",
        }
        filename = mapping.get(normalized)
        if not filename:
            match = get_close_matches(normalized, mapping.keys(), n=1, cutoff=0.72)
            filename = mapping[match[0]] if match else None
        if not filename:
            return None

        path = Path(__file__).resolve().parents[1] / "data" / "demo_fallbacks" / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        data = assign_backend_ids(data, normalized)
        data["metadata"] = {
            "model_used": "demo_fallback",
            "resource_sources": ["demo"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cached": False,
            "fallback": True,
        }
        return Roadmap.model_validate(data)


def _strip_markdown_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        return "\n".join(lines).strip()
    return text


def _iter_resources(parsed: dict[str, Any]):
    for phase in parsed.get("phases", []):
        for node in phase.get("nodes", []):
            yield from node.get("resources", [])
        yield from phase.get("project", {}).get("resources", [])


def _fill_missing_project_resources(parsed: dict[str, Any]) -> dict[str, Any]:
    for phase in parsed.get("phases", []):
        project = phase.get("project", {})
        if not project.get("resources"):
            first_node_resources = phase.get("nodes", [{}])[0].get("resources", [])
            project["resources"] = first_node_resources[:2]
        phase["project"] = project
    return parsed


def _built_in_seed_resources(normalized: str) -> list[ResourceCandidate]:
    label = normalized.replace("-", " ").title()
    return [
        ResourceCandidate(
            title=f"{label} beginner tutorial",
            url="https://www.youtube.com/watch?v=kqtD5dpn9C8",
            type=ResourceType.youtube_video,
            source="YouTube",
        ),
        ResourceCandidate(
            title=f"{label} beginner guide",
            url="https://www.freecodecamp.org/news/",
            type=ResourceType.article,
            source="Tavily",
        ),
        ResourceCandidate(
            title=f"Free {label} course",
            url="https://www.khanacademy.org/",
            type=ResourceType.free_course,
            source="Tavily",
        ),
    ]
