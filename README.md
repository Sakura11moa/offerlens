# OfferLens MVP (V2 Skeleton)

OfferLens is an AI-powered job application efficiency tool.
Users input resume content and job description (JD), then get:
- match score
- strengths
- weaknesses
- missing keywords
- rewrite suggestions
- interview questions
- summary

This delivery is the first-round MVP skeleton for continuous development.

## Tech Stack

- Frontend: Vue 3, Vite, TypeScript, Element Plus, Axios
- Backend: FastAPI, Pydantic, Uvicorn, Python 3.11+
- Deployment: Docker, Docker Compose

## Project Structure

```text
offerlens/
  docker-compose.yml
  .env.example
  README.md
  backend/
    Dockerfile
    requirements.txt
    app/
      main.py
      schemas.py
      api/
        routes.py
      core/
        config.py
      services/
        analyzer_service.py
        llm_service.py
      prompts/
        resume_analysis_prompt.txt
  frontend/
    Dockerfile
    package.json
    vite.config.ts
    tsconfig.json
    index.html
    src/
      main.ts
      App.vue
      api/
        analyze.ts
      components/
        ResumeForm.vue
        AnalyzeResult.vue
      types/
        analyze.ts
      views/
        HomeView.vue
```

## Environment Variables

You can copy `.env.example` to `.env` in project root (optional, used for overrides):

```bash
cp .env.example .env
```

Variables:

- `APP_ENV`: runtime environment name
- `LLM_BASE_URL`: OpenAI-compatible provider base URL (example: `https://your-proxy.example.com/v1`)
- `LLM_API_KEY`: LLM API key
- `LLM_MODEL`: model name
- `LLM_TIMEOUT`: request timeout in seconds
- `VITE_API_BASE_URL`: frontend request base URL

Notes:
- If `LLM_API_KEY` or `LLM_BASE_URL` is missing, the project still starts.
- `POST /api/analyze` returns `503` with clear config error.
- Backend treats provider as OpenAI-compatible and calls `{LLM_BASE_URL}/chat/completions`.

## Backend API

Base prefix: `/api`

1) Health Check

- `GET /api/health`
- Response example:

```json
{
  "status": "ok",
  "llm_configured": false
}
```

2) Analyze

- `POST /api/analyze`
- Request:

```json
{
  "resume_text": "string",
  "job_description": "string"
}
```

- Response:

```json
{
  "score": 78,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_keywords": ["..."],
  "rewrite_suggestions": ["..."],
  "interview_questions": ["..."],
  "summary": "..."
}
```

Validation:
- non-empty and length checks via Pydantic
- unified error JSON format in backend

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open frontend: `http://localhost:5173`

## Docker Run

From project root:

```bash
docker compose up --build
```

Services:
- frontend: `http://localhost:5173`
- backend: `http://localhost:8000`

`.env` is optional for Docker startup because compose includes safe defaults.

## Enable Real LLM API Key

1. Edit `.env` in root.
2. Set:

```env
LLM_BASE_URL=https://your-openai-compatible-provider/v1
LLM_API_KEY=your_real_key
LLM_MODEL=your_model_name
LLM_TIMEOUT=30
```

3. Restart services:

```bash
docker compose up --build
```

## FAQ

1) Why does analyze return `LLM not configured`?
- `LLM_API_KEY` or `LLM_BASE_URL` is empty or not loaded.

2) Can I run without database?
- Yes. MVP has no database by design.

3) Does startup depend on real model availability?
- No. Startup is independent. Only analyze call needs model config.

4) Where is prompt managed?
- `backend/app/prompts/resume_analysis_prompt.txt`

5) Where to replace LLM vendor protocol?
- `backend/app/services/llm_service.py`
