from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas import ComicGenerationResult, ComicPanelLayout


def fake_result(pdf_path='/static/exports/test.pdf', warning=None):
    panels=[ComicPanelLayout(panel_number=i,title=f'Title {i}',scene_description=f'Scene {i}',narration=f'Narration {i}',dialogue=f'Dialogue {i}',image_path='/static/placeholders/panel-placeholder.png') for i in range(1,6)]
    return ComicGenerationResult(panels=panels,pdf_path=pdf_path,generated_at=datetime.now(timezone.utc),export_warning=warning)


def valid_form():
    return {'story_prompt':'A brave fox exploring an enchanted forest.','character_name':'Fenn','setting':'Enchanted Forest','tone':'Adventure','art_style':'Comic Book'}


def test_health(client):
    r=client.get('/health')
    assert r.status_code==200 and r.json()=={'status':'healthy'}


def test_homepage_returns_200(client):
    assert client.get('/').status_code==200


def test_blank_form_returns_validation_without_pipeline_call(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'generate_comic',lambda req: (_ for _ in ()).throw(AssertionError('pipeline should not run')))
    data=valid_form(); data['story_prompt']='   '
    r=client.post('/generate',data=data)
    assert r.status_code==422
    assert 'valid' in r.text.lower() or 'required' in r.text.lower()


def test_json_generation_returns_five_panels(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'generate_comic',lambda req: fake_result())
    r=client.post('/generate-comic/json',json=valid_form())
    assert r.status_code==200
    body=r.json()
    assert len(body['panels'])==5
    assert body['pdf_path'].endswith('.pdf')


def test_generation_exception_is_safe(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'generate_comic',lambda req: (_ for _ in ()).throw(RuntimeError('SECRET_API_KEY_123')))
    r=client.post('/generate-comic/json',json=valid_form())
    assert r.status_code==500
    assert 'SECRET_API_KEY_123' not in r.text


def test_test_image_disabled(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'settings',SimpleNamespace(enable_test_image=False))
    r=client.post('/test-image',json={'prompt':'fox'})
    assert r.status_code==404

def test_homepage_contains_full_form_and_loading_overlay(client):
    r = client.get('/')
    text = r.text
    for name in ['story_prompt','character_name','setting','tone','art_style']:
        assert f'name="{name}"' in text
    assert 'Generate My Comic' in text
    assert 'loading-overlay' in text


def test_generate_preview_renders_five_panel_titles_images_and_download(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'generate_comic',lambda req: fake_result())
    r=client.post('/generate',data=valid_form())
    assert r.status_code==200
    for i in range(1,6):
        assert f'Title {i}' in r.text
    assert r.text.count('<img') >= 5
    assert '/static/exports/test.pdf' in r.text


def test_preview_shows_export_warning_without_pdf_link(client, monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes,'generate_comic',lambda req: fake_result(pdf_path=None, warning='PDF unavailable'))
    r=client.post('/generate',data=valid_form())
    assert r.status_code==200
    assert 'PDF unavailable' in r.text
    assert 'Download PDF' not in r.text
