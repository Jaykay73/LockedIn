import httpx

from app.core.config import Settings
from app.core.errors import MODEL_PROVIDER_FAILED, ServiceError


class DeepSeekClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate_json(self, prompt: str, model: str) -> str:
        if not self.settings.deepseek_api_key:
            raise ServiceError(
                code=MODEL_PROVIDER_FAILED,
                message="DeepSeek API key is not configured",
                stage="deepseek_generation",
            )

        url = self.settings.deepseek_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You return strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.settings.roadmap_generation_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ServiceError(
                code=MODEL_PROVIDER_FAILED,
                message="DeepSeek returned an unexpected response shape",
                stage="deepseek_generation",
            ) from exc
