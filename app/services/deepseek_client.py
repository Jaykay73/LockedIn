from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.errors import MODEL_PROVIDER_FAILED, ServiceError


class DeepSeekClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            if not self.settings.deepseek_api_key:
                raise ServiceError(
                    code=MODEL_PROVIDER_FAILED,
                    message="DeepSeek API key is not configured",
                    stage="deepseek_generation",
                )
            self._client = AsyncOpenAI(
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url,
                timeout=self.settings.roadmap_generation_timeout_seconds,
            )
        return self._client

    async def generate_json(self, prompt: str, model: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Response content is None")
            return content
        except Exception as exc:
            raise ServiceError(
                code=MODEL_PROVIDER_FAILED,
                message=f"DeepSeek generation failed: {type(exc).__name__} - {str(exc)}",
                stage="deepseek_generation",
            ) from exc
