from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fpdf import FPDF
from PIL import Image

from app.config import BASE_DIR, settings
from app.schemas import ComicPanelLayout


class PdfExportError(RuntimeError):
    pass


def _local_image_path(web_path: str) -> Path:
    if web_path.startswith("/static/"):
        candidate = BASE_DIR / web_path.lstrip("/")
    else:
        candidate = Path(web_path)
    if candidate.exists():
        return candidate
    return BASE_DIR / "static" / "placeholders" / "panel-placeholder.png"


def _latin(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def save_pdf(layout: list[ComicPanelLayout], title: str) -> str:
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"comic-{uuid4().hex}.pdf"
    destination = settings.exports_dir / filename
    try:
        pdf = FPDF(unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        for panel in sorted(layout, key=lambda p: p.panel_number):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 10, _latin(f"{title} - Panel {panel.panel_number}: {panel.title}"))
            image_path = _local_image_path(panel.image_path)
            with Image.open(image_path) as img:
                w, h = img.size
            max_w, max_h = 170, 105
            ratio = min(max_w / w, max_h / h)
            draw_w, draw_h = w * ratio, h * ratio
            x = (210 - draw_w) / 2
            pdf.image(str(image_path), x=x, w=draw_w, h=draw_h)
            pdf.ln(5)
            pdf.set_font("Helvetica", "I", 10)
            pdf.multi_cell(0, 6, _latin(panel.scene_description))
            pdf.ln(2)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 7, _latin(panel.narration))
            if panel.dialogue:
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(0, 7, _latin(f'Dialogue: "{panel.dialogue}"'))
        pdf.output(str(destination))
    except Exception as exc:
        try:
            destination.unlink(missing_ok=True)
        except Exception:
            pass
        raise PdfExportError("Could not export the comic PDF.") from exc
    return f"/static/exports/{filename}"
