# Ojas: API Specification

| Item | Detail |
|---|---|
| Related documents | 01_Project_Requirement_Documentation.md, 02_System_Architecture.md, 05_Database_Schema.md |
| Base URL | `http://127.0.0.1:8000/api` |
| Format | JSON request/response bodies |
| Auth | None (single local user) |
| Error shape | `{ "error": { "code": "<ERROR_CODE>", "message": "<human readable>" } }` |

---

## 1. Conventions

- **Base path:** All endpoints are prefixed with `/api`.
- **IDs:** UUID4 strings.
- **Timestamps:** ISO 8601 strings.
- **Pagination:** Not needed for first version (project-scoped, small datasets).
- **File uploads:** `multipart/form-data`.
- **Status codes:**
  - `200` — Success (GET, PUT, PATCH).
  - `201` — Created (POST that creates a resource).
  - `202` — Accepted (async task started).
  - `204` — No Content (DELETE).
  - `400` — Bad Request (validation error).
  - `404` — Not Found.
  - `409` — Conflict (e.g. another run is active).
  - `500` — Internal Server Error.

---

## 2. Health and Settings

### 2.1 `GET /api/health`

Check backend and model status.

**Response 200:**
```json
{
  "status": "ready",
  "model_loaded": true,
  "model_name": "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
  "model_load_time_s": 12.3,
  "backend_version": "0.1.0",
  "python_version": "3.10.12",
  "paths": {
    "data": "data/",
    "models": "models/",
    "workspace": "workspace/",
    "logs": "logs/",
    "reports": "reports/"
  },
  "last_error": null
}
```

### 2.2 `GET /api/settings`

Get all runtime settings.

**Response 200:**
```json
{
  "model_path": "models/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
  "n_ctx": 4096,
  "n_threads": 4,
  "max_tokens": 2048,
  "temperature": 0.2,
  "iteration_limit": 5,
  "test_timeout": 60,
  "theme": "system"
}
```

### 2.3 `PUT /api/settings`

Update runtime settings. Model-related changes may trigger a reload.

**Request body:**
```json
{
  "n_ctx": 8192,
  "temperature": 0.3
}
```

**Response 200:**
```json
{
  "settings": { "...updated settings..." },
  "model_reload_required": true,
  "model_reload_status": "reloading"
}
```

---

## 3. Projects

### 3.1 `GET /api/projects`

List all projects.

**Response 200:**
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Library System",
      "description": "A book management system",
      "status": "done",
      "document_count": 3,
      "requirement_count": 12,
      "last_run_result": "all_passed",
      "created_at": "2026-10-22T10:00:00",
      "updated_at": "2026-10-23T14:30:00"
    }
  ]
}
```

### 3.2 `POST /api/projects`

Create a new project.

**Request body:**
```json
{
  "name": "Library System",
  "description": "A book management system"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "name": "Library System",
  "description": "A book management system",
  "status": "idle",
  "created_at": "2026-10-22T10:00:00",
  "updated_at": "2026-10-22T10:00:00"
}
```

**Error 400:** Name is empty or already exists.

### 3.3 `GET /api/projects/{project_id}`

Get project details.

**Response 200:** Same shape as a single project in the list, plus:
```json
{
  "...project fields...",
  "document_count": 3,
  "requirement_count": 12,
  "test_case_count": 8,
  "bug_count": 2,
  "run_count": 5
}
```

### 3.4 `PATCH /api/projects/{project_id}`

Rename or update a project.

**Request body:**
```json
{
  "name": "Library System v2",
  "description": "Updated description"
}
```

**Response 200:** Updated project object.

### 3.5 `DELETE /api/projects/{project_id}`

Delete a project and all its data (documents, workspace, runs, reports).

**Response 204:** No content.

**Error 409:** A run is currently active for this project.

---

## 4. Documents

### 4.1 `POST /api/projects/{project_id}/documents`

Upload one or more requirement documents.

**Request:** `multipart/form-data` with field `files` (one or more files).

**Response 201:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "requirements.pdf",
      "file_type": "pdf",
      "status": "uploaded",
      "uploaded_at": "2026-10-22T10:05:00"
    }
  ]
}
```

**Error 400:** Unsupported file type (not docx, pdf, or txt).

### 4.2 `GET /api/projects/{project_id}/documents`

List all documents for a project with their indexing status.

**Response 200:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "requirements.pdf",
      "file_type": "pdf",
      "file_hash": "sha256...",
      "status": "indexed",
      "chunk_count": 8,
      "uploaded_at": "2026-10-22T10:05:00",
      "indexed_at": "2026-10-22T10:05:30"
    }
  ]
}
```

### 4.3 `DELETE /api/projects/{project_id}/documents/{document_id}`

Delete a document and its chunks.

**Response 204:** No content.

### 4.4 `GET /api/projects/{project_id}/requirements`

List all requirement chunks across all documents.

**Response 200:**
```json
{
  "requirements": [
    {
      "id": "chunk_uuid",
      "req_id": "REQ-001",
      "heading": "Add Book",
      "content": "The system shall allow...",
      "document_filename": "requirements.pdf",
      "chunk_type": "requirement",
      "linked_code": ["app/models.py:Book", "app/services.py:add_book"],
      "linked_tests": ["TC-001", "TC-002"]
    }
  ]
}
```

### 4.5 `POST /api/projects/{project_id}/index`

Trigger (re-)indexing of all documents. Skips unchanged files (hash match).

**Response 202:**
```json
{
  "run_id": "uuid",
  "message": "Indexing started",
  "documents_to_index": 2,
  "documents_skipped": 1
}
```

---

## 5. Runs

### 5.1 `POST /api/projects/{project_id}/runs`

Start a new run.

**Request body:**
```json
{
  "run_type": "develop",
  "prompt": "Build a library management system with book CRUD and member management"
}
```

| `run_type` | Description |
|---|---|
| `plan` | Generate requirement analysis and development plan only |
| `develop` | Plan (if not done) + generate code |
| `test` | Run tests only |
| `fix_loop` | Test + fix cycle until stop rule |

**Response 202:**
```json
{
  "run_id": "uuid",
  "run_type": "develop",
  "status": "queued",
  "message": "Development run started"
}
```

**Error 409:** Another run is already active.

### 5.2 `GET /api/projects/{project_id}/runs`

List run history for a project.

**Response 200:**
```json
{
  "runs": [
    {
      "id": "uuid",
      "run_type": "develop",
      "status": "completed",
      "prompt": "Build a library...",
      "iteration_count": 0,
      "stop_reason": null,
      "tokens_generated": 4520,
      "started_at": "2026-10-22T10:10:00",
      "completed_at": "2026-10-22T10:25:00",
      "created_at": "2026-10-22T10:10:00"
    }
  ]
}
```

### 5.3 `GET /api/runs/{run_id}`

Get detailed status of a specific run.

**Response 200:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "run_type": "fix_loop",
  "status": "running",
  "prompt": "...",
  "plan_text": "## Development Plan\n...",
  "iteration_count": 2,
  "iteration_limit": 5,
  "stop_reason": null,
  "tokens_generated": 8340,
  "current_stage": "fixing",
  "current_file": "app/services.py",
  "started_at": "...",
  "completed_at": null,
  "steps": [
    {
      "step_index": 0,
      "stage": "testing",
      "agent": "testing",
      "description": "Running pytest",
      "status": "completed",
      "duration_ms": 3200
    }
  ]
}
```

### 5.4 `POST /api/runs/{run_id}/cancel`

Cancel a running task.

**Response 200:**
```json
{
  "run_id": "uuid",
  "status": "cancelled",
  "message": "Run cancellation requested"
}
```

### 5.5 `GET /api/runs/{run_id}/events`

Server-Sent Events stream for live progress.

**Response:** `text/event-stream`

```
event: stage
data: {"stage": "generating", "status": "started", "message": "Generating code files"}

event: file
data: {"path": "app/models.py", "action": "created", "status": "ast_ok", "lines": 45}

event: token
data: {"text": "def add_book", "total_tokens": 120}

event: check
data: {"file": "app/models.py", "tool": "ruff", "passed": true, "issues": []}

event: test
data: {"tc_id": "TC-001", "name": "test_add_book", "result": "passed", "duration_ms": 150}

event: bug
data: {"bug_id": "B-001", "req_id": "REQ-002", "tc_id": "TC-003", "severity": "high", "cause": "Missing null check"}

event: iteration
data: {"iteration": 2, "limit": 5, "failures_remaining": 1}

event: done
data: {"status": "completed", "stop_reason": "all_passed", "report_links": ["/api/projects/uuid/reports/consolidated"]}

event: error
data: {"code": "MODEL_ERROR", "message": "Generation failed: context length exceeded"}
```

---

## 6. Workspace Files

### 6.1 `GET /api/projects/{project_id}/files`

Get file tree of the workspace.

**Response 200:**
```json
{
  "tree": [
    {
      "name": "app",
      "path": "app",
      "type": "directory",
      "children": [
        {
          "name": "models.py",
          "path": "app/models.py",
          "type": "file",
          "size_bytes": 1234,
          "is_generated": true,
          "pending_approval": false,
          "updated_at": "2026-10-22T10:15:00"
        },
        {
          "name": "__init__.py",
          "path": "app/__init__.py",
          "type": "file",
          "size_bytes": 0,
          "is_generated": true,
          "pending_approval": false,
          "updated_at": "2026-10-22T10:15:00"
        }
      ]
    }
  ]
}
```

### 6.2 `GET /api/projects/{project_id}/files/{path:path}`

Read a file's content.

**Response 200:**
```json
{
  "path": "app/models.py",
  "content": "class Book:\n    ...",
  "size_bytes": 1234,
  "is_generated": true,
  "pending_approval": false,
  "language": "python",
  "linked_req_ids": ["REQ-001"],
  "updated_at": "2026-10-22T10:15:00"
}
```

**Error 404:** File does not exist.

### 6.3 `PUT /api/projects/{project_id}/files/{path:path}`

Create or save a file.

**Request body:**
```json
{
  "content": "class Book:\n    def __init__(self, title):\n        self.title = title\n"
}
```

**Response 200:**
```json
{
  "path": "app/models.py",
  "size_bytes": 78,
  "updated_at": "2026-10-22T10:20:00"
}
```

**Error 400:** Path attempts to escape workspace.

### 6.4 `DELETE /api/projects/{project_id}/files/{path:path}`

Delete a file from the workspace.

**Response 204:** No content.

### 6.5 `POST /api/projects/{project_id}/files/{path:path}/accept`

Accept a generated change (approve in diff view).

**Response 200:**
```json
{
  "path": "app/models.py",
  "status": "accepted",
  "message": "Change accepted"
}
```

### 6.6 `POST /api/projects/{project_id}/files/{path:path}/reject`

Reject a generated change (revert to previous version).

**Response 200:**
```json
{
  "path": "app/models.py",
  "status": "rejected",
  "message": "Change rejected, previous version restored"
}
```

---

## 7. Tests

### 7.1 `POST /api/projects/{project_id}/tests`

Upload or save test cases.

**Request:** `multipart/form-data` with field `files` (pytest files) or JSON body for inline test cases.

**Multipart upload response 201:**
```json
{
  "test_cases": [
    {
      "id": "uuid",
      "tc_id": "TC-001",
      "name": "test_add_book",
      "file_path": "tests/test_books.py",
      "function_name": "test_add_book",
      "source": "user",
      "status": "not_run"
    }
  ]
}
```

### 7.2 `GET /api/projects/{project_id}/tests`

List all test cases for a project.

**Response 200:**
```json
{
  "test_cases": [
    {
      "id": "uuid",
      "tc_id": "TC-001",
      "name": "test_add_book",
      "file_path": "tests/test_books.py",
      "function_name": "test_add_book",
      "linked_req_ids": ["REQ-001"],
      "source": "user",
      "status": "passed",
      "last_run_at": "2026-10-22T10:30:00"
    }
  ]
}
```

### 7.3 `GET /api/projects/{project_id}/tests/{test_case_id}/results`

Get all results for a specific test case across runs.

**Response 200:**
```json
{
  "test_case_id": "uuid",
  "tc_id": "TC-001",
  "results": [
    {
      "run_id": "uuid",
      "iteration": 0,
      "result": "failed",
      "error_message": "AssertionError: expected 5, got 3",
      "duration_ms": 150,
      "created_at": "..."
    },
    {
      "run_id": "uuid",
      "iteration": 1,
      "result": "passed",
      "duration_ms": 120,
      "created_at": "..."
    }
  ]
}
```

---

## 8. Bug Reports

### 8.1 `GET /api/projects/{project_id}/bugs`

List all bug reports for a project.

**Query params:** `?status=open` (optional filter).

**Response 200:**
```json
{
  "bugs": [
    {
      "id": "uuid",
      "bug_id": "B-001",
      "req_id": "REQ-002",
      "tc_id": "TC-003",
      "file_path": "app/services.py",
      "function_name": "issue_book",
      "severity": "high",
      "expected_result": "Should raise error when book is unavailable",
      "actual_result": "Returns None silently",
      "probable_cause": "Missing availability check before issuing",
      "iteration": 1,
      "status": "fixed",
      "fix_description": "Added availability check in issue_book()",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

### 8.2 `GET /api/projects/{project_id}/bugs/{bug_id}`

Get a single bug report with full details.

**Response 200:** Single bug object (same shape as list item).

---

## 9. Reports

### 9.1 `GET /api/projects/{project_id}/reports`

List available reports for a project.

**Response 200:**
```json
{
  "reports": [
    {
      "name": "development_plan",
      "title": "Development Plan",
      "type": "markdown",
      "generated_at": "2026-10-22T10:12:00",
      "run_id": "uuid"
    },
    {
      "name": "consolidated_test_report",
      "title": "Consolidated Test Report",
      "type": "markdown",
      "generated_at": "2026-10-22T10:35:00",
      "run_id": "uuid"
    }
  ]
}
```

### 9.2 `GET /api/projects/{project_id}/reports/{report_name}`

Download a report.

**Query params:** `?format=markdown` (default) or `?format=json`.

**Response 200 (markdown):**
```
Content-Type: text/markdown

# Consolidated Test Report
## Project: Library System
...
```

**Response 200 (json):**
```json
{
  "report_name": "consolidated_test_report",
  "title": "Consolidated Test Report",
  "content": "# Consolidated Test Report\n...",
  "summary": {
    "total_tests": 8,
    "passed": 7,
    "failed": 1,
    "iterations": 3,
    "total_time_s": 180
  },
  "coverage": [
    {
      "req_id": "REQ-001",
      "heading": "Add Book",
      "tests": [
        { "tc_id": "TC-001", "result": "passed" },
        { "tc_id": "TC-002", "result": "passed" }
      ]
    },
    {
      "req_id": "REQ-003",
      "heading": "Return Book",
      "tests": []
    }
  ]
}
```

---

## 10. Plan Approval

### 10.1 `GET /api/projects/{project_id}/plan`

Get the current development plan (if generated).

**Response 200:**
```json
{
  "plan_text": "## Architecture\n...\n## Modules\n...\n## Files\n...",
  "status": "pending_approval",
  "run_id": "uuid"
}
```

**Response 404:** No plan has been generated yet.

### 10.2 `POST /api/projects/{project_id}/plan/approve`

Approve the plan (optionally with edits) and proceed to code generation.

**Request body:**
```json
{
  "plan_text": "## Architecture\n... (edited by user) ...",
  "proceed": true
}
```

**Response 202:**
```json
{
  "run_id": "uuid",
  "message": "Plan approved, code generation started"
}
```

---

## 11. Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Request body validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Conflicting state (e.g. run already active) |
| `PATH_ESCAPE` | 400 | File path attempts to escape workspace |
| `UNSUPPORTED_FILE_TYPE` | 400 | Document type not supported |
| `MODEL_NOT_LOADED` | 503 | Model is not ready |
| `MODEL_ERROR` | 500 | LLM generation failed |
| `RUN_ACTIVE` | 409 | Another run is already in progress |
| `NO_DOCUMENTS` | 400 | No indexed documents to work with |
| `NO_TESTS` | 400 | No test cases uploaded for testing |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## 12. CORS

- **Production:** Not needed. Frontend is served from the same origin by FastAPI.
- **Development:** Allow `http://localhost:5173` (Vite dev server) only.

```python
# In main.py, only in dev mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
