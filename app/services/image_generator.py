from __future__ import annotations

import logging
from functools import lru_cache
from uuid import uuid4

from app.config import settings

logger = logging.getLogger(__name__)
PLACEHOLDER_PATH = "/static/placeholders/panel-placeholder.png"


def _load_pipeline_class():
    from diffusers import StableDiffusionPipeline
    return StableDiffusionPipeline


@lru_cache(maxsize=1)
def get_image_pipeline():
    pipeline_cls = _load_pipeline_class()
    pipe = pipeline_cls.from_pretrained(settings.image_model_id)
    try:
        pipe = pipe.to(settings.device)
    except Exception:
        logger.warning("Could not use configured device %s; falling back to CPU", settings.device)
        pipe = pipe.to("cpu")
    return pipe


def build_image_prompt(prompt: str, art_style: str) -> str:
    return f"{prompt}, {art_style} comic illustration, consistent character design, cinematic composition, no text"


def generate_image(prompt: str, panel_number: int, art_style: str) -> str:
    try:
        settings.panels_dir.mkdir(parents=True, exist_ok=True)
        filename = f"panel-{panel_number}-{uuid4().hex}.png"
        destination = settings.panels_dir / filename
        result = get_image_pipeline()(build_image_prompt(prompt, art_style), num_inference_steps=25)
        image = result.images[0]
        image.save(destination)
        return f"/static/panels/{filename}"
    except Exception:
        logger.exception("Panel %s image generation failed; using placeholder", panel_number)
        return PLACEHOLDER_PATH
