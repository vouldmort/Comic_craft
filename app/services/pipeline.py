from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import ComicGenerationResult, PromptRequest
from app.services.exporters import PdfExportError, save_pdf
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout


def generate_comic(request: PromptRequest) -> ComicGenerationResult:
    outline = generate_outline(request)
    stories = generate_story(outline, request)
    image_paths: dict[int, str] = {}
    for panel in outline:
        image_paths[panel.panel_number] = generate_image(panel.image_prompt, panel.panel_number, request.art_style)
    layout = build_comic_layout(outline, stories, image_paths)
    pdf_path: str | None = None
    warning: str | None = None
    try:
        pdf_path = save_pdf(layout, f"{request.character_name}'s Comic")
    except PdfExportError:
        warning = "Your comic was created, but the PDF export could not be generated."
    return ComicGenerationResult(
        panels=layout,
        pdf_path=pdf_path,
        generated_at=datetime.now(timezone.utc),
        export_warning=warning,
    )
