from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.roadmap import Roadmap


class SuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: Roadmap


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool = True
    debug: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = False
    error: ErrorDetail
