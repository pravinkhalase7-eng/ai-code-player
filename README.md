# AI Coding Tutor

A personal AI teacher that sits next to the student and teaches programming visually.

Ask:

> Explain Java for loop

The platform generates a structured lesson, types the code in a VS Code-style editor, compiles it in an isolated sandbox, animates every iteration, narrates with Kokoro, then quizzes the student.

This is not a chatbot. It is **AI Tutor + VS Code + Code Runner + Interactive Animation**.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind, Monaco, Framer Motion |
| Video | Remotion (`16:9` and `9:16`) |
| API | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Agents | Google Gemini via Google ADK + structured JSON |
| Jobs | Celery + Redis |
| Database | PostgreSQL |
| Voice | Kokoro TTS, Gemini TTS fallback, browser TTS |
| Execution | Isolated `code-runner` container (Java, Python, JavaScript) |

## Architecture

```
                     NGINX
                       |
          ┌────────────┴────────────┐
          │                         │
       Next.js                   FastAPI
                                     |
                     ┌───────────────┼───────────────┐
                     |               |               |
                   Redis          PostgreSQL       Kokoro
                     |
                   Workers
                     |
              ┌──────┴──────┐
              │             │
          Code Runner   Remotion
```

Gemini creates lesson instructions. Deterministic backend services execute code, cache audio, and store real stdout. The model is never allowed to invent terminal output.

## Project layout

```
backend/app/                 FastAPI, ADK agents, lesson pipeline
backend/alembic/             Database migrations
services/code-runner/       Isolated compile/execute sandbox
frontend/app/               Next.js dashboard + /learn/[lessonId]
frontend/components/        Player, Monaco workbench, tutor avatar
frontend/remotion/          Lesson video renderer
deploy/nginx.conf           Optional reverse proxy
```

## Local development

### 1. Environment

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Set `GEMINI_API_KEY` in `.env`. Copy the same file to `backend/.env` or export the variables.

`GEMINI_MODEL` can be changed without code changes, for example:

```bash
GEMINI_MODEL=gemini-3.6-flash
```

### 2. Docker Compose (recommended)

This starts Postgres, Redis, FastAPI, the worker, Next.js, Kokoro, and the sandbox:

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000).

API docs: [http://localhost:8000/docs](http://localhost:8000/docs).

Kokoro is optional for the first run. If it is slow to pull, set `TTS_PROVIDER=browser` in `.env` so the interactive lesson still works.

### 3. Manual services

Postgres and Redis should be running, then:

```bash
# sandbox
cd services/code-runner
python3 -m pip install -r requirements.txt
python3 -m uvicorn app:app --port 8090

# API
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env .env
uvicorn app.main:app --reload --port 8000

# worker (optional if Redis is up)
celery -A app.workers.celery_app.celery_app worker --loglevel=info

# frontend
cd frontend
npm install
npm run dev
```

Without Redis, the API still queues lesson generation on a background thread. It still never executes student code inside the API process; it always calls `CODE_RUNNER_URL`.

### 4. Database migrations

`init_db()` creates tables on API startup. To use Alembic explicitly:

```bash
cd backend
alembic upgrade head
```

## MVP lesson flow

1. Student enters **Explain Java for loop**.
2. Tutor Agent infers language and level.
3. Lesson Planner returns a Pydantic-validated scene list.
4. Code Agent supplies `Main.java`.
5. Execution Agent sends the program to the sandbox (`javac` then `java`).
6. Real stdout is stored. Gemini does not invent it.
7. Visualizer builds `i = 0 … i = 5 / 5 < 5 → FALSE`.
8. Kokoro (or fallback TTS) narrates each scene. Identical text is cached by `sha256(text+voice+speed+provider)`.
9. The interactive player at `/learn/[lessonId]` plays, highlights, quizzes, and accepts follow-up chat.
10. Optional Remotion render exports MP4.

## Code execution security

The `code-runner` service:

- runs as a non-root user
- uses a temporary filesystem that is destroyed after the run
- applies CPU, memory, process, output-size, and timeout limits
- does not receive Postgres credentials or application secrets
- does not mount the host project
- treats AI-generated code as untrusted input

Infinite loops are killed by `CODE_EXECUTION_TIMEOUT` (default 5 seconds). The tutor then explains why removing `i++` never ends.

## Tests

```bash
cd backend
pytest
```

Coverage includes lesson schema validation, Gemini JSON parsing, Java stdout, compile errors, timeout/infinite loops, quiz scoring, TTS cache keys, progress, and API endpoints.

Java tests skip if `javac` is not installed.

## Remotion

```bash
cd frontend
npm run remotion     # studio
npm run render       # MP4
```

Aspect ratio is configurable (`16:9` → 1920×1080, `9:16` → 1080×1920).

`POST /api/v1/lesson/{id}/render` enqueues a render job. The interactive lesson is kept even if video export fails.

## Production

1. Fill `.env` with real `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, and `KOKORO_URL`.
2. `docker compose up --build -d`
3. Optional: `docker compose --profile proxy up -d nginx` and terminate TLS in front of port `8080`.
4. Optional GPU Kokoro: replace the CPU image with `ghcr.io/remsky/kokoro-fastapi-gpu`.
5. Run `alembic upgrade head` against production Postgres.
6. Put object storage in front of `STORAGE_PATH` later; the local provider is the default.

Do not commit `.env`.

## Phase map

- **Phase 1 (this MVP):** Java for-loop, Gemini structured lessons, Monaco player, Java sandbox, terminal, highlighting, Kokoro/fallback TTS, quizzes.
- **Phase 2:** Python, JavaScript, adaptive chat, richer avatar, Remotion export.
- **Phase 3:** more languages, Three.js character, curriculum analytics, voice input.
# ai-code-player
