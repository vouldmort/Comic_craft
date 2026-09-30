import json
import pytest

from app.schemas import ComicPanelOutline, PromptRequest
from app.services.gemini_pro import StoryGenerationError, parse_story_response, build_story_prompt


def stories():
    return [{"panel_number": i, "narration": f"Narration {i}", "dialogue": None if i == 5 else f"Line {i}"} for i in range(1,6)]


def outline():
    return [ComicPanelOutline(panel_number=i, title=f"P{i}", scene_description=f"Scene {i}", image_prompt=f"Image {i}") for i in range(1,6)]


def request():
    return PromptRequest(story_prompt="Fox quest", character_name="Fenn", setting="Forest", tone="Adventure", art_style="Comic")


def test_story_json_parses_five_ordered_items():
    result = parse_story_response(json.dumps(stories()))
    assert [p.panel_number for p in result] == [1,2,3,4,5]
    assert result[-1].dialogue is None


def test_story_fenced_json_is_accepted():
    result = parse_story_response("```json\n" + json.dumps(stories()) + "\n```")
    assert len(result) == 5


def test_duplicate_or_missing_panel_numbers_are_rejected():
    data = stories(); data[4]["panel_number"] = 4
    with pytest.raises(StoryGenerationError):
        parse_story_response(json.dumps(data))


def test_narration_is_required_but_dialogue_is_optional():
    data = stories(); data[0].pop("dialogue"); data[1].pop("narration")
    with pytest.raises(StoryGenerationError):
        parse_story_response(json.dumps(data))


def test_story_prompt_preserves_character_and_tone():
    prompt = build_story_prompt(outline(), request())
    assert "Fenn" in prompt and "Adventure" in prompt and "Narration" in prompt

def test_generate_story_uses_current_genai_client(monkeypatch):
    from types import SimpleNamespace
    import app.services.gemini_pro as svc
    class Models:
        def generate_content(self, model, contents):
            assert model == 'model-story'
            return SimpleNamespace(text=json.dumps(stories()))
    fake_client = SimpleNamespace(models=Models())
    monkeypatch.setattr(svc, '_create_client', lambda: fake_client, raising=False)
    monkeypatch.setattr(svc, 'settings', SimpleNamespace(gemini_api_key='key', gemini_story_model='model-story'))
    result = svc.generate_story(outline(), request())
    assert len(result) == 5
