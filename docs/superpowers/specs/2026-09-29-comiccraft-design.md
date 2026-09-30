# ComicCraft — AI Comic Story Creator

## 1. Project Goal
ComicCraft is a web application that converts a user's creative prompt into a complete 5-panel comic. The user supplies a story idea, character name, setting, tone, and art style. The system generates a structured comic outline, narration/dialogue, an illustration for each panel, an on-screen preview, and a downloadable PDF.

## 2. Success Criteria
The MVP is successful when a user can:
1. Open the web interface locally.
2. Enter story details through a form.
3. Generate a coherent 5-panel comic.
4. See a title, scene image, and narration/dialogue for each panel.
5. Download the completed comic as a PDF.
6. Create another comic without restarting the server.
7. Receive understandable error messages if an AI/API step fails.

## 3. Technology Stack
- Backend: Python 3.11+, FastAPI
- Server: Uvicorn
- Frontend: HTML5, CSS3, Jinja2
- Text generation: Google Gemini API
- Image generation: Hugging Face Diffusers with Stable Diffusion v1.5
- PDF generation: FPDF2
- Image handling: Pillow
- Validation: Pydantic
- Configuration/secrets: python-dotenv
- Testing: pytest + FastAPI TestClient

## 4. High-Level Architecture

User Browser
   |
   v
FastAPI Routes
   |
   +--> Input Validation
   |
   +--> Gemini Outline Service
   |       |
   |       v
   |   5-panel outline
   |
   +--> Gemini Story Service
   |       |
   |       v
   |   narration/dialogue
   |
   +--> Image Generator
   |       |
   |       v
   |   panel images
   |
   +--> Layout Builder
   |       |
   |       v
   |   normalized panel layout
   |
   +--> PDF Exporter
           |
           v
      downloadable PDF

The frontend consumes the final layout through Jinja2 templates and renders each panel in sequence.

## 5. User Inputs
The main form collects:
- Story prompt — required text
- Main character name — required text
- Setting — required text
- Tone — selectable or free text
- Art style — selectable or free text

Validation rules:
- Empty required values are rejected.
- Text lengths are bounded to avoid oversized prompts.
- Inputs are normalized and escaped before display.

## 6. Core Data Model

### PromptRequest
Fields:
- story_prompt: str
- character_name: str
- setting: str
- tone: str
- art_style: str

### ComicPanelOutline
Fields:
- panel_number: int
- title: str
- scene_description: str
- image_prompt: str

### ComicPanelLayout
Fields:
- panel_number: int
- title: str
- scene_description: str
- narration: str
- dialogue: str | optional
- image_path: str

### ComicGenerationResult
Fields:
- panels: list[ComicPanelLayout]
- pdf_path: str
- generated_at: datetime

## 7. AI Generation Pipeline

### Step 1 — Outline Generation
Module: `app/services/gemini_flash.py`
Function: `generate_outline(request: PromptRequest)`

Responsibilities:
- Build a structured prompt from the user's values.
- Request exactly five panels.
- Require machine-readable JSON where possible.
- Validate panel count and mandatory keys.
- Fall back to safe parsing if the model wraps JSON in Markdown.

Output: five ComicPanelOutline objects.

### Step 2 — Story Generation
Module: `app/services/gemini_pro.py`
Function: `generate_story(outline, request)`

Responsibilities:
- Expand the outline into narration/dialogue.
- Preserve panel ordering.
- Keep the named main character consistent.
- Match the requested tone.
- Avoid changing scene meaning from the outline.

Output: structured text per panel rather than one unstructured block.

### Step 3 — Illustration Generation
Module: `app/services/image_generator.py`
Function: `generate_image(prompt, panel_number, art_style)`

Responsibilities:
- Load the Stable Diffusion pipeline lazily.
- Generate one image per panel.
- Save images under `static/panels/`.
- Use collision-safe filenames.
- Return a browser-safe static path.
- Use a local placeholder image when image generation fails, while preserving the rest of the comic.

Performance design:
- Model initializes once and is reused.
- CPU fallback is supported, but GPU is preferred.
- Image dimensions are kept moderate for a student project and reasonable export size.

## 8. Layout Builder
Module: `app/services/layout_builder.py`
Function: `build_comic_layout()`

Responsibilities:
- Merge outline, story, and image results by panel number.
- Guarantee stable 1–5 ordering.
- Prevent missing-panel indexing errors.
- Return template-ready dictionaries/models.

## 9. PDF Export
Module: `app/services/exporters.py`
Function: `save_pdf(layout, metadata)`

Responsibilities:
- Create a title page/heading.
- Add one panel per page for readability.
- Add panel title, image, narration, and dialogue.
- Preserve margins and aspect ratio.
- Save under `static/exports/`.
- Use a unique timestamp/UUID filename.

## 10. FastAPI Routes
Module: `app/routes.py`

### GET `/`
Renders `index.html`.

### POST `/generate`
Browser-form workflow:
1. Validate form fields.
2. Generate outline.
3. Generate story.
4. Generate five images.
5. Build layout.
6. Save PDF.
7. Render `comic_preview.html`.

### POST `/generate-comic/json`
API workflow:
- Accept PromptRequest JSON.
- Run the same service pipeline.
- Return panel metadata and PDF path as JSON.

### GET `/export-success`
Renders a simple confirmation page.

### POST `/test-image`
Developer-only utility for testing image generation.

### GET `/health`
Returns simple application health status for testing/debugging.

## 11. Frontend Design

### `index.html`
- Comic-themed hero section.
- Clear input form.
- Select controls for tone and art style.
- Large “Generate My Comic” CTA.
- Loading overlay while the request is processing.
- Responsive layout for desktop/mobile.

### `comic_preview.html`
- Comic title and summary header.
- 5 visually separated panel cards.
- Image, panel title, narration, and dialogue.
- Download PDF button.
- “Create Another Comic” button.

### `export_success.html`
- Confirmation message.
- Link back to home.

### Visual Language
- Off-white paper background.
- Bold comic-style headings using system-safe fonts.
- Thick borders and subtle shadows.
- Speech-bubble style dialogue blocks.
- Responsive single-column mobile layout.

## 12. Project Structure

```
ComicCraft/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── schemas.py
│   ├── config.py
│   └── services/
│       ├── __init__.py
│       ├── gemini_flash.py
│       ├── gemini_pro.py
│       ├── image_generator.py
│       ├── layout_builder.py
│       └── exporters.py
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
├── static/
│   ├── css/style.css
│   ├── panels/
│   └── exports/
├── tests/
│   ├── test_routes.py
│   ├── test_layout_builder.py
│   └── test_exporter.py
├── docs/superpowers/specs/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 13. Configuration
Environment variables:
- `GEMINI_API_KEY`
- `GEMINI_OUTLINE_MODEL` (default configurable)
- `GEMINI_STORY_MODEL` (default configurable)
- `IMAGE_MODEL_ID` (default `runwayml/stable-diffusion-v1-5`)
- `DEVICE` (`cuda`, `mps`, or `cpu`)

No API keys will be hard-coded.

## 14. Error Handling
- Invalid form input: show user-friendly validation message.
- Gemini API error: show generation failure message, log technical details.
- Invalid AI JSON: retry parsing once; fail clearly if unusable.
- Image generation failure: use placeholder panel rather than failing entire comic.
- PDF failure: keep preview available and show export warning.
- Unexpected server errors: FastAPI exception handler with safe frontend message.

## 15. Security and Reliability
- Never expose API keys in templates or responses.
- Escape user-generated content in templates.
- Restrict output filenames to generated identifiers.
- Avoid accepting arbitrary file paths from user input.
- Keep developer utility endpoints easy to disable for production.

## 16. Testing Strategy

### Unit tests
- Prompt schema validation.
- Layout ordering and merge logic.
- PDF generation with mocked image paths.
- AI response parsing using mocked responses.

### Route tests
- GET `/` returns 200.
- POST `/generate` validates missing inputs.
- POST `/generate-comic/json` accepts valid payload.
- GET `/health` returns healthy status.

### Manual acceptance test
Use prompt:
“A brave fox exploring an enchanted forest.”
Character: “Fenn”
Setting: “Enchanted Forest”
Tone: “Adventure”
Art Style: “Comic Book”

Expected result:
- Exactly five panels.
- Coherent story progression.
- Five panel image files or graceful placeholders.
- Preview page renders all panels.
- PDF file is created and downloadable.

## 17. MVP Scope Boundaries
Included:
- Single-user local web app
- Five-panel comics
- One generated image per panel
- PDF export
- Browser form + JSON API

Not included in MVP:
- User accounts
- Cloud database
- Payments
- Comic editing canvas
- Multi-language UI
- Cloud deployment
- Persistent comic gallery

These can be added later without changing the core pipeline.

## 18. Future Scope
- User login and saved comics
- Regenerate only one panel
- Editable captions/dialogue
- More art models/styles
- Multi-language generation
- Cloud deployment
- Shareable comic links
- Speech/audio narration
- Variable panel counts

## 19. Final Design Decision
Build the project as a modular FastAPI application with clean separation between routing, AI generation, image generation, layout composition, and PDF export. Preserve the workflow described in the source document while improving maintainability, validation, resilience, and UI quality.
