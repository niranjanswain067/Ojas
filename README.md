# Ojas

**Local Autonomous Software Engineer with Verification and Self-Healing Loops.**

> An offline-first, local-LLM-driven autonomous coding assistant that designs, implements, verifies, and self-heals software solutions directly within your local workspace. Nothing leaves your machine.

---

## Features

- **100% Offline Execution**: Powered by `llama-cpp-python` (GGUF models) and local embeddings (`fastembed` + `ChromaDB` + SQLite `FTS5`). No cloud APIs or telemetry.
- **Hybrid RAG Retrieval**: Combines dense vector search and sparse FTS5 keyword search with Reciprocal Rank Fusion (RRF) over uploaded requirement documents (`.pdf`, `.docx`, `.txt`, `.md`).
- **Autonomous Multi-Agent Pipeline**:
  - **Development Agent**: Analyzes requirements, proposes modular development plans, and generates multi-language code (Python, HTML, CSS, JavaScript) with static syntax validation (`ast.parse`, HTML/CSS/JS checks, `ruff`).
  - **Testing Agent & Self-Healing Fix Loop**: Runs `pytest` in isolated workspaces, parses tracebacks, creates structured bug reports linked to requirements, and iteratively fixes failing functions (up to configurable iteration limits with repeated-failure detection).
- **Interactive Workspace UI**: Built with React, TypeScript, Tailwind CSS, and an offline-bundled Monaco Editor with real-time Server-Sent Events (SSE) progress streaming.
- **Traceability, Reports & Export**:
  - Consolidated Markdown reports mapping Requirements ➔ Files ➔ Test Cases ➔ Bug Reports.
  - One-click **Download Project** button to export the entire project workspace as a `.zip` archive.
- **Performance Metrics**: Automatically records stage durations, token throughput, peak RAM usage, and fix-loop iterations to `logs/metrics.json`.

---

## Quick Start (Windows)

### Prerequisites
- Python virtual environment located at `runtime/venv/` (Python 3.10–3.14)
- GGUF model file placed at `models/ojas.gguf` (configured in `config/settings.json`)
- Built frontend bundle in `frontend/dist/`

### Launch Application
Double-click **`start.bat`** or run from terminal:
```bat
start.bat
```
This starts the FastAPI + Uvicorn server on `http://127.0.0.1:8000` and automatically opens Ojas in your default browser once the health check passes.

---

## Development & Testing

### Backend Tests
```bat
runtime\venv\Scripts\pytest.exe backend/tests/ -v
```

### Frontend Tests & Build
```bat
cd frontend
npm test -- --run
npm run build
```

### Sample Projects
Three reference sample projects are available under `samples/` for testing and benchmarking:
- `samples/calculator/` — Basic arithmetic calculator with history
- `samples/library_system/` — Book catalog, member registration, and circulation
- `samples/student_grade_manager/` — Course grades, GPA calculation, and report cards

---

## Documentation

See the [docs/](docs/) directory for full technical specifications:
- `01_Project_Requirement_Documentation.md` — System requirements
- `02_System_Architecture.md` — Component architecture and data flow
- `03_UI_Design.md` — UI layout and design system
- `05_Database_Schema.md` — 12-table SQLite + FTS5 schema
- `06_API_Specification.md` — REST & SSE API contracts
- `08_Setup_Guide.md` — Machine setup instructions
- `09_Implementation_Plan.md` — Complete 20-phase roadmap
