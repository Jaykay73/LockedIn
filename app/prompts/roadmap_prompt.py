import json

from app.schemas.requests import GenerateRoadmapRequest
from app.services.resource_filter import ResourceCandidate


def build_roadmap_prompt(request: GenerateRoadmapRequest, resources: list[ResourceCandidate]) -> str:
    resource_payload = [
        {
            "title": resource.title,
            "url": resource.url,
            "type": resource.type.value,
            "source": resource.source,
            "is_free": True,
            "snippet": resource.snippet[:300],
        }
        for resource in resources
    ]
    return f"""
You are generating a beginner-friendly learning roadmap for LockedIn.
Return JSON only. Do not use markdown. Do not include explanations outside JSON.
Use only the provided resources. Do not invent URLs. Do not output paid resources.
Support non-tech skills as well as tech skills.

User request:
- skill: {request.skill}
- user_level: {request.user_level}
- goal: {request.goal}
- time_commitment: {request.time_commitment}
- preferred_resource_types: {[item.value for item in request.preferred_resource_types]}
- language: {request.language}

Rules:
- Create exactly 3 phases.
- Each phase must have exactly 3 nodes.
- Each phase must have exactly 1 project.
- Each node must have 2 to 4 resources.
- Use simple beginner-friendly language.
- Make the roadmap practical and project-based.
- Keep descriptions concise but useful.
- Do not generate IDs. Omit id fields or leave them empty.
- Output valid JSON matching this shape:
{{
  "skill": "Readable Skill Name",
  "overview": "Short beginner-friendly overview",
  "estimated_total_duration": "6-8 weeks",
  "phases": [
    {{
      "title": "Beginner",
      "level": "beginner",
      "goal": "...",
      "estimated_duration": "2 weeks",
      "nodes": [
        {{
          "title": "...",
          "description": "2-3 useful sentences.",
          "estimated_completion_time": "2-3 hours",
          "resources": [
            {{"title": "...", "url": "https://...", "type": "youtube_video", "source": "YouTube", "is_free": true}}
          ]
        }}
      ],
      "project": {{
        "title": "...",
        "brief": "...",
        "tools_needed": ["..."],
        "resources": []
      }}
    }}
  ]
}}

Provided resource candidates:
{json.dumps(resource_payload, indent=2)}
""".strip()
