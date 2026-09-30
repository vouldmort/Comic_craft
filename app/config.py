from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_outline_model: str = os.getenv("GEMINI_OUTLINE_MODEL", "gemini-3.5-flash-lite")
    gemini_story_model: str = os.getenv("GEMINI_STORY_MODEL", "gemini-3.8-flash")
    image_model_id: str = os.getenv("IMAGE_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    device: str = os.getenv("DEVICE", "cuda")
    enable_test_image: bool = os.getenv("ENABLE_TEST_IMAGE", "false").lower() in {"1", "true", "yes", "on"}
    panels_dir: Path = Path(os.getenv("PANELS_DIR", str(BASE_DIR / "static" / "panels")))
    exports_dir: Path = Path(os.getenv("EXPORTS_DIR", str(BASE_DIR / "static" / "exports")))


settings = Settings()
