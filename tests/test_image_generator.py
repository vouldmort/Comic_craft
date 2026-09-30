from pathlib import Path
from types import SimpleNamespace
from PIL import Image

from app.services import image_generator


class FakeResult:
    def __init__(self):
        self.images = [Image.new("RGB", (64, 64), "white")]


class FakePipeline:
    def __call__(self, prompt, **kwargs):
        return FakeResult()


def test_generated_filenames_are_safe_and_collision_resistant(tmp_path, monkeypatch):
    monkeypatch.setattr(image_generator, "settings", SimpleNamespace(panels_dir=tmp_path, image_model_id="x", device="cpu"))
    monkeypatch.setattr(image_generator, "get_image_pipeline", lambda: FakePipeline())
    first = image_generator.generate_image("my secret prompt text", 1, "Comic")
    second = image_generator.generate_image("my secret prompt text", 1, "Comic")
    assert "my secret" not in first
    assert first != second


def test_get_image_pipeline_is_cached(monkeypatch):
    calls = []
    class DummyPipe:
        @classmethod
        def from_pretrained(cls, model_id):
            calls.append(model_id)
            return cls()
        def to(self, device):
            return self
    image_generator.get_image_pipeline.cache_clear()
    monkeypatch.setattr(image_generator, "_load_pipeline_class", lambda: DummyPipe)
    monkeypatch.setattr(image_generator, "settings", SimpleNamespace(panels_dir=Path("x"), image_model_id="model-x", device="cpu"))
    assert image_generator.get_image_pipeline() is image_generator.get_image_pipeline()
    assert calls == ["model-x"]
    image_generator.get_image_pipeline.cache_clear()


def test_successful_generation_saves_panel_and_returns_static_path(tmp_path, monkeypatch):
    monkeypatch.setattr(image_generator, "settings", SimpleNamespace(panels_dir=tmp_path, image_model_id="x", device="cpu"))
    monkeypatch.setattr(image_generator, "get_image_pipeline", lambda: FakePipeline())
    path = image_generator.generate_image("fox", 2, "Anime")
    assert path.startswith("/static/panels/")
    assert any(tmp_path.glob("*.png"))


def test_generation_failure_returns_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(image_generator, "settings", SimpleNamespace(panels_dir=tmp_path, image_model_id="x", device="cpu"))
    def fail():
        raise RuntimeError("boom")
    monkeypatch.setattr(image_generator, "get_image_pipeline", fail)
    assert image_generator.generate_image("fox", 3, "Comic") == "/static/placeholders/panel-placeholder.png"
