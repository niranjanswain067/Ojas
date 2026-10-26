# Ojas: Setup Guide

| Item | Detail |
|---|---|
| Related documents | 02_System_Architecture.md, 04_Technology_Stack.md |
| Target OS | Windows 10/11 (x64) |
| Python | 3.10 or later |
| Node.js | 18 or later (build-time only) |

---

## 1. Prerequisites

Install these before starting. These are one-time installations.

| Tool | Version | Download | Verify |
|---|---|---|---|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) | `node --version` and `npm --version` |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) | `git --version` |

> **Important:** During Python installation, check "Add Python to PATH".

---

## 2. Project Folder Structure

Create the following folder structure (or clone the repo if already set up):

```
ojas/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   ├── runs.py
│   │   │   ├── files.py
│   │   │   ├── tests.py
│   │   │   ├── reports.py
│   │   │   ├── settings.py
│   │   │   └── health.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── tasks/
│   │   │   └── __init__.py
│   │   ├── events/
│   │   │   └── __init__.py
│   │   ├── orchestrator.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── development_agent.py
│   │   │   ├── testing_agent.py
│   │   │   └── prompts/
│   │   │       └── (prompt template files)
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── llama_cpp_client.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   ├── index.py
│   │   │   └── search.py
│   │   ├── validation/
│   │   │   ├── __init__.py
│   │   │   ├── static_check.py
│   │   │   └── test_runner.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── db.py
│   │       ├── files.py
│   │       └── reports.py
│   └── tests/
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── app/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   ├── store/
│   │   └── monaco/
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── package.json
├── runtime/
│   └── venv/              (created during setup)
├── models/                 (GGUF and embedding model files)
├── data/                   (created at runtime)
│   ├── ojas.db
│   └── chroma/
├── workspace/              (created at runtime)
├── logs/                   (created at runtime)
├── reports/                (created at runtime)
├── config/
│   └── settings.json
├── docs/                   (project documentation)
├── requirements.txt
├── start.bat
├── .gitignore
└── README.md
```

---

## 3. Backend Setup

### 3.1 Create virtual environment

Open a terminal in the project root:

```powershell
# Create the virtual environment
python -m venv runtime/venv

# Activate it
.\runtime\venv\Scripts\Activate.ps1
```

> **CMD users:** Use `.\runtime\venv\Scripts\activate.bat` instead.

### 3.2 Install Python dependencies

With the venv activated:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 `requirements.txt`

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
pydantic==2.10.*
python-multipart==0.0.*
sse-starlette==2.2.*
llama-cpp-python==0.3.*
fastembed==0.5.*
chromadb==0.6.*
python-docx==1.1.*
pypdf==5.4.*
pytest==8.3.*
ruff==0.9.*
httpx==0.28.*
aiofiles==24.*
```

> **Note:** Pin exact versions after confirming they work on your machine. The versions above are starting points.

### 3.4 llama-cpp-python installation notes

llama-cpp-python compiles C++ code during installation. On Windows, you may need:

1. **Visual Studio Build Tools** with "Desktop development with C++" workload.
2. Or use a pre-built wheel:
   ```powershell
   pip install llama-cpp-python --prefer-binary
   ```
3. If compilation fails, check [llama-cpp-python installation docs](https://github.com/abetlen/llama-cpp-python#installation).

### 3.5 Verify backend

```powershell
# With venv activated
cd backend
python -c "from app.main import app; print('FastAPI app created successfully')"
```

---

## 4. Model Setup

### 4.1 Download the LLM (GGUF)

Download the default model into `models/`:

| Model | File | Size | Download |
|---|---|---|---|
| Qwen2.5-Coder-3B-Instruct (Q4_K_M) | `qwen2.5-coder-3b-instruct-q4_k_m.gguf` | ~2 GB | [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF) |

```powershell
# Using Hugging Face CLI (optional)
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-Coder-3B-Instruct-GGUF qwen2.5-coder-3b-instruct-q4_k_m.gguf --local-dir models/
```

Or download manually and place the `.gguf` file in the `models/` folder.

### 4.2 Verify the model loads

```python
# test_model.py (run from project root with venv activated)
from llama_cpp import Llama

model = Llama(
    model_path="models/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
    n_ctx=4096,
    n_threads=4,
    n_gpu_layers=0,
    verbose=True
)

output = model.create_chat_completion(
    messages=[{"role": "user", "content": "Write a Python hello world."}],
    max_tokens=100,
    temperature=0.2
)

print(output["choices"][0]["message"]["content"])
print(f"Load time and generation complete!")
```

```powershell
python test_model.py
```

### 4.3 Embedding model

The fastembed library downloads the embedding model on first use. To pre-download for offline use:

```python
# test_embeddings.py
from fastembed import TextEmbedding

model = TextEmbedding("BAAI/bge-small-en-v1.5")
embeddings = list(model.embed(["This is a test sentence."]))
print(f"Embedding dimension: {len(embeddings[0])}")  # Should print 384
print("Embedding model working!")
```

```powershell
python test_embeddings.py
```

> The model files are cached by fastembed. Note the cache location for offline use. You may need to copy them to the project folder.

---

## 5. Frontend Setup

### 5.1 Install Node.js dependencies

```powershell
cd frontend
npm install
```

### 5.2 Verify the frontend builds

```powershell
npm run build
```

This creates `frontend/dist/` which FastAPI will serve as static files.

### 5.3 Vite dev server configuration

In `vite.config.ts`, configure the proxy to the backend:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
});
```

### 5.4 Monaco Editor offline configuration

In `src/monaco/loader.ts`:

```typescript
import * as monaco from 'monaco-editor';
import { loader } from '@monaco-editor/react';

// Use bundled Monaco instead of CDN
loader.config({ monaco });
```

Configure workers in `vite.config.ts` (add to the existing config):

```typescript
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

// In your monaco setup file
self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'typescript' || label === 'javascript') {
      return new tsWorker();
    }
    return new editorWorker();
  },
};
```

---

## 6. Configuration

### 6.1 Default settings file

Create `config/settings.json`:

```json
{
  "model_path": "models/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
  "n_ctx": 4096,
  "n_threads": 4,
  "n_batch": 512,
  "n_gpu_layers": 0,
  "max_tokens": 2048,
  "temperature": 0.2,
  "iteration_limit": 5,
  "test_timeout": 60,
  "host": "127.0.0.1",
  "port": 8000,
  "log_level": "info",
  "theme": "system"
}
```

### 6.2 `.gitignore`

```gitignore
# Python
runtime/venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Node
frontend/node_modules/
frontend/dist/

# Models (too large for Git)
models/*.gguf

# Runtime data
data/
workspace/
logs/
reports/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Environment
.env
```

---

## 7. Running the Platform

### 7.1 Development mode (two terminals)

**Terminal 1 — Backend:**
```powershell
.\runtime\venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173` in the browser. The Vite dev server proxies `/api` calls to the backend.

### 7.2 Production mode (single process)

```powershell
# Build the frontend first
cd frontend
npm run build

# Start the backend (serves frontend from dist/)
cd ..
.\runtime\venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in the browser.

### 7.3 `start.bat`

```batch
@echo off
echo Starting Ojas...
echo.

REM Activate virtual environment and start Uvicorn
cd /d "%~dp0"

REM Check if venv exists
if not exist "runtime\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Run setup first: python -m venv runtime\venv
    pause
    exit /b 1
)

REM Check if model exists
if not exist "models\*.gguf" (
    echo ERROR: No model file found in models\ folder.
    echo Download a GGUF model and place it in the models\ folder.
    pause
    exit /b 1
)

echo Starting backend server...
start "" http://127.0.0.1:8000
runtime\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

pause
```

---

## 8. Verify Offline Mode

After completing setup, verify the platform works offline:

1. **Disconnect from the internet** (disable Wi-Fi / unplug Ethernet).
2. Double-click `start.bat`.
3. Wait for "Model: Ready" in the browser UI.
4. Create a project, upload a document, start development.
5. Verify no errors about network or CDN.

### Common offline issues

| Issue | Cause | Fix |
|---|---|---|
| Monaco shows blank | Loading from CDN | Verify `loader.config({ monaco })` is set |
| Chroma logs connection errors | Telemetry enabled | Set `ANONYMIZED_TELEMETRY=False` in environment or Chroma config |
| fastembed tries to download model | Model not cached | Run `test_embeddings.py` online first |
| Fonts look different | Web fonts loading | Use system font stack only |

---

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| `pip install llama-cpp-python` fails | Install Visual Studio Build Tools with C++ workload, or use `--prefer-binary` |
| `ModuleNotFoundError` | Ensure venv is activated: `.\runtime\venv\Scripts\Activate.ps1` |
| Port 8000 already in use | Kill the process: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| Model loads but generation is very slow | Increase `n_threads` to match CPU core count. Try a smaller context (`n_ctx`) |
| SQLite "database is locked" | Ensure only one Uvicorn process is running |
| Frontend build fails | Delete `node_modules` and run `npm install` again |
| `npm run dev` proxy error | Ensure backend is running on port 8000 first |

---

## 10. Team Development Workflow

1. **Clone the repo:** `git clone <repo-url> && cd ojas`
2. **Run setup:** Follow sections 3–5 above.
3. **Create a branch:** `git checkout -b feature/your-feature`
4. **Make changes and test locally.**
5. **Run checks:**
   ```powershell
   # Backend
   cd backend && ruff check . && python -m pytest tests/

   # Frontend
   cd frontend && npm run lint && npm run build
   ```
6. **Push and create a pull request.**
