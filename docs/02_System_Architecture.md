# Ojas: System Architecture

| Item | Detail |
|---|---|
| Related documents | 01_Project_Requirement_Documentation.md, 03_UI_Design.md, 04_Technology_Stack.md |
| Frontend | React.js with Monaco Editor |
| Backend | FastAPI (Python 3.10+) |
| Model | Local quantized GGUF LLM on CPU (default Qwen2.5-Coder-3B-Instruct, Q4_K_M) |

---

## 1. Architecture Overview

Ojas is a single-machine, offline web application. A React single-page app in the browser talks to a FastAPI backend over HTTP and Server-Sent Events. The backend runs an orchestrator that controls two agents. Both agents use one local LLM. Retrieval, static checks and test execution are plain Python.

### 1.1 Design principles

1. **Layering.** Each layer talks only to the layer below it.
2. **One shared model.** Loaded once at start-up; one generation at a time.
3. **Plain code wherever possible.** Parsing, search, syntax checks and tests are not done by the LLM.
4. **Deterministic verdicts.** Pass or fail comes from real pytest runs.
5. **Small prompts.** Retrieve only the needed chunks; generate one file at a time.
6. **Background tasks with progress.** The UI never waits on a blocking call.
7. **Configuration over code.** Model, paths, ports and limits live in config files.
8. **Fully local.** Loopback only, telemetry off, all assets bundled.

---

## 2. Layered Architecture

```
+--------------------------------------------------------------------+
| PRESENTATION   React SPA (Vite build)                              |
|   Monaco Editor | File tree | Run panel | Logs | Reports           |
+------------------------------+-------------------------------------+
                               | HTTP (JSON) + Server-Sent Events
+------------------------------v-------------------------------------+
| SERVICE        FastAPI + Uvicorn (127.0.0.1:8000)                  |
|   Routers | Pydantic schemas | Task manager | SSE stream | Static  |
+------------------------------+-------------------------------------+
| LOGIC          Orchestrator (Python state machine)                 |
|   Development Agent | Testing Agent | Fix-loop controller          |
+------------------+-----------+-------------------+-----------------+
| RETRIEVAL        | MODEL     | VALIDATION        | STORAGE         |
| Parser, chunker  | LLMClient | ast.parse, ruff   | SQLite          |
| fastembed, Chroma| llama.cpp | pytest (subprocess)| Chroma         |
| FTS5, RRF        | GGUF, CPU | sandbox folder    | workspace/ logs/|
+------------------+-----------+-------------------+-----------------+
| FOUNDATION     Python 3.10+, runtime/venv, start.bat               |
+--------------------------------------------------------------------+
```

| Layer | Responsibility |
|---|---|
| Presentation | Collect input, show code, progress, results and reports. No model code. |
| Service | Validate requests, expose REST and SSE, manage background tasks, serve the built frontend. |
| Logic | Choose the agent, build prompts, control the workflow and the fix loop. |
| Retrieval | Find the few relevant requirement and code chunks. |
| Model | Load the GGUF model once and expose a generate function. |
| Validation | Syntax and style checks, real test execution. |
| Storage | Records, vectors, workspace files, logs and reports. |
| Foundation | Interpreter, isolated packages, launcher. |

---

## 3. Components

### 3.1 Frontend (React SPA)

| Component | Role |
|---|---|
| App shell and router | Pages: Projects, Workspace, Reports, Settings |
| Monaco editor area | Edit workspace files, diff view for generated changes |
| File tree | Browse and manage workspace files |
| Documents panel | Upload documents, show indexed requirements (REQ-IDs) |
| Run panel | Prompt box, Start / Stop, run stage and iteration status |
| Bottom panel | Tabs: Logs, Test results, Bug reports, Model output |
| API client | Typed fetch wrappers and an SSE subscriber |
| State | Server state (queries) and a small UI store |

The frontend contains no business logic about agents. It only calls the API and renders events. Details are in `03_UI_Design.md`.

### 3.2 Backend (FastAPI)

| Module | Role |
|---|---|
| `main.py` | App creation, start-up (load config, model, DB), static file mounting |
| `api/` routers | `projects`, `documents`, `runs`, `files`, `tests`, `reports`, `settings`, `health` |
| `schemas/` | Pydantic request and response models |
| `tasks/` | Background task manager: queue, status, cancel, event publishing |
| `events/` | In-memory event bus feeding the SSE endpoint |
| `orchestrator.py` | Workflow control and fix loop |
| `agents/` | `development_agent.py`, `testing_agent.py`, prompt templates |
| `llm/` | `LLMClient` interface and llama.cpp implementation |
| `rag/` | `parser.py`, `chunker.py`, `embedder.py`, `index.py`, `search.py` |
| `validation/` | `static_check.py` (ast, ruff), `test_runner.py` (pytest) |
| `storage/` | SQLite access, workspace file service, report writer |
| `config/` | Settings loader |

### 3.3 Orchestrator
A plain Python state machine, not a framework. It:
- selects the agent for a task,
- decides whether retrieval is needed,
- runs the develop, test, fix and re-test loop,
- applies the stop rules,
- publishes progress events,
- records every step in the run history.

### 3.4 Development Agent
Builds prompts and handles output for construction tasks: requirement analysis, architecture and development plan, file-by-file code generation, and fixes from bug reports. Each file goes through `ast.parse` and ruff. Errors are returned to the model as short messages.

### 3.5 Testing Agent
Loads requirements and test cases, retrieves the code linked to each requirement, runs the tests, and turns failures into structured bug reports. Its reference is always the requirements and test cases, never the Development Agent's own claims.

| Aspect | Development Agent | Testing Agent |
|---|---|---|
| Phase | Construction | Validation |
| Inputs | Requirements, prompt, bug reports | Requirements, test cases, generated code |
| Outputs | Plan, code, fixes | Test results, bug reports |
| Deterministic checks | ast.parse, ruff | pytest |
| LLM used for | Planning, writing and fixing code | Reading failures, filling bug fields |

Both use the same model; independence comes from real test execution, user-written tests and separate prompts.

### 3.6 LLM subsystem
- `LLMClient` interface: `generate(prompt, max_tokens, temperature, stop)` and `stream(...)`.
- Default implementation: llama-cpp-python loading `models/*.gguf` once at start-up.
- A lock allows one generation at a time.
- Settings: `model_path`, `n_ctx`, `n_threads`, `n_batch`, `n_gpu_layers = 0`, `temperature`, `max_tokens`.
- Replaceable by a llama-server implementation without changing agents.

### 3.7 Retrieval subsystem (RAG)

| Step | Detail |
|---|---|
| Parse | python-docx, pypdf, plain text |
| Chunk | One requirement = one chunk with REQ-ID (about 250 to 400 tokens). One function or class (via `ast`) = one code chunk |
| Embed | bge-small-en-v1.5 via fastembed (ONNX) |
| Store | Chroma (embedded, persistent) for vectors. SQLite for chunk text, FTS5 index, hashes, links |
| Search | Semantic (Chroma) plus keyword (FTS5 BM25) |
| Merge | Reciprocal Rank Fusion, top 4 to 6 chunks into the prompt |
| Update | Hash check. Changed file: delete old chunks, upsert new. Chroma is rebuildable from SQLite |

Chroma collections: `requirements`, `code`, `tests_bugs`.

### 3.8 Validation subsystem
- **Static checks:** `ast.parse` and ruff on every generated Python file.
- **Test runner:** pytest through a subprocess in `workspace/` with a timeout and a restricted working directory. Output is parsed from the pytest XML report.

### 3.9 Storage

| Store | Location | Contents |
|---|---|---|
| SQLite | `data/ojas.db` | Projects, documents, chunks, FTS5, hashes, runs, bugs, test results, links |
| Chroma | `data/chroma/` | Embeddings and metadata |
| Workspace | `workspace/<project>/` | Generated and edited code and tests |
| Logs | `logs/` | Requests, errors, model timings |
| Reports | `reports/<project>/` | Plans, bug reports, pytest results, consolidated report |
| Config | `config/` | Model and runtime settings |

---

## 4. Workflow

```
Upload documents + prompt
        |
        v
Parse, chunk, embed, index            (no LLM)
        |
        v
Requirement analysis + development plan   (LLM)
        |
        v
Generate code, one file at a time     (LLM, with retrieved chunks)
        |
        v
ast.parse + ruff                      (no LLM) --error--> back to generation
        |
        v
User test cases loaded                (Testing Agent)
        |
        v
pytest execution                      (no LLM)
        |
   +----+----------------+
   |                     |
all pass /          failures
limit reached           |
   |                     v
   |              Bug report (LLM fills cause, expected, actual;
   |                          template adds REQ-ID, TC-ID, location)
   |                     |
   |                     v
   |              Fix failing function (LLM) --> static checks --> pytest
   v
Final project + consolidated test report
```

### 4.1 Fix loop stop rules
1. All tests pass: success.
2. Iteration limit reached (default 5): stop and report.
3. The same failure repeats twice: stop and escalate to the user.

### 4.2 Traceability
`REQ-ID` (requirement) → code symbol (function or class) → `TC-ID` (test case) → result → bug report. Stored as metadata in Chroma and as links in SQLite.

---

## 5. Request and Event Flow

1. User action in the UI (for example, Start development).
2. UI calls `POST /api/projects/{id}/runs` with the run type and prompt.
3. FastAPI validates the body (Pydantic) and creates a task. It returns `202` with a `run_id` at once.
4. The task manager runs the orchestrator in a worker thread so the event loop stays free.
5. The orchestrator publishes events (stage, file, iteration, tokens, result) to the event bus.
6. The UI listens on `GET /api/runs/{run_id}/events` (SSE) and updates panels live.
7. On completion, files are in `workspace/`, reports in `reports/`, and the run record is in SQLite.
8. The UI refreshes the file tree and results.

Only one run executes at a time. A second request is queued or rejected with a clear message.

---

## 6. API Design

Base path: `/api`. JSON bodies. Errors use a standard `{ "error": { "code", "message" } }` shape.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Model loaded, paths, versions |
| GET / PUT | `/settings` | Read and change runtime settings |
| GET / POST | `/projects` | List and create projects |
| GET / PATCH / DELETE | `/projects/{id}` | Read, rename, delete |
| POST | `/projects/{id}/documents` | Upload a document (multipart) |
| GET | `/projects/{id}/documents` | List documents and indexing status |
| GET | `/projects/{id}/requirements` | List requirement chunks with REQ-IDs |
| POST | `/projects/{id}/index` | (Re)index documents |
| POST | `/projects/{id}/runs` | Start a run: `plan`, `develop`, `test`, `fix_loop` |
| GET | `/projects/{id}/runs` | Run history |
| GET | `/runs/{run_id}` | Run status and summary |
| POST | `/runs/{run_id}/cancel` | Stop a run |
| GET | `/runs/{run_id}/events` | SSE stream of progress |
| GET | `/projects/{id}/files` | File tree |
| GET / PUT / DELETE | `/projects/{id}/files/{path}` | Read, save, delete a file |
| POST | `/projects/{id}/files/{path}/accept` | Accept a generated change (diff approval) |
| POST | `/projects/{id}/tests` | Upload or save test cases |
| GET | `/projects/{id}/bugs` | Bug reports |
| GET | `/projects/{id}/reports` | List reports |
| GET | `/projects/{id}/reports/{name}` | Download a report |

### 6.1 SSE event types

| Event | Payload (summary) |
|---|---|
| `stage` | stage name, status |
| `file` | path, action (created, changed), status |
| `token` | streamed model text (optional) |
| `check` | static check result for a file |
| `test` | TC-ID, pass or fail, duration |
| `bug` | bug ID, REQ-ID, TC-ID, short cause |
| `iteration` | loop number, limit |
| `done` | final status and report links |
| `error` | code and message |

---

## 7. Deployment and Runtime View

- One folder, one machine, loopback only.
- `start.bat` activates (or calls) `runtime/venv`, starts Uvicorn, and opens the browser.
- FastAPI serves the built React app from `frontend/dist` as static files, so **one process** serves both UI and API at `http://127.0.0.1:8000`. Node.js is needed only to build the frontend, not to run the platform.
- During development the Vite dev server runs on its own port and proxies `/api` to FastAPI.
- The model loads once at start-up; start-up time is noticeable on a CPU.

### 7.1 Project folder structure

```
ojas/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/            routers
|   |   |-- schemas/
|   |   |-- tasks/ events/
|   |   |-- orchestrator.py
|   |   |-- agents/         development_agent.py, testing_agent.py, prompts/
|   |   |-- llm/            client.py, llama_cpp_client.py
|   |   |-- rag/            parser.py, chunker.py, embedder.py, index.py, search.py
|   |   |-- validation/     static_check.py, test_runner.py
|   |   `-- storage/        db.py, files.py, reports.py
|   `-- tests/
|-- frontend/
|   |-- src/                components, pages, api, store, monaco setup
|   |-- public/
|   `-- dist/               built app served by FastAPI
|-- runtime/venv/
|-- models/                 *.gguf, embedding model files
|-- data/                   ojas.db, chroma/
|-- workspace/
|-- logs/
|-- reports/
|-- config/
|-- requirements.txt
|-- start.bat
`-- README.md
```

---

## 8. Offline and Security Design

| Measure | Detail |
|---|---|
| No cloud LLM API | All generation through the local GGUF model |
| Loopback only | Servers bound to 127.0.0.1 |
| No telemetry | Chroma and other library telemetry turned off |
| No runtime downloads | Models are placed on disk beforehand |
| Bundled frontend assets | Monaco, fonts and icons are served locally. Monaco's loader is configured to use the local package, not a CDN |
| No CDN-dependent docs page | FastAPI's `/docs` page loads assets from a CDN and may not render offline. The platform does not depend on it |
| Safe execution | Generated code runs in `workspace/` with a timeout, in a subprocess |
| Path safety | File endpoints reject paths that leave the project workspace |
| CORS | Not needed in production (same origin). In development only the Vite origin is allowed |

---

## 9. Quality Attributes and Design Decisions

| Attribute | How the design supports it |
|---|---|
| Performance on CPU | Single loaded model, short prompts, file-by-file generation, hybrid retrieval for small context |
| Responsiveness | Background tasks, SSE progress, streaming tokens |
| Reliability | Stop rules, one run at a time, cancel support, consistent workspace on failure |
| Independence of validation | Real pytest runs, user test cases, separate prompts and retrieval |
| Maintainability | Interfaces for LLM and retrieval, config-driven settings, separate modules |
| Traceability | REQ-ID and TC-ID links in SQLite and Chroma |

| Decision | Choice | Reason |
|---|---|---|
| Orchestration | Plain Python state machine | Two agents in a loop do not need a framework |
| Progress channel | SSE | One-way, simple, works through FastAPI, enough for progress and tokens |
| Serving the UI | FastAPI static files | One process, no Node at run time, easy offline |
| Source of truth for chunks | SQLite | Chroma can be rebuilt from it |
| LLM runtime | llama-cpp-python behind `LLMClient` | Simple start; llama-server can replace it later |

---

## 10. Open Items

- Final target hardware and measured tokens per second (benchmark with llama-bench).
- In-process model versus llama-server (current assumption: in-process).
- Fallback model (7B) if 3B quality is insufficient.
- Whether OCR (PaddleOCR) is added before the parsing step.
- Sandboxing strength for generated code beyond a restricted folder and timeout.
