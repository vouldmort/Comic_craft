from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.config import settings
from app.schemas import ComicPanelOutline, PromptRequest


class OutlineGenerationError(RuntimeError):
    pass


def _extract_json(raw_text: str) -> str:
    text = raw_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("["):
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return text


def parse_outline_response(raw_text: str) -> list[ComicPanelOutline]:
    try:
        payload = json.loads(_extract_json(raw_text))
        panels = [ComicPanelOutline.model_validate(item) for item in payload]
    except (json.JSONDecodeError, TypeError, ValidationError, KeyError) as exc:
        raise OutlineGenerationError("Gemini returned an invalid comic outline.") from exc
    if len(panels) != 5 or {p.panel_number for p in panels} != {1, 2, 3, 4, 5}:
        raise OutlineGenerationError("Comic outline must contain exactly five unique panels numbered 1 through 5.")
    return sorted(panels, key=lambda p: p.panel_number)


def build_outline_prompt(request: PromptRequest) -> str:
    return f"""Create exactly 5 ordered comic panels as strict JSON array only.
Each object must have: panel_number, title, scene_description, image_prompt.
Story idea: {request.story_prompt}
Main character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}
Keep the same main character and a coherent beginning, middle, and ending. Do not include Markdown."""


def _create_client():
    from google import genai
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_text(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise OutlineGenerationError("GEMINI_API_KEY is not configured.")
    try:
        client = _create_client()
        response = client.models.generate_content(model=settings.gemini_outline_model, contents=prompt)
        return response.text
    except Exception as exc:  # network/provider boundary
        raise OutlineGenerationError("Unable to generate comic outline.") from exc


def generate_outline(request: PromptRequest) -> list[ComicPanelOutline]:
    return parse_outline_response(_generate_text(build_outline_prompt(request)))
