from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.roadmap import ResourceType


class GenerateRoadmapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(..., min_length=1, max_length=120)
    user_level: str = "complete beginner"
    goal: str = "learn the skill step by step and build practical confidence"
    time_commitment: str = "3 to 5 hours per week"
    preferred_resource_types: list[ResourceType] = Field(
        default_factory=lambda: [
            ResourceType.youtube_video,
            ResourceType.article,
            ResourceType.free_course,
            ResourceType.documentation,
            ResourceType.free_book,
            ResourceType.interactive_practice,
        ]
    )
    language: str = "English"

    @field_validator("skill", "user_level", "goal", "time_commitment", "language")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("must not be empty")
        return value
