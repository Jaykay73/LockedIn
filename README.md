# LockedIn AI Service

Standalone FastAPI AI service for generating beginner-friendly learning roadmaps for tech and non-tech skills. It returns validated JSON only and does not handle auth, Supabase, frontend, progress tracking, streaks, or user data.

## Architecture

- FastAPI API layer exposes `POST /api/v1/roadmaps/generate`.
- Tavily and YouTube clients fetch real resource candidates.
- Resource filters remove paid-looking, irrelevant, duplicate, or broken links.
- DeepSeek generates the roadmap using only fetched resources.
- Pydantic v2 validates the final schema.
- Backend code assigns all stable IDs.
- SQLite caches validated roadmaps by normalized request hash.
- Demo fallback roadmaps cover common hackathon examples when providers fail.

## Setup

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install dependencies:

```bash
uv sync
```

Create a local `.env` from `.env.example` and fill real keys:

```bash
cp .env.example .env
```

Never commit `.env`.

## Environment Variables

Required for live generation:

- `DEEPSEEK_API_KEY`
- `TAVILY_API_KEY`
- `YOUTUBE_API_KEY`

Important defaults:

- `DEEPSEEK_DEFAULT_MODEL=deepseek-v4-flash`
- `DEEPSEEK_FALLBACK_MODEL=deepseek-v4-pro`
- `ENABLE_CACHE=true`
- `ENABLE_DEMO_FALLBACK=true`
- `SQLITE_DB_PATH=./lockedin_cache.db`
- `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173`

## Run Locally

```bash
uv run fastapi dev app/main.py
```

Alternative:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

Health check:

```bash
curl http://localhost:7860/health
```

Generate a roadmap:

```bash
curl -X POST http://localhost:7860/api/v1/roadmaps/generate \
  -H "Content-Type: application/json" \
  -d '{"skill":"Learn Python"}'
```

## Tests

Tests mock external providers and do not consume DeepSeek, Tavily, or YouTube credits.

```bash
uv run pytest
```

## Docker

Build:

```bash
docker build -t lockedin-ai-service .
```

Run:

```bash
docker run --env-file .env -p 7860:7860 lockedin-ai-service
```

## Hugging Face Spaces Docker Notes

Use the Docker SDK option in Spaces. Add the environment variables as Space secrets. The container listens on port `7860` and starts:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 7860
```

## API Shape

Request:

```json
{
  "skill": "Learn Python",
  "user_level": "complete beginner",
  "goal": "build projects",
  "time_commitment": "5 hours per week",
  "preferred_resource_types": ["youtube_video", "article", "free_course"],
  "language": "English"
}
```

Success response:

```json
{
  "success": true,
  "data": {
    "roadmap_id": "roadmap_python_abc123",
    "skill": "Python for Beginners",
    "normalized_skill": "python",
    "overview": "...",
    "estimated_total_duration": "6-8 weeks",
    "phases": [],
    "projects": [],
    "metadata": {
      "model_used": "deepseek-v4-flash",
      "resource_sources": ["tavily", "youtube"],
      "generated_at": "2026-04-30T00:00:00Z",
      "cached": false
    }
  }
}
```

Failure response:

```json
{
  "success": false,
  "error": {
    "code": "ROADMAP_GENERATION_FAILED",
    "message": "We could not generate this roadmap right now. Please try again.",
    "retryable": true
  }
}
```
