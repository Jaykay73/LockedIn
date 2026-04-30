import json

from app.services.resource_filter import ResourceCandidate


def build_repair_prompt(raw_content: str, validation_error: str, resources: list[ResourceCandidate]) -> str:
    allowed_urls = [resource.url for resource in resources]
    return f"""
Repair the following roadmap content into valid JSON only.
No markdown fences. No explanations outside JSON.
Preserve content as much as possible.
Do not add fake links. Do not invent resources.
Use only these allowed URLs:
{json.dumps(allowed_urls, indent=2)}

Validation error:
{validation_error}

Content to repair:
{raw_content}
""".strip()
