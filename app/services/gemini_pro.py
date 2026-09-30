from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.config import settings
from app.schemas import ComicPanelOutline, ComicPanelStory, PromptRequest


class StoryGenerationError(RuntimeError):
    pass


def _extract_json(raw_text: str) -> str:
    text = raw_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("["):
        start, end = text.find("["), text.rfind("]")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return text


def parse_story_response(raw_text: str) -> list[ComicPanelStory]:
    try:
        payload = json.loads(_extract_json(raw_text))
        panels = [ComicPanelStory.model_validate(item) for item in payload]
    except (json.JSONDecodeError, TypeError, ValidationError, KeyError) as exc:
        raise StoryGenerationError("Gemini returned invalid story content.") from exc
    if len(panels) != 5 or {p.panel_number for p in panels} != {1, 2, 3, 4, 5}:
        raise StoryGenerationError("Comic story must contain exactly five unique panels numbered 1 through 5.")
    return sorted(panels, key=lambda p: p.panel_number)


def build_story_prompt(outline: list[ComicPanelOutline], request: PromptRequest) -> str:
    outline_json = json.dumps([p.model_dump() for p in outline], ensure_ascii=False)
    return f"""Expand this five-panel comic outline into strict JSON array only.
Each object must contain panel_number and Narration; use JSON key narration. dialogue is optional and may be null.
Main character: {request.character_name}
Tone: {request.tone}
Setting: {request.setting}
Keep scene meaning and panel numbers unchanged. Keep the main character consistent. Do not include Markdown.
Outline: {outline_json}"""


def _create_client():
    from google import genai
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_text(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise StoryGenerationError("GEMINI_API_KEY is not configured.")
    try:
        client = _create_client()
        response = client.models.generate_content(model=settings.gemini_story_model, contents=prompt)
        return response.text
    except Exception as exc:
        raise StoryGenerationError("Unable to generate comic narration.") from exc


def generate_story(outline: list[ComicPanelOutline], request: PromptRequest) -> list[ComicPanelStory]:
    return parse_story_response(_generate_text(build_story_prompt(outline, request)))
