import json
import pytest
from app.schemas import PromptRequest
from app.services.gemini_flash import OutlineGenerationError, parse_outline_response, build_outline_prompt


def five_panels():
    return [{"panel_number": i, "title": f"P{i}", "scene_description": f"Scene {i}", "image_prompt": f"Image {i}"} for i in range(1,6)]


def test_valid_json_parses_five_panels():
    result = parse_outline_response(json.dumps(five_panels()))
    assert [p.panel_number for p in result] == [1,2,3,4,5]


def test_fenced_json_is_recovered():
    result = parse_outline_response("```json\n" + json.dumps(five_panels()) + "\n```")
    assert len(result) == 5


def test_fewer_than_five_panels_rejected():
    with pytest.raises(OutlineGenerationError):
        parse_outline_response(json.dumps(five_panels()[:4]))


def test_missing_required_panel_field_rejected():
    data = five_panels(); del data[2]["title"]
    with pytest.raises(OutlineGenerationError):
        parse_outline_response(json.dumps(data))


def test_outline_prompt_mentions_user_values_and_exact_count():
    req = PromptRequest(story_prompt="Fox quest", character_name="Fenn", setting="Forest", tone="Adventure", art_style="Comic")
    prompt = build_outline_prompt(req)
    assert "Fenn" in prompt and "Forest" in prompt and "exactly 5" in prompt.lower()

def test_generate_outline_uses_current_genai_client(monkeypatch):
    from types import SimpleNamespace
    import app.services.gemini_flash as svc
    class Models:
        def generate_content(self, model, contents):
            assert model == 'model-outline'
            return SimpleNamespace(text=json.dumps(five_panels()))
    fake_client = SimpleNamespace(models=Models())
    monkeypatch.setattr(svc, '_create_client', lambda: fake_client, raising=False)
    monkeypatch.setattr(svc, 'settings', SimpleNamespace(gemini_api_key='key', gemini_outline_model='model-outline'))
    result = svc.generate_outline(PromptRequest(story_prompt='Fox quest', character_name='Fenn', setting='Forest', tone='Adventure', art_style='Comic'))
    assert len(result) == 5
