from dataclasses import dataclass
from typing import Any


ROADMAP_GENERATION_FAILED = "ROADMAP_GENERATION_FAILED"
RESOURCE_SEARCH_FAILED = "RESOURCE_SEARCH_FAILED"
MODEL_PROVIDER_FAILED = "MODEL_PROVIDER_FAILED"
SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
LINK_VALIDATION_FAILED = "LINK_VALIDATION_FAILED"
CACHE_ERROR = "CACHE_ERROR"


@dataclass
class ServiceError(Exception):
    code: str
    message: str
    stage: str
    retryable: bool = True
    debug: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code} at {self.stage}: {self.message}"
