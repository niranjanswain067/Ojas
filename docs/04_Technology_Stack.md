# Ojas: Technology Stack

| Item | Detail |
|---|---|
| Related documents | 01_Project_Requirement_Documentation.md, 02_System_Architecture.md, 03_UI_Design.md |
| Frontend | React.js with Monaco Editor |
| Backend | FastAPI |
| Principle | Fully offline after one-time setup, CPU-only, one project folder |

Version numbers marked "pin" must be fixed in `requirements.txt` and `package-lock.json` when setup is done, using versions that are already installed and tested on the team's machines.

---

## 1. Stack at a Glance

| Layer | Technology |
|---|---|
| Frontend framework | React.js (18 or later) with TypeScript |
| Code editor | Monaco Editor (`monaco-editor` with `@monaco-editor/react`) |
| Build tool | Vite |
| Backend framework | FastAPI |
| ASGI server | Uvicorn |
| Language (backend) | Python 3.10+ |
| LLM | Qwen2.5-Coder-3B-Instruct, INT4 (Q4_K_M), GGUF |
| LLM runtime | llama.cpp through llama-cpp-python |
| Embeddings | bge-small-en-v1.5 via fastembed (ONNX) |
| Vector database | Chroma (embedded, persistent) |
| Keyword search and records | SQLite (FTS5) |
| Rank fusion | Reciprocal Rank Fusion |
| Static checks | `ast`, ruff |
| Test execution | pytest |
| Launcher | start.bat |

---

## 2. Frontend

### 2.1 Core

| Tool | Purpose | Why |
|---|---|---|
| React.js 18+ | UI library | Requested framework, large ecosystem, component model fits the panel layout |
| TypeScript | Typed code | Catches API-shape mistakes early; mirrors Pydantic models |
| Vite | Dev server and build | Fast builds, simple config, produces static files for FastAPI to serve |
| Monaco Editor | Code editor and diff view | Same editor engine as VS Code; syntax highlighting, diff editor, works offline when bundled |
| `@monaco-editor/react` | React wrapper for Monaco | Ready `Editor` and `DiffEditor` components |

### 2.2 Supporting libraries

| Tool | Purpose |
|---|---|
| React Router | Pages: Projects, Workspace, Reports, Settings |
| TanStack Query | Fetching and caching server data (projects, files, reports) |
| Zustand | Small UI and run-progress store |
| Tailwind CSS | Styling with design tokens, no runtime cost |
| `lucide-react` | Icons bundled in the build (no remote icons) |
| `react-resizable-panels` | Resizable sidebar, editor and bottom panel |
| `react-markdown` (+ `remark-gfm`) | Render reports and the development plan |
| Native `EventSource` | Server-Sent Events for progress (no extra library) |
| Native `fetch` | API calls via a small typed client |

### 2.3 Quality tools

| Tool | Purpose |
|---|---|
| ESLint and Prettier | Code style |
| Vitest and React Testing Library | Component and logic tests |

### 2.4 Offline rules for the frontend

- **Monaco must load locally.** Import `monaco-editor` and call `loader.config({ monaco })` so the wrapper does not fetch Monaco from a CDN.
- **Workers through Vite.** Configure Monaco's editor and language workers with Vite `?worker` imports so features work offline.
- **No web fonts, no CDN scripts, no remote icons.** Use system fonts and bundled icons.
- **Node.js is a build-time tool only.** Run `npm run build` once (or on each change). The result in `frontend/dist` is committed or copied with the project, so the target machine does not need Node.js.

### 2.5 Frontend project layout

```
frontend/
|-- src/
|   |-- main.tsx
|   |-- app/            router, providers, theme
|   |-- pages/          Projects, Workspace, Reports, Settings
|   |-- components/     editor, file-tree, run-panel, bottom-panel, reports, shared
|   |-- api/            typed client, SSE subscriber, types
|   |-- store/          UI and run state
|   `-- monaco/         loader config, workers, themes
|-- public/
|-- index.html
|-- vite.config.ts
`-- package.json
```

---

## 3. Backend

### 3.1 Core

| Tool | Purpose | Why |
|---|---|---|
| Python 3.10+ | Language | Required by the AI libraries; simple to maintain |
| FastAPI | REST API, request validation, SSE | Requested framework; async, typed, automatic validation |
| Uvicorn | ASGI server | Standard FastAPI server, runs on loopback |
| Pydantic v2 | Schemas and settings | Request and response models, config validation |
| `python-multipart` | File uploads | Needed for document upload endpoints |
| SSE support (`sse-starlette` or a streaming response) | Progress and token streaming | One-way push to the UI |
| `aiofiles` or standard file I/O | File service | Workspace read and write |

### 3.2 AI and retrieval

| Tool | Purpose | Notes |
|---|---|---|
| llama-cpp-python | Run the GGUF model on CPU | Loaded once; access protected by a lock |
| Qwen2.5-Coder-3B-Instruct (Q4_K_M) | Default LLM | About 2 GB, runs on 8 GB RAM, 32K context |
| fastembed + bge-small-en-v1.5 | Embeddings | ONNX on CPU; model files stored in `models/` |
| Chroma | Vector store | Embedded persistent mode; pass embeddings in directly; telemetry off |
| SQLite (FTS5) | Chunks, keyword search, hashes, links, runs | Source of truth for chunks |
| `python-docx`, `pypdf` | Parse docx and pdf | Plain text read directly |
| `ast` (standard library) | Split code into functions and classes | Exact code chunk boundaries |

### 3.3 Validation and testing

| Tool | Purpose |
|---|---|
| `ast.parse` | Syntax check of generated Python |
| ruff | Fast lint and error check |
| pytest | Run user tests and generated tests; XML report is parsed |
| `subprocess` | Run pytest in `workspace/` with a timeout |

### 3.4 Backend quality tools

| Tool | Purpose |
|---|---|
| pytest (platform tests) | Tests for the platform itself |
| httpx / FastAPI `TestClient` | API tests |
| ruff | Linting and formatting of platform code |

### 3.5 Backend project layout

```
backend/
|-- app/
|   |-- main.py
|   |-- api/            projects, documents, runs, files, tests, reports, settings, health
|   |-- schemas/
|   |-- tasks/ events/
|   |-- orchestrator.py
|   |-- agents/
|   |-- llm/
|   |-- rag/
|   |-- validation/
|   `-- storage/
`-- tests/
```

---

## 4. Model Choice

| Model | Approx. size (Q4) | Fit | Role |
|---|---|---|---|
| Qwen2.5-Coder-3B-Instruct | ~2 GB | Light and fast on CPU, runs on 8 GB RAM | **Default** |
| Qwen2.5-Coder-7B-Instruct | ~4.5 GB | Better quality, slower | Fallback |
| Qwen2.5-Coder-14B-Instruct | ~9 GB | Needs 16 to 32 GB, slow on CPU | Alternative |
| Qwen3-Coder-30B-A3B (MoE) | ~18 GB | Needs 32 GB RAM | Alternative |

Quantization INT4 (Q4_K_M) is the default for size and speed. INT8 (Q8_0, about 3.3 GB) is an option on machines with more RAM. The model is replaced through configuration without code changes. The expected speed of 10 to 20 tokens per second is an estimate; benchmark with llama-bench on the real machine. Check the model's licence on its model card before submission.

---

## 5. Data and Storage

| Store | Technology | Location |
|---|---|---|
| Records, chunks, FTS index, links | SQLite | `data/ojas.db` |
| Vectors | Chroma | `data/chroma/` |
| Generated code and tests | Plain files | `workspace/` |
| Logs | Plain files | `logs/` |
| Reports | Markdown and pytest XML | `reports/` |
| Settings | JSON or YAML | `config/` |

---

## 6. Runtime and Deployment

| Item | Choice |
|---|---|
| Processes | One backend process (Uvicorn) serving both the API and the built frontend |
| Address | `http://127.0.0.1:8000` |
| Environment | `runtime/venv` created with `python -m venv`; packages from `requirements.txt` |
| Launcher | `start.bat` calls the venv interpreter directly, starts Uvicorn, opens the browser |
| Dev mode | Vite dev server (for example port 5173) with a proxy to `/api` on port 8000 |
| Frontend delivery | `frontend/dist` mounted as static files by FastAPI |
| Node.js | Needed only to build the frontend |

**Virtual environment note.** A venv holds packages but records the base Python path, so it is not portable between machines or folders. Recreate it from `requirements.txt` if the folder moves. `models/`, `data/` and the other folders can be copied as they are.

---

## 7. One-Time Setup (Online) and Run (Offline)

### 7.1 One-time setup (internet needed)
1. Install Python 3.10 or later (and Node.js 18 or later on the machine that builds the frontend).
2. Create `runtime/venv` and install `requirements.txt`.
3. Run `npm install` and `npm run build` in `frontend/`.
4. Download the GGUF model into `models/`.
5. Download the embedding model files (bge-small-en-v1.5) into the project folder.
6. Run once with the network on to confirm that nothing else is fetched.

### 7.2 Run (offline)
1. Double-click `start.bat`.
2. Wait for "Model: Ready" in the UI.
3. Use the platform. No outbound connection is made.

---

## 8. Offline and Security Checklist

- No cloud LLM API in the code.
- Servers bound to 127.0.0.1.
- Chroma telemetry off; no analytics anywhere.
- Models pre-downloaded; libraries do not fetch models at run time.
- Monaco, fonts and icons bundled; no CDN references in `index.html`.
- FastAPI `/docs` page is not relied on (it loads CDN assets by default).
- Generated code runs only in `workspace/` through a subprocess with a timeout.
- File API rejects paths that escape the project workspace.

---

## 9. Environment Requirements

| Item | Requirement |
|---|---|
| OS | Windows (start.bat) |
| CPU | Multi-core x64; more physical cores give faster generation |
| RAM | 8 GB minimum for the 3B model; 16 GB recommended |
| Disk | A few GB for the model, embedding files, packages and project data |
| GPU | Not required |
| Browser | A current Chromium-based browser or Firefox |

Final hardware is still to be confirmed.

---

## 10. Dependency Lists (starting point)

**`requirements.txt` (pin versions after setup)**
```
fastapi
uvicorn
pydantic
python-multipart
sse-starlette
llama-cpp-python
fastembed
chromadb
python-docx
pypdf
pytest
ruff
httpx
```

**Frontend `package.json` dependencies (pin versions after setup)**
```
react, react-dom, react-router-dom
@tanstack/react-query, zustand
monaco-editor, @monaco-editor/react
react-markdown, remark-gfm
react-resizable-panels, lucide-react
tailwindcss, vite, typescript
eslint, prettier, vitest, @testing-library/react
```

---

## 11. Decisions and Alternatives

| Area | Chosen | Alternative considered | Reason |
|---|---|---|---|
| Frontend | React.js + Monaco | Streamlit or plain HTML | Requested; better editor and diff experience |
| Backend | FastAPI | Flask | Requested; async, typed schemas, SSE |
| Progress channel | SSE | WebSocket | One-way updates are enough and simpler |
| LLM runtime | llama-cpp-python (in-process) | llama-server | Fewer moving parts; replaceable behind `LLMClient` |
| Vector store | Chroma | FAISS or NumPy | Metadata, persistence and upsert are built in |
| Orchestration | Plain Python | LangChain or similar | Two agents in a loop need no framework |
| Serving UI | FastAPI static files | Separate Node server | One process, no Node at run time |

---

## 12. Open Items

- Pin exact versions of every package after the first working setup.
- Confirm target hardware and measure tokens per second.
- Decide whether to add OCR (PaddleOCR) before document parsing.
- Decide whether to export reports to PDF or Word (extra libraries).
- Confirm the 3B model's licence.
