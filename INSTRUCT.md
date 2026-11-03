# Ojas — AI Agent Instruct File

> **Purpose:** This file gives any AI coding assistant instant full context about
> the Ojas project — what it is, what has been built, how it is structured, and
> exactly what to do next. Read this before touching any code.

---

## 1. What Is Ojas?

**Ojas** is a fully **offline**, browser-based AI software development assistant.

- The user uploads requirement documents (PDF / DOCX / TXT).
- A **Development Agent** reads the documents, generates a development plan, and writes Python source files.
- A **Testing Agent** runs pytest, parses failures, writes structured bug reports, and feeds them back to the Development Agent for fixing.
- The cycle repeats (up to 5 iterations) until all tests pass or a stop rule triggers.
- **Nothing leaves the machine.** No cloud APIs, no telemetry.

| Item | Detail |
|---|---|
| Team | 4 members |
| Schedule | 22 Oct – 30 Nov 2026 (40 days) |
| Target OS | Windows (CPU-only) |
| LLM | GGUF model via llama-cpp-python |
| UI | React + TypeScript + Monaco Editor |
| Backend | Python + FastAPI |

---

## 2. Project Location & Layout

**Root:** `c:\Users\Asus\Desktop\Ojas\`

```
Ojas/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry point (Phase 5 ✅)
│   │   ├── config.py            ← Pydantic settings loader (Phase 2 ✅)
│   │   ├── api/
│   │   │   └── health.py        ← GET /api/health (Phase 5 ✅)
│   │   ├── schemas/
│   │   │   └── common.py        ← ErrorResponse, SuccessResponse (Phase 5 ✅)
│   │   ├── storage/
│   │   │   └── db.py            ← SQLite init + helpers (Phase 3 ✅)
│   │   ├── llm/
│   │   │   ├── client.py        ← Abstract LLMClient (Phase 4 ✅)
│   │   │   └── llama_cpp_client.py  ← llama.cpp implementation (Phase 4 ✅)
│   │   ├── agents/              ← Empty placeholders (Phases 16–18)
│   │   ├── events/              ← Empty placeholder (Phase 12)
│   │   ├── rag/                 ← Empty placeholder (Phases 13–15)
│   │   ├── tasks/               ← Empty placeholder (Phase 12)
│   │   └── validation/          ← Empty placeholder (Phases 16, 18)
│   └── tests/
│       ├── test_config.py       ← 3 config tests (Phase 2 ✅)
│       └── test_health.py       ← 11 health tests (Phase 5 ✅)
├── frontend/                    ← Only .gitkeep — NOT scaffolded yet (Phase 6)
├── models/
│   └── ojas.gguf                ← 1.8 GB GGUF model (present ✅)
├── data/
│   └── ojas.db                  ← SQLite database (created on startup ✅)
├── config/
│   └── settings.json            ← All 13 runtime settings (Phase 2 ✅)
├── runtime/
│   └── venv/                    ← Python 3.14 virtual environment
├── docs/                        ← All 9 design documents (fully written)
├── workspace/                   ← Generated project files live here (runtime)
├── logs/                        ← ojas.log written here on startup
├── reports/                     ← Markdown reports written here
├── requirements.txt             ← Pinned Python deps (updated Phase 4)
└── start.bat                    ← Empty placeholder (Phase 19)
```

---

## 3. Implementation Status & Schedule

> **Project Start:** 25 Oct 2026 | **Project Deadline:** 25 Nov 2026 | **Total Duration:** 32 days

| Phase | Name | Deadline | Duration | Status | Key files |
|---|---|---|---|---|---|
| 1 | Folder Structure & Boilerplate | 25 Oct 2026 | 1 day | ✅ Done | All dirs, `__init__.py`, `.gitignore`, `README.md` |
| 2 | Configuration System | 26 Oct 2026 | 1 day | ✅ Done | `config.py`, `config/settings.json` |
| 3 | Database Initialization | 27 Oct 2026 | 1 day | ✅ Done | `storage/db.py` — 12 tables, FTS5, triggers |
| 4 | LLM Client | 29 Oct 2026 | 2 days | ✅ Done | `llm/client.py`, `llm/llama_cpp_client.py` |
| 5 | Health Endpoint & FastAPI App | 30 Oct 2026 | 1 day | ✅ Done | `main.py`, `api/health.py`, `schemas/common.py` |
| 6 | Frontend Scaffold | 01 Nov 2026 | 2 days | 🔲 **NEXT** | `frontend/` — Vite + React + TS |
| 7 | UI Shell & Navigation | 03 Nov 2026 | 2 days | 🔲 Pending | AppShell, 4 pages, routing |
| 8 | Project CRUD | 05 Nov 2026 | 2 days | 🔲 Pending | Projects API + UI |
| 9 | File Management API | 06 Nov 2026 | 1 day | 🔲 Pending | Workspace file CRUD |
| 10 | Workspace Layout & Editor | 08 Nov 2026 | 2 days | 🔲 Pending | Monaco editor, 4-panel layout |
| 11 | Settings API & Page | 09 Nov 2026 | 1 day | 🔲 Pending | Settings endpoint + form |
| 12 | Task Manager & Event Bus | 10 Nov 2026 | 1 day | 🔲 Pending | ThreadPool, SSE |
| 13 | Document Upload & Parsing | 12 Nov 2026 | 2 days | 🔲 Pending | PDF/DOCX/TXT parsing |
| 14 | Chunking, Embedding & Indexing | 14 Nov 2026 | 2 days | 🔲 Pending | REQ-IDs, Chroma, FTS5 |
| 15 | RAG Search Engine | 15 Nov 2026 | 1 day | 🔲 Pending | Hybrid search + RRF fusion |
| 16 | Development Agent & Code Gen | 17 Nov 2026 | 2 days | 🔲 Pending | DevelopmentAgent, static checks |
| 17 | Orchestrator, Runs API & Run Panel | 19 Nov 2026 | 2 days | 🔲 Pending | Full plan→develop flow + SSE |
| 18 | Testing Agent, Bug Reports & Fix Loop | 21 Nov 2026 | 2 days | 🔲 Pending | TestingAgent, fix loop |
| 19 | Traceability, Reports & UI Polish | 23 Nov 2026 | 2 days | 🔲 Pending | Reports page, streaming |
| 20 | Integration Testing & Final QA | 25 Nov 2026 | 2 days | 🔲 Pending | 3 sample projects, metrics |

**Overall progress: 5 / 20 phases complete (25% done) — Currently 4 days behind schedule (actual completion of Phase 5: 3 Nov)**

---

## 4. How to Run the Project

### Start the backend
```bat
cd c:\Users\Asus\Desktop\Ojas
runtime\venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000
```
- Health check: `http://127.0.0.1:8000/api/health`
- Swagger docs: `http://127.0.0.1:8000/docs`

### Run tests
```bat
cd c:\Users\Asus\Desktop\Ojas
runtime\venv\Scripts\pytest.exe backend/tests/ -v
```
Current result: **14 passed** (3 config + 11 health tests)

### Python interpreter
Always use the venv interpreter — **not** the system Python:
```
c:\Users\Asus\Desktop\Ojas\runtime\venv\Scripts\python.exe
```

> **Important:** Python 3.14 is being used. `llama-cpp-python` was installed via
> the pre-built CPU wheel from `abetlen.github.io` because no MSVC compiler is
> available (building from source fails). Always use `--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu` when installing it.

---

## 5. Key Technical Decisions & Conventions

### Backend conventions
| Rule | Detail |
|---|---|
| **All paths are relative to project root** | `_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent` (from `backend/app/…`) |
| **Settings are a singleton** | Always use `from backend.app.config import get_settings` — never instantiate `OjasSettings` directly |
| **DB helpers** | Use `fetch_one()`, `fetch_all()`, `execute_query()` from `storage/db.py` — never open raw connections in application code |
| **LLM access** | Use `get_llm_client()` from `backend.app.main` — returns the global singleton or `None` |
| **Mock path for LLM** | When testing, patch `backend.app.llm.llama_cpp_client.get_settings`, NOT `backend.app.config.get_settings` |
| **Timestamps** | Always ISO 8601 UTC strings: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")` |
| **UUIDs** | Use `str(uuid.uuid4())` for all primary keys |
| **Error response** | Use `ErrorResponse` from `schemas/common.py` in all exception handlers |
| **Logging** | Use `logging.getLogger(__name__)` — never `print()` in backend code |

### Database conventions
| Rule | Detail |
|---|---|
| **12 tables** | `projects`, `documents`, `chunks`, `chunks_fts` (FTS5), `code_chunks`, `runs`, `run_steps`, `test_cases`, `test_results`, `bug_reports`, `traceability_links`, `settings` |
| **FTS5 sync** | Three triggers (`chunks_ai`, `chunks_ad`, `chunks_au`) keep `chunks_fts` in sync automatically |
| **ON DELETE CASCADE** | All foreign keys use CASCADE — deleting a project cascades to all child records |
| **WAL mode** | Always set on every connection — already done in `get_connection()` |

### Model conventions
| Rule | Detail |
|---|---|
| **Model file** | `models/ojas.gguf` (1.8 GB, present) |
| **Settings key** | `model_path = "models/ojas.gguf"` in `config/settings.json` |
| **Thread safety** | `LlamaCppClient` uses a `threading.Lock()` — one inference at a time |
| **Graceful degradation** | If model not loaded, `is_loaded()` returns `False`; backend still starts |

---

## 6. Installed Python Packages (as of Phase 5)

```
fastapi==0.162.0        uvicorn==0.54.0         httpx==0.28.1
starlette==1.10.0       python-multipart==0.0.33
pydantic==2.14.1        pydantic-settings==2.16.1
llama-cpp-python==0.3.36  numpy==2.5.4
jinja2==3.1.6           diskcache==5.6.3
pytest==9.1.1           python-dotenv==1.2.4
anyio==4.16.0           h11==0.16.0
```

**Still to install (needed for Phase 6+):**
```
fastembed    chromadb    python-docx    pypdf    chardet    ruff
```

---

## 7. Reference Documents

All design docs are in `docs/`. Read these before implementing later phases:

| File | Content |
|---|---|
| `01_Project_Requirement_Documentation.md` | Full SRS — what the system must do |
| `02_System_Architecture.md` | Component diagram, data flow |
| `03_UI_Design.md` | All UI wireframes, theme tokens, panel layout |
| `04_Technology_Stack.md` | Every library choice with rationale |
| `05_Database_Schema.md` | All 12 table definitions with exact SQL |
| `06_API_Specification.md` | All API endpoints with request/response shapes |
| `07_Development_Plan.md` | Sprint plan and team responsibilities |
| `08_Setup_Guide.md` | Step-by-step machine setup instructions |
| `09_Implementation_Plan.md` | **Primary reference** — 20 micro-phases with exact file lists and verification checklists |

---

## 8. What To Do Next (Phase 6)

**Goal:** Scaffold the React + TypeScript frontend with Vite.

### Steps
1. Run `npm create vite@latest frontend -- --template react-ts` in project root
2. `cd frontend && npm install`
3. Install UI deps: `react-router-dom @tanstack/react-query zustand tailwindcss lucide-react react-resizable-panels react-markdown remark-gfm monaco-editor @monaco-editor/react`
4. Configure `vite.config.ts` — proxy `/api` → `http://127.0.0.1:8000`
5. Set up Tailwind CSS
6. Create `frontend/src/api/client.ts` (base fetch wrapper)
7. Create `frontend/src/api/types.ts` (TypeScript types mirroring Pydantic schemas)
8. Create `frontend/src/monaco/loader.ts` (offline Monaco loader, no CDN)

### Verification
- `cd frontend && npm run dev` → Vite dev server on `http://localhost:5173`
- `fetch('/api/health')` from browser console → returns backend health JSON
- `npm run build` → no TypeScript errors
- Monaco editor loads with no CDN network requests

---

## 9. Quirks & Known Issues

| Issue | Detail |
|---|---|
| **Python 3.14** | Newer than typical. Most pre-built wheels exist for 3.10–3.12. Always check compatibility before `pip install`. |
| **No MSVC compiler** | Cannot build C/C++ extensions from source. Use `--prefer-binary` and/or `--extra-index-url` for native packages. |
| **PowerShell `&&`** | PowerShell does not support `&&` as command chaining. Use `;` or separate commands. |
| **`run_command` sandbox** | Python/pip cannot run inside the sandbox (access denied). Use `BypassSandbox: true` for all Python/pip/npm invocations. |
| **Mock path for LLM** | Must patch `backend.app.llm.llama_cpp_client.get_settings` not `backend.app.config.get_settings` |
| **`lru_cache` on `get_settings`** | Cache persists across test runs in same process. Use `get_settings.cache_clear()` in tests that change settings. |
| **Deprecation warning** | `starlette.testclient` with `httpx` shows a deprecation warning. Non-breaking — address in Phase 20 by switching to `httpx2`. |

