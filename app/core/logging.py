import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings


def log_failed_generation(
    settings: Settings,
    *,
    normalized_skill: str,
    stage: str,
    model_used: str | None = None,
    validation_error_summary: str | None = None,
    raw_model_response: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    if not settings.log_failed_generations:
        return

    log_dir = Path("logs/failed_generations")
    if not log_dir.is_absolute():
        log_dir = Path.cwd() / "app" / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "timestamp": timestamp,
        "normalized_skill": normalized_skill,
        "stage": stage,
        "model_used": model_used,
        "validation_error_summary": validation_error_summary,
        "raw_model_response": raw_model_response,
        "extra": extra or {},
    }
    safe_name = f"{timestamp.replace(':', '-').replace('.', '-')}_{normalized_skill or 'unknown'}.json"
    (log_dir / safe_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
