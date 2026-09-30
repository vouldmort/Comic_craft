import pytest
from pydantic import ValidationError

from app.schemas import PromptRequest


def valid_payload():
    return {
        "story_prompt": "A brave fox exploring an enchanted forest.",
        "character_name": "Fenn",
        "setting": "Enchanted Forest",
        "tone": "Adventure",
        "art_style": "Comic Book",
    }


def test_prompt_request_accepts_valid_values():
    req = PromptRequest(**valid_payload())
    assert req.story_prompt == "A brave fox exploring an enchanted forest."
    assert req.character_name == "Fenn"
    assert req.setting == "Enchanted Forest"
    assert req.tone == "Adventure"
    assert req.art_style == "Comic Book"


def test_prompt_request_rejects_blank_required_values():
    payload = valid_payload()
    payload["story_prompt"] = "   "
    with pytest.raises(ValidationError):
        PromptRequest(**payload)


def test_prompt_request_rejects_oversized_values():
    payload = valid_payload()
    payload["story_prompt"] = "x" * 2001
    with pytest.raises(ValidationError):
        PromptRequest(**payload)
