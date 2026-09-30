from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PromptRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    story_prompt: str = Field(min_length=1, max_length=2000)
    character_name: str = Field(min_length=1, max_length=120)
    setting: str = Field(min_length=1, max_length=200)
    tone: str = Field(min_length=1, max_length=80)
    art_style: str = Field(min_length=1, max_length=80)

    @field_validator("story_prompt", "character_name", "setting", "tone", "art_style")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ComicPanelOutline(BaseModel):
    panel_number: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=200)
    scene_description: str = Field(min_length=1, max_length=2000)
    image_prompt: str = Field(min_length=1, max_length=2000)


class ComicPanelStory(BaseModel):
    panel_number: int = Field(ge=1, le=5)
    narration: str = Field(min_length=1, max_length=3000)
    dialogue: str | None = Field(default=None, max_length=2000)


class ComicPanelLayout(BaseModel):
    panel_number: int = Field(ge=1, le=5)
    title: str
    scene_description: str
    narration: str
    dialogue: str | None = None
    image_path: str


class ComicGenerationResult(BaseModel):
    panels: list[ComicPanelLayout]
    pdf_path: str | None
    generated_at: datetime
    export_warning: str | None = None
