from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.schemas import PromptRequest
from app.services.image_generator import generate_image
from app.services.pipeline import generate_comic

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate", response_class=HTMLResponse)
async def generate_from_form(request: Request):
    form = await request.form()
    try:
        prompt = PromptRequest(
            story_prompt=str(form.get("story_prompt", "")),
            character_name=str(form.get("character_name", "")),
            setting=str(form.get("setting", "")),
            tone=str(form.get("tone", "")),
            art_style=str(form.get("art_style", "")),
        )
    except ValidationError:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Please enter valid values in all required fields."},
            status_code=422,
        )
    try:
        result = generate_comic(prompt)
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Comic generation failed. Please check your configuration and try again."},
            status_code=500,
        )
    return templates.TemplateResponse(request=request, name="comic_preview.html", context={"result": result, "request_data": prompt})


@router.post("/generate-comic/json")
def generate_from_json(prompt: PromptRequest):
    try:
        result = generate_comic(prompt)
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Comic generation failed."})
    return JSONResponse(content=result.model_dump(mode="json"))


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request):
    return templates.TemplateResponse(request=request, name="export_success.html", context={})


@router.post("/test-image")
async def test_image(request: Request):
    if not settings.enable_test_image:
        raise HTTPException(status_code=404, detail="Not found")
    payload = await request.json()
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt is required")
    path = generate_image(prompt, 1, "Comic Book")
    return {"image_path": path}
