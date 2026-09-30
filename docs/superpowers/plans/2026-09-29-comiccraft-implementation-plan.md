# ComicCraft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local FastAPI web app that turns a user's story prompt into a coherent five-panel comic with Gemini-generated text, Stable Diffusion illustrations, browser preview, JSON API output, and downloadable PDF export.

**Architecture:** Keep the request flow thin at the route layer and move each generation step into a focused service: outline generation, story expansion, image generation, layout composition, and PDF export. Pydantic models define the interfaces between services, and the browser form plus JSON endpoint both call the same orchestration path so behavior stays consistent.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic, Jinja2, Google Gemini API, Hugging Face Diffusers / Stable Diffusion v1.5, PyTorch, Pillow, FPDF2, python-dotenv, pytest, FastAPI TestClient.

**Spec:** `docs/superpowers/specs/2026-09-29-comiccraft-design.md`

## Global Constraints

- Python version: 3.11 or newer.
- Generate exactly five comic panels for every successful comic.
- Keep API keys only in environment variables; never hard-code or render them.
- Default image model: `runwayml/stable-diffusion-v1-5`.
- Image generation must fail gracefully by substituting a local placeholder instead of failing the whole comic.
- PDF export must not prevent the browser preview from being shown when export fails.
- All generated filenames must use server-generated identifiers; never derive filesystem paths directly from user input.
- Both `/generate` and `/generate-comic/json` must use the same core generation pipeline.
- Developer utility endpoints must be easy to disable through configuration.
- MVP remains single-user, local, five-panel, with no database, authentication, payments, cloud deployment, or persistent gallery.

## Review Focus

1. **Model returns malformed or Markdown-wrapped JSON** — parsing should strip wrappers, validate all five panels, and return a clear generation error only when recovery fails.
2. **User submits blank or oversized strings** — schema validation should reject them before any model call and preserve a user-friendly error response.
3. **One panel image generation fails** — the comic should still contain five ordered panels, using a placeholder only for the failed image.
4. **Story or image data arrives out of order or with a missing panel** — layout composition should normalize by `panel_number` and fail clearly for incomplete text data rather than silently mis-pairing content.
5. **PDF generation fails after a successful comic generation** — preview should still render and expose an export warning instead of returning a total request failure.

---

## File Map

### Application core
- `app/__init__.py` — package marker.
- `app/main.py` — FastAPI app creation, static mounting, router registration, exception wiring.
- `app/config.py` — environment-driven settings and output directory configuration.
- `app/schemas.py` — Pydantic request/result models shared across services and routes.
- `app/routes.py` — browser/API endpoints and orchestration entry points.

### Services
- `app/services/__init__.py` — package marker.
- `app/services/gemini_flash.py` — five-panel outline prompt, model call, robust JSON parsing.
- `app/services/gemini_pro.py` — per-panel narration/dialogue generation and parsing.
- `app/services/image_generator.py` — lazy Stable Diffusion pipeline, prompt construction, image persistence, placeholder fallback.
- `app/services/layout_builder.py` — merge outline/story/image results in stable panel order.
- `app/services/exporters.py` — safe PDF creation from normalized layout.
- `app/services/pipeline.py` — single orchestration function used by both form and JSON routes.

### Frontend
- `templates/index.html` — input form and loading overlay.
- `templates/comic_preview.html` — five-panel preview, export state, create-another action.
- `templates/export_success.html` — confirmation page.
- `templates/error.html` — safe user-facing generation error page.
- `static/css/style.css` — comic-themed responsive styling.
- `static/panels/.gitkeep` — output directory placeholder.
- `static/exports/.gitkeep` — output directory placeholder.
- `static/placeholders/panel-placeholder.png` — local fallback image.

### Tests and project metadata
- `tests/conftest.py` — test app fixtures and temp output directories.
- `tests/test_schemas.py` — request validation.
- `tests/test_gemini_flash.py` — outline parsing and malformed model output handling.
- `tests/test_gemini_pro.py` — story parsing and character/tone structure expectations.
- `tests/test_image_generator.py` — filename behavior, lazy pipeline boundary, placeholder fallback.
- `tests/test_layout_builder.py` — ordering, merging, and missing data behavior.
- `tests/test_exporter.py` — PDF creation and failure behavior.
- `tests/test_pipeline.py` — orchestration and partial-image/PDF failures.
- `tests/test_routes.py` — health, homepage, form validation, JSON generation, safe errors.
- `.env.example` — documented settings without secrets.
- `.gitignore` — Python, environment, model cache, generated output exclusions.
- `requirements.txt` — runtime/test dependencies.
- `README.md` — setup, configuration, run, test, and usage instructions.

---

### Task 1: Project Configuration and Shared Schemas

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/schemas.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `requirements.txt`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: environment variables defined in the spec.
- Produces: `Settings`, `PromptRequest`, `ComicPanelOutline`, `ComicPanelStory`, `ComicPanelLayout`, and `ComicGenerationResult` for all later tasks.

- [ ] **Step 1: Write failing schema tests**

Add tests named `test_prompt_request_accepts_valid_values`, `test_prompt_request_rejects_blank_required_values`, and `test_prompt_request_rejects_oversized_values`. Assert that a valid request preserves the five fields, whitespace-only required values fail validation, and the chosen bounds reject oversized prompt values.

- [ ] **Step 2: Run schema tests and verify failure**

Run: `pytest tests/test_schemas.py -v`

Expected: FAIL because `app.schemas` and its models do not exist.

- [ ] **Step 3: Implement configuration and schemas**

Create:
- `Settings` in `app/config.py` with fields `gemini_api_key`, `gemini_outline_model`, `gemini_story_model`, `image_model_id`, `device`, `enable_test_image`, `panels_dir`, and `exports_dir`.
- `PromptRequest` in `app/schemas.py` with fields `story_prompt`, `character_name`, `setting`, `tone`, `art_style`, trimming validators, nonblank validation, and conservative max lengths.
- `ComicPanelOutline(panel_number: int, title: str, scene_description: str, image_prompt: str)`.
- `ComicPanelStory(panel_number: int, narration: str, dialogue: str | None = None)`.
- `ComicPanelLayout(panel_number: int, title: str, scene_description: str, narration: str, dialogue: str | None, image_path: str)`.
- `ComicGenerationResult(panels: list[ComicPanelLayout], pdf_path: str | None, generated_at: datetime, export_warning: str | None = None)`.

Populate `.env.example`, `.gitignore`, and `requirements.txt` with the exact project dependencies and no secrets.

- [ ] **Step 4: Run schema tests and verify success**

Run: `pytest tests/test_schemas.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/__init__.py app/config.py app/schemas.py tests/test_schemas.py .env.example .gitignore requirements.txt
git commit -m "feat: add ComicCraft configuration and schemas"
```

---

### Task 2: Gemini Outline Generation

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/gemini_flash.py`
- Test: `tests/test_gemini_flash.py`

**Interfaces:**
- Consumes: `PromptRequest`.
- Produces: `parse_outline_response(raw_text: str) -> list[ComicPanelOutline]` and `generate_outline(request: PromptRequest) -> list[ComicPanelOutline]`.

- [ ] **Step 1: Write failing outline parsing tests**

Add tests that assert:
- valid JSON with five panels becomes five `ComicPanelOutline` objects numbered 1–5;
- a fenced ```json response is recovered correctly;
- fewer than five panels raises `OutlineGenerationError`;
- a panel missing `title`, `scene_description`, or `image_prompt` raises `OutlineGenerationError`.

- [ ] **Step 2: Run outline tests and verify failure**

Run: `pytest tests/test_gemini_flash.py -v`

Expected: FAIL because the outline service does not exist.

- [ ] **Step 3: Implement parsing and model-call boundary**

In `app/services/gemini_flash.py`, define:
- `class OutlineGenerationError(RuntimeError)`;
- `parse_outline_response(raw_text: str) -> list[ComicPanelOutline]`;
- `build_outline_prompt(request: PromptRequest) -> str` requesting exactly five ordered panels and strict machine-readable JSON;
- `generate_outline(request: PromptRequest) -> list[ComicPanelOutline]` using the configured Gemini outline model.

Keep the Gemini client/model call isolated so tests can monkeypatch it without network access.

- [ ] **Step 4: Run outline tests and verify success**

Run: `pytest tests/test_gemini_flash.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/__init__.py app/services/gemini_flash.py tests/test_gemini_flash.py
git commit -m "feat: add Gemini comic outline generation"
```

---

### Task 3: Gemini Story Expansion

**Files:**
- Create: `app/services/gemini_pro.py`
- Test: `tests/test_gemini_pro.py`

**Interfaces:**
- Consumes: `list[ComicPanelOutline]`, `PromptRequest`.
- Produces: `parse_story_response(raw_text: str) -> list[ComicPanelStory]` and `generate_story(outline: list[ComicPanelOutline], request: PromptRequest) -> list[ComicPanelStory]`.

- [ ] **Step 1: Write failing story service tests**

Assert that:
- five structured story items parse into five `ComicPanelStory` objects numbered 1–5;
- Markdown-wrapped JSON is accepted;
- duplicate or missing panel numbers are rejected;
- optional dialogue may be `null`/missing while narration is required.

- [ ] **Step 2: Run story tests and verify failure**

Run: `pytest tests/test_gemini_pro.py -v`

Expected: FAIL because `gemini_pro.py` does not exist.

- [ ] **Step 3: Implement story prompt, parser, and model call**

Define:
- `class StoryGenerationError(RuntimeError)`;
- `parse_story_response(raw_text: str) -> list[ComicPanelStory]`;
- `build_story_prompt(outline: list[ComicPanelOutline], request: PromptRequest) -> str` preserving panel meaning, requested tone, and main character consistency;
- `generate_story(...)` using the configured Gemini story model.

- [ ] **Step 4: Run story tests and verify success**

Run: `pytest tests/test_gemini_pro.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/gemini_pro.py tests/test_gemini_pro.py
git commit -m "feat: add Gemini comic story expansion"
```

---

### Task 4: Stable Diffusion Image Generation with Graceful Fallback

**Files:**
- Create: `app/services/image_generator.py`
- Create: `static/panels/.gitkeep`
- Create: `static/placeholders/panel-placeholder.png`
- Test: `tests/test_image_generator.py`

**Interfaces:**
- Consumes: panel prompt, panel number, art style, configured model/device.
- Produces: `generate_image(prompt: str, panel_number: int, art_style: str) -> str` returning a browser-safe `/static/...` path.

- [ ] **Step 1: Write failing image-generation boundary tests**

Add tests that assert:
- generated filenames do not contain user prompt text and are collision-safe;
- the model-loading function is cached/lazy so repeated generations reuse the pipeline;
- a mocked successful pipeline saves an image beneath `static/panels/` and returns its `/static/panels/...` path;
- a pipeline exception returns `/static/placeholders/panel-placeholder.png` instead of raising.

- [ ] **Step 2: Run image tests and verify failure**

Run: `pytest tests/test_image_generator.py -v`

Expected: FAIL because the image service does not exist.

- [ ] **Step 3: Implement lazy model loading and fallback**

Define:
- `get_image_pipeline()` as an `lru_cache(maxsize=1)` loader for the configured Diffusers pipeline;
- `build_image_prompt(prompt: str, art_style: str) -> str`;
- `generate_image(prompt: str, panel_number: int, art_style: str) -> str` using UUID-based filenames and Pillow-compatible saving;
- GPU preferred according to configuration, with safe CPU fallback when device setup is unavailable;
- exception handling that logs details and returns the placeholder path.

- [ ] **Step 4: Run image tests and verify success**

Run: `pytest tests/test_image_generator.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/image_generator.py static/panels/.gitkeep static/placeholders/panel-placeholder.png tests/test_image_generator.py
git commit -m "feat: add comic panel image generation"
```

---

### Task 5: Layout Composition

**Files:**
- Create: `app/services/layout_builder.py`
- Test: `tests/test_layout_builder.py`

**Interfaces:**
- Consumes: `list[ComicPanelOutline]`, `list[ComicPanelStory]`, `dict[int, str]` image paths.
- Produces: `build_comic_layout(outline, stories, image_paths) -> list[ComicPanelLayout]`.

- [ ] **Step 1: Write failing layout tests**

Assert that:
- unordered inputs produce panel layouts ordered 1–5;
- each title/scene/narration/dialogue/image is paired by `panel_number`, not list position;
- missing story content raises `LayoutBuildError`;
- a provided placeholder image path is treated like a valid image path and preserves five panels.

- [ ] **Step 2: Run layout tests and verify failure**

Run: `pytest tests/test_layout_builder.py -v`

Expected: FAIL because the layout builder does not exist.

- [ ] **Step 3: Implement deterministic merge**

Define:
- `class LayoutBuildError(RuntimeError)`;
- `build_comic_layout(outline: list[ComicPanelOutline], stories: list[ComicPanelStory], image_paths: dict[int, str]) -> list[ComicPanelLayout]`.

Require complete outline/story panel sets `{1,2,3,4,5}` and merge strictly by panel number.

- [ ] **Step 4: Run layout tests and verify success**

Run: `pytest tests/test_layout_builder.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/layout_builder.py tests/test_layout_builder.py
git commit -m "feat: add comic layout composition"
```

---

### Task 6: PDF Export

**Files:**
- Create: `app/services/exporters.py`
- Create: `static/exports/.gitkeep`
- Test: `tests/test_exporter.py`

**Interfaces:**
- Consumes: `list[ComicPanelLayout]`, optional title/metadata.
- Produces: `save_pdf(layout: list[ComicPanelLayout], title: str) -> str` returning `/static/exports/...pdf`.

- [ ] **Step 1: Write failing exporter tests**

Assert that:
- a five-panel layout creates a non-empty PDF beneath the configured exports directory;
- output filenames are UUID/timestamp-based and not user-path-derived;
- a missing/unreadable panel image is handled with the placeholder image where possible;
- an unrecoverable PDF writer failure raises `PdfExportError` for the pipeline to downgrade to a warning.

- [ ] **Step 2: Run exporter tests and verify failure**

Run: `pytest tests/test_exporter.py -v`

Expected: FAIL because the exporter does not exist.

- [ ] **Step 3: Implement PDF export**

Define:
- `class PdfExportError(RuntimeError)`;
- `save_pdf(layout: list[ComicPanelLayout], title: str) -> str` using FPDF2;
- one readable panel per page, preserving image aspect ratio and margins;
- title, narration, and optional dialogue on each panel page;
- safe generated filename under `static/exports/`.

- [ ] **Step 4: Run exporter tests and verify success**

Run: `pytest tests/test_exporter.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/exporters.py static/exports/.gitkeep tests/test_exporter.py
git commit -m "feat: add comic PDF export"
```

---

### Task 7: Shared Comic Generation Pipeline

**Files:**
- Create: `app/services/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `PromptRequest` and the services from Tasks 2–6.
- Produces: `generate_comic(request: PromptRequest) -> ComicGenerationResult`.

- [ ] **Step 1: Write failing orchestration tests**

Using monkeypatched service functions, assert that:
- the pipeline calls outline → story → five image generations → layout → PDF in that logical order;
- exactly five image calls occur for a successful outline;
- one image failure represented by the image service placeholder still produces five final panels;
- `PdfExportError` returns a `ComicGenerationResult` with `pdf_path=None` and a nonempty `export_warning` while keeping all panels;
- outline/story/layout failures propagate as generation failures rather than producing partial text layouts.

- [ ] **Step 2: Run pipeline tests and verify failure**

Run: `pytest tests/test_pipeline.py -v`

Expected: FAIL because the shared pipeline does not exist.

- [ ] **Step 3: Implement shared orchestration**

Define `generate_comic(request: PromptRequest) -> ComicGenerationResult` in `app/services/pipeline.py`. Keep browser-specific concerns out of this function. Catch only `PdfExportError` as a nonfatal export warning; let other generation errors bubble to route-level user handling.

- [ ] **Step 4: Run pipeline tests and verify success**

Run: `pytest tests/test_pipeline.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/pipeline.py tests/test_pipeline.py
git commit -m "feat: add shared comic generation pipeline"
```

---

### Task 8: FastAPI Application and Routes

**Files:**
- Create: `app/main.py`
- Create: `app/routes.py`
- Create: `tests/conftest.py`
- Create: `tests/test_routes.py`

**Interfaces:**
- Consumes: `PromptRequest`, `generate_comic()`.
- Produces: GET `/`, POST `/generate`, POST `/generate-comic/json`, GET `/export-success`, POST `/test-image`, GET `/health`.

- [ ] **Step 1: Write failing route tests**

Add tests asserting:
- `GET /health` returns `200` and `{"status":"healthy"}`;
- `GET /` returns `200`;
- `POST /generate` with blank required input returns a user-facing validation response without calling the generation pipeline;
- `POST /generate-comic/json` with a valid body returns five panel objects and the PDF/export fields from a mocked pipeline;
- generation exceptions return safe messages without leaking stack traces/API keys;
- `/test-image` returns 404 or disabled behavior when `enable_test_image` is false.

- [ ] **Step 2: Run route tests and verify failure**

Run: `pytest tests/test_routes.py -v`

Expected: FAIL because the app and routes do not exist.

- [ ] **Step 3: Implement app factory behavior and endpoints**

In `app/main.py`:
- create the FastAPI app;
- mount `/static`;
- include the router;
- ensure configured output directories exist.

In `app/routes.py`:
- configure `Jinja2Templates(directory="templates")`;
- implement all six specified routes;
- convert form values into `PromptRequest` before generation;
- serialize `ComicGenerationResult` for the JSON endpoint;
- handle known generation errors with safe frontend/API responses;
- gate `/test-image` behind `enable_test_image`.

- [ ] **Step 4: Run route tests and verify success**

Run: `pytest tests/test_routes.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/routes.py tests/conftest.py tests/test_routes.py
git commit -m "feat: add ComicCraft FastAPI routes"
```

---

### Task 9: Comic-Themed Frontend

**Files:**
- Create: `templates/index.html`
- Create: `templates/comic_preview.html`
- Create: `templates/export_success.html`
- Create: `templates/error.html`
- Create: `static/css/style.css`
- Modify: `tests/test_routes.py`

**Interfaces:**
- Consumes: template context from Task 8.
- Produces: usable browser UI for input, preview, errors, and export state.

- [ ] **Step 1: Extend route tests with frontend assertions**

Assert that:
- the homepage includes inputs named `story_prompt`, `character_name`, `setting`, `tone`, and `art_style`;
- the homepage includes a loading overlay element and “Generate My Comic” CTA;
- a mocked successful `/generate` response contains all five panel titles and an image element for every panel;
- when `pdf_path` is present, preview contains a download link;
- when `export_warning` is present, preview shows the warning and no broken PDF link.

- [ ] **Step 2: Run the frontend route tests and verify failure**

Run: `pytest tests/test_routes.py -v`

Expected: FAIL because templates/CSS are missing.

- [ ] **Step 3: Build templates and responsive styling**

Implement the four templates and `static/css/style.css` according to the spec's visual language: off-white paper background, bold comic headings, thick panel borders, subtle shadows, speech-bubble dialogue blocks, responsive single-column mobile layout, and a form loading overlay driven by minimal inline/vanilla JavaScript.

Use Jinja autoescaping and never render secrets or raw exception traces.

- [ ] **Step 4: Run frontend route tests and verify success**

Run: `pytest tests/test_routes.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates static/css/style.css tests/test_routes.py
git commit -m "feat: add ComicCraft web interface"
```

---

### Task 10: README, Local Setup, and End-to-End Verification

**Files:**
- Create: `README.md`
- Modify: any earlier file only if verification exposes a defect.

**Interfaces:**
- Consumes: completed application.
- Produces: documented local install/run/test procedure and verified MVP.

- [ ] **Step 1: Write README setup and usage instructions**

Document:
- Python 3.11+ requirement;
- virtual environment creation/activation;
- `pip install -r requirements.txt`;
- copying `.env.example` to `.env` and setting `GEMINI_API_KEY`;
- GPU/CPU device notes;
- `uvicorn app.main:app --reload`;
- browser URL `http://127.0.0.1:8000` and API docs URL `/docs`;
- `pytest -v`;
- generated file locations and placeholder behavior;
- the exact manual acceptance prompt from the design spec.

- [ ] **Step 2: Run the complete automated suite**

Run: `pytest -v`

Expected: all tests PASS.

- [ ] **Step 3: Verify application imports and route registration**

Run: `python -c "from app.main import app; print(sorted({r.path for r in app.routes}))"`

Expected: output includes `/`, `/generate`, `/generate-comic/json`, `/export-success`, `/test-image`, `/health`, `/docs`, and static/OpenAPI routes.

- [ ] **Step 4: Run a no-network smoke test with mocked AI/image services**

Use the TestClient test suite or a short local test harness to submit the acceptance input:
- Story: `A brave fox exploring an enchanted forest.`
- Character: `Fenn`
- Setting: `Enchanted Forest`
- Tone: `Adventure`
- Art Style: `Comic Book`

Expected: exactly five ordered panels render, placeholder/mocked images are accepted, and PDF output or export-warning behavior matches the injected exporter result.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add ComicCraft setup and verification guide"
```

---

## Final Verification Gate

Before declaring the project complete:

- [ ] Run `pytest -v` and confirm zero failures.
- [ ] Confirm no `.env` or API key is tracked by Git.
- [ ] Confirm generated files are excluded from Git except `.gitkeep` and the placeholder image.
- [ ] Confirm both browser and JSON paths call the shared pipeline.
- [ ] Confirm malformed AI JSON, blank input, one failed image, missing panel data, and failed PDF export all have automated coverage.
- [ ] Confirm the local app starts with `uvicorn app.main:app --reload` once dependencies are installed.
- [ ] Perform the manual five-panel acceptance test with real Gemini credentials when available; if no credential is available, record that automated/mock verification passed and leave the real-network check explicitly unverified.
