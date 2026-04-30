from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer, field_validator, model_validator


class ResourceType(StrEnum):
    youtube_video = "youtube_video"
    article = "article"
    free_course = "free_course"
    documentation = "documentation"
    free_book = "free_book"
    interactive_practice = "interactive_practice"


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="", max_length=120)
    title: str = Field(..., min_length=1, max_length=220)
    url: HttpUrl
    type: ResourceType
    source: str = Field(..., min_length=1, max_length=80)
    is_free: bool

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        return str(value)

    @field_validator("is_free")
    @classmethod
    def must_be_free(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("resource must be free")
        return value


class RoadmapNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="", max_length=120)
    title: str = Field(..., min_length=1, max_length=180)
    description: str = Field(..., min_length=20, max_length=700)
    estimated_completion_time: str = Field(..., min_length=1, max_length=80)
    resources: list[Resource] = Field(..., min_length=2, max_length=4)


class Project(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="", max_length=120)
    phase_id: str = Field(default="", max_length=120)
    title: str = Field(..., min_length=1, max_length=180)
    brief: str = Field(..., min_length=20, max_length=900)
    tools_needed: list[str] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list, max_length=4)

    @field_validator("tools_needed")
    @classmethod
    def clean_tools(cls, value: list[str]) -> list[str]:
        return [tool.strip() for tool in value if tool.strip()]


class Phase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="", max_length=120)
    title: str = Field(..., min_length=1, max_length=120)
    level: str = Field(..., min_length=1, max_length=80)
    goal: str = Field(..., min_length=1, max_length=500)
    estimated_duration: str = Field(..., min_length=1, max_length=80)
    nodes: list[RoadmapNode] = Field(..., min_length=3, max_length=3)
    project: Project


class RoadmapMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_used: str = ""
    resource_sources: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cached: bool = False
    fallback: bool = False


class Roadmap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roadmap_id: str = Field(default="", max_length=160)
    skill: str = Field(..., min_length=1, max_length=160)
    normalized_skill: str = Field(..., min_length=1, max_length=160)
    overview: str = Field(..., min_length=20, max_length=1200)
    estimated_total_duration: str = Field(..., min_length=1, max_length=80)
    phases: list[Phase] = Field(..., min_length=3, max_length=3)
    projects: list[Project] = Field(..., min_length=3, max_length=3)
    metadata: RoadmapMetadata

    @model_validator(mode="after")
    def validate_project_consistency(self) -> "Roadmap":
        phase_projects = [phase.project for phase in self.phases]
        phase_project_ids = [project.id for project in phase_projects]
        top_project_ids = [project.id for project in self.projects]
        if phase_project_ids != top_project_ids:
            raise ValueError("flattened projects must match phase projects in order")
        for index, phase in enumerate(self.phases, start=1):
            expected_phase_id = f"phase_{index}"
            if phase.id and phase.id != expected_phase_id:
                raise ValueError("phase ids must be backend generated and sequential")
            if phase.project.phase_id and phase.project.phase_id != phase.id:
                raise ValueError("project phase_id must match phase id")
        return self


def roadmap_to_jsonable(roadmap: Roadmap) -> dict[str, Any]:
    return roadmap.model_dump(mode="json")
