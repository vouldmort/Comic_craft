from app.schemas import ComicPanelOutline, ComicPanelStory, ComicPanelLayout, PromptRequest
from app.services import pipeline
from app.services.exporters import PdfExportError


def request():
    return PromptRequest(story_prompt='A brave fox exploring an enchanted forest.', character_name='Fenn', setting='Enchanted Forest', tone='Adventure', art_style='Comic Book')


def outlines():
    return [ComicPanelOutline(panel_number=i,title=f'T{i}',scene_description=f'S{i}',image_prompt=f'I{i}') for i in range(1,6)]


def stories():
    return [ComicPanelStory(panel_number=i,narration=f'N{i}',dialogue=f'D{i}') for i in range(1,6)]


def layouts(images):
    return [ComicPanelLayout(panel_number=i,title=f'T{i}',scene_description=f'S{i}',narration=f'N{i}',dialogue=f'D{i}',image_path=images[i]) for i in range(1,6)]


def test_pipeline_calls_services_in_logical_order(monkeypatch):
    calls=[]
    monkeypatch.setattr(pipeline,'generate_outline',lambda req: calls.append('outline') or outlines())
    monkeypatch.setattr(pipeline,'generate_story',lambda o,req: calls.append('story') or stories())
    monkeypatch.setattr(pipeline,'generate_image',lambda prompt,num,style: calls.append(f'image{num}') or f'/static/panels/{num}.png')
    monkeypatch.setattr(pipeline,'build_comic_layout',lambda o,s,imgs: calls.append('layout') or layouts(imgs))
    monkeypatch.setattr(pipeline,'save_pdf',lambda lay,title: calls.append('pdf') or '/static/exports/x.pdf')
    result=pipeline.generate_comic(request())
    assert calls==['outline','story','image1','image2','image3','image4','image5','layout','pdf']
    assert len(result.panels)==5 and result.pdf_path.endswith('.pdf')


def test_pdf_failure_preserves_preview(monkeypatch):
    monkeypatch.setattr(pipeline,'generate_outline',lambda req: outlines())
    monkeypatch.setattr(pipeline,'generate_story',lambda o,req: stories())
    monkeypatch.setattr(pipeline,'generate_image',lambda *args: '/static/placeholders/panel-placeholder.png')
    monkeypatch.setattr(pipeline,'build_comic_layout',lambda o,s,imgs: layouts(imgs))
    def fail(*args): raise PdfExportError('boom')
    monkeypatch.setattr(pipeline,'save_pdf',fail)
    result=pipeline.generate_comic(request())
    assert len(result.panels)==5
    assert result.pdf_path is None
    assert result.export_warning


def test_outline_failure_propagates(monkeypatch):
    def fail(req): raise RuntimeError('outline failed')
    monkeypatch.setattr(pipeline,'generate_outline',fail)
    try:
        pipeline.generate_comic(request())
    except RuntimeError as exc:
        assert 'outline failed' in str(exc)
    else:
        raise AssertionError('expected generation failure')
