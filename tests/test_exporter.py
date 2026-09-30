from pathlib import Path
from types import SimpleNamespace
import pytest

from app.schemas import ComicPanelLayout
from app.services import exporters


def layout():
    return [ComicPanelLayout(panel_number=i,title=f"Title {i}",scene_description=f"Scene {i}",narration=f"Narration {i}",dialogue=f"Hello {i}",image_path="/static/placeholders/panel-placeholder.png") for i in range(1,6)]


def test_five_panel_layout_creates_nonempty_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(exporters, "settings", SimpleNamespace(exports_dir=tmp_path))
    web_path = exporters.save_pdf(layout(), "Fox Story")
    assert web_path.startswith("/static/exports/")
    files = list(tmp_path.glob("*.pdf"))
    assert len(files) == 1 and files[0].stat().st_size > 0
    assert "Fox Story" not in files[0].name


def test_unreadable_image_falls_back_to_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(exporters, "settings", SimpleNamespace(exports_dir=tmp_path))
    panels = layout(); panels[0].image_path = "/static/panels/does-not-exist.png"
    assert exporters.save_pdf(panels, "Test").endswith(".pdf")


def test_unrecoverable_pdf_writer_failure_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(exporters, "settings", SimpleNamespace(exports_dir=tmp_path))
    monkeypatch.setattr(exporters.FPDF, "output", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("disk failed")))
    with pytest.raises(exporters.PdfExportError):
        exporters.save_pdf(layout(), "Test")
