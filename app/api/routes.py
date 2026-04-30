from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import ROADMAP_GENERATION_FAILED, ServiceError
from app.schemas.requests import GenerateRoadmapRequest
from app.schemas.responses import ErrorDetail, ErrorResponse, SuccessResponse
from app.services.roadmap_generator import RoadmapGenerator

router = APIRouter()
generator = RoadmapGenerator()


@router.post("/api/v1/roadmaps/generate")
async def generate_roadmap(request: GenerateRoadmapRequest):
    settings = get_settings()
    try:
        roadmap = await generator.generate(request)
        return SuccessResponse(data=roadmap)
    except Exception as exc:
        debug = None
        if settings.is_development:
            debug = {
                "reason": str(exc),
                "stage": getattr(exc, "stage", "unknown"),
            }
            if isinstance(exc, ServiceError) and exc.debug:
                debug.update(exc.debug)
        response = ErrorResponse(
            error=ErrorDetail(
                code=ROADMAP_GENERATION_FAILED,
                message="We could not generate this roadmap right now. Please try again.",
                retryable=True,
                debug=debug,
            )
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(exclude_none=True))
