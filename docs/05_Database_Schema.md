# Ojas: Database Schema

| Item | Detail |
|---|---|
| Related documents | 01_Project_Requirement_Documentation.md, 02_System_Architecture.md |
| Database | SQLite (`data/ojas.db`) |
| Vector store | Chroma (`data/chroma/`) |
| Principle | SQLite is the source of truth. Chroma is rebuildable from SQLite. |

---

## 1. Overview

All structured data lives in a single SQLite database at `data/ojas.db`. Chroma stores only embeddings and metadata for semantic search. If the Chroma data is lost it can be rebuilt from the chunks stored in SQLite.

### 1.1 Naming conventions

- Table names: `snake_case`, plural (e.g. `projects`, `documents`).
- Column names: `snake_case`.
- Primary keys: `id` (TEXT, UUID4 string) unless noted otherwise.
- Timestamps: ISO 8601 strings stored as TEXT (`YYYY-MM-DDTHH:MM:SS`).
- Foreign keys: `<table_singular>_id` (e.g. `project_id`).
- Boolean columns: INTEGER (0 = false, 1 = true).
- All foreign keys have `ON DELETE CASCADE` unless stated otherwise.

---

## 2. Entity-Relationship Diagram

```
projects 1──* documents 1──* chunks
    |                           |
    |                           * (linked via req_id)
    |                           |
    +──────* runs 1──* run_steps
    |
    +──────* workspace_files
    |
    +──────* test_cases 1──* test_results
    |                           |
    |                           * (linked via tc_id)
    |                           |
    +──────* bug_reports ───────+
    |
    +──────* traceability_links
```

---

## 3. Tables

### 3.1 `projects`

Stores each user project.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `name` | TEXT | NOT NULL, UNIQUE | Project display name |
| `description` | TEXT | DEFAULT '' | Optional description |
| `status` | TEXT | NOT NULL, DEFAULT 'idle' | One of: `idle`, `indexing`, `planning`, `developing`, `testing`, `fixing`, `done`, `failed` |
| `created_at` | TEXT | NOT NULL | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'idle',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

### 3.2 `documents`

Uploaded requirement/specification files.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `filename` | TEXT | NOT NULL | Original filename (e.g. `requirements.pdf`) |
| `file_type` | TEXT | NOT NULL | One of: `docx`, `pdf`, `txt` |
| `file_hash` | TEXT | NOT NULL | SHA-256 hash of file content |
| `file_path` | TEXT | NOT NULL | Relative path in project folder |
| `status` | TEXT | NOT NULL, DEFAULT 'uploaded' | One of: `uploaded`, `indexing`, `indexed`, `failed` |
| `chunk_count` | INTEGER | DEFAULT 0 | Number of chunks extracted |
| `uploaded_at` | TEXT | NOT NULL | ISO 8601 |
| `indexed_at` | TEXT | | ISO 8601, NULL if not yet indexed |

```sql
CREATE TABLE documents (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    file_hash   TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'uploaded',
    chunk_count INTEGER DEFAULT 0,
    uploaded_at TEXT NOT NULL,
    indexed_at  TEXT,
    UNIQUE(project_id, filename)
);

CREATE INDEX idx_documents_project ON documents(project_id);
```

### 3.3 `chunks`

Requirement chunks extracted from documents. Source of truth for Chroma rebuilds.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `document_id` | TEXT | NOT NULL, FK → documents.id | Source document |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project (denormalized for fast queries) |
| `req_id` | TEXT | | Requirement identifier (e.g. `REQ-001`), NULL for non-requirement chunks |
| `chunk_type` | TEXT | NOT NULL | One of: `requirement`, `specification`, `architecture`, `general` |
| `heading` | TEXT | DEFAULT '' | Section heading the chunk belongs to |
| `content` | TEXT | NOT NULL | Full text of the chunk |
| `token_count` | INTEGER | | Estimated token count |
| `chunk_index` | INTEGER | NOT NULL | Order within the document (0-based) |
| `content_hash` | TEXT | NOT NULL | SHA-256 hash of content for change detection |
| `metadata` | TEXT | DEFAULT '{}' | JSON string for extra metadata |
| `created_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE chunks (
    id           TEXT PRIMARY KEY,
    document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id   TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    req_id       TEXT,
    chunk_type   TEXT NOT NULL,
    heading      TEXT DEFAULT '',
    content      TEXT NOT NULL,
    token_count  INTEGER,
    chunk_index  INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    metadata     TEXT DEFAULT '{}',
    created_at   TEXT NOT NULL
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_project ON chunks(project_id);
CREATE INDEX idx_chunks_req_id ON chunks(req_id);
```

### 3.4 `chunks_fts` (FTS5 virtual table)

Full-text search index over chunk content for BM25 keyword retrieval.

```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    heading,
    req_id,
    content='chunks',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content, heading, req_id)
    VALUES (new.rowid, new.content, new.heading, new.req_id);
END;

CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, heading, req_id)
    VALUES ('delete', old.rowid, old.content, old.heading, old.req_id);
END;

CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, heading, req_id)
    VALUES ('delete', old.rowid, old.content, old.heading, old.req_id);
    INSERT INTO chunks_fts(rowid, content, heading, req_id)
    VALUES (new.rowid, new.content, new.heading, new.req_id);
END;
```

### 3.5 `code_chunks`

Code chunks extracted from generated workspace files (for code retrieval).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `file_path` | TEXT | NOT NULL | Relative path in workspace (e.g. `app/models.py`) |
| `symbol_name` | TEXT | NOT NULL | Function or class name |
| `symbol_type` | TEXT | NOT NULL | One of: `function`, `class`, `method`, `module` |
| `content` | TEXT | NOT NULL | Full source code of the symbol |
| `start_line` | INTEGER | NOT NULL | Start line in the file |
| `end_line` | INTEGER | NOT NULL | End line in the file |
| `content_hash` | TEXT | NOT NULL | SHA-256 of content |
| `linked_req_ids` | TEXT | DEFAULT '[]' | JSON array of linked REQ-IDs |
| `created_at` | TEXT | NOT NULL | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE code_chunks (
    id             TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path      TEXT NOT NULL,
    symbol_name    TEXT NOT NULL,
    symbol_type    TEXT NOT NULL,
    content        TEXT NOT NULL,
    start_line     INTEGER NOT NULL,
    end_line       INTEGER NOT NULL,
    content_hash   TEXT NOT NULL,
    linked_req_ids TEXT DEFAULT '[]',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE INDEX idx_code_chunks_project ON code_chunks(project_id);
CREATE INDEX idx_code_chunks_file ON code_chunks(project_id, file_path);
```

### 3.6 `runs`

Each invocation of plan, develop, test, or fix loop.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `run_type` | TEXT | NOT NULL | One of: `plan`, `develop`, `test`, `fix_loop` |
| `status` | TEXT | NOT NULL, DEFAULT 'queued' | One of: `queued`, `running`, `completed`, `failed`, `cancelled` |
| `prompt` | TEXT | DEFAULT '' | User prompt for this run |
| `plan_text` | TEXT | | Generated development plan (for plan/develop runs) |
| `iteration_count` | INTEGER | DEFAULT 0 | Number of fix-loop iterations completed |
| `iteration_limit` | INTEGER | DEFAULT 5 | Maximum allowed iterations |
| `stop_reason` | TEXT | | One of: `all_passed`, `iteration_limit`, `repeated_failure`, `user_cancelled`, NULL |
| `error_message` | TEXT | | Error details if status is `failed` |
| `tokens_generated` | INTEGER | DEFAULT 0 | Total tokens generated in this run |
| `started_at` | TEXT | | ISO 8601 |
| `completed_at` | TEXT | | ISO 8601 |
| `created_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE runs (
    id               TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    run_type         TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'queued',
    prompt           TEXT DEFAULT '',
    plan_text        TEXT,
    iteration_count  INTEGER DEFAULT 0,
    iteration_limit  INTEGER DEFAULT 5,
    stop_reason      TEXT,
    error_message    TEXT,
    tokens_generated INTEGER DEFAULT 0,
    started_at       TEXT,
    completed_at     TEXT,
    created_at       TEXT NOT NULL
);

CREATE INDEX idx_runs_project ON runs(project_id);
CREATE INDEX idx_runs_status ON runs(status);
```

### 3.7 `run_steps`

Individual steps within a run for audit trail.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `run_id` | TEXT | NOT NULL, FK → runs.id | Parent run |
| `step_index` | INTEGER | NOT NULL | Order within the run (0-based) |
| `stage` | TEXT | NOT NULL | Stage name (e.g. `indexing`, `planning`, `generating`, `static_check`, `testing`, `fixing`) |
| `agent` | TEXT | | One of: `development`, `testing`, NULL |
| `description` | TEXT | NOT NULL | Human-readable description of what happened |
| `file_path` | TEXT | | File being processed (if applicable) |
| `input_summary` | TEXT | | Summary of prompt/input sent to LLM |
| `output_summary` | TEXT | | Summary of LLM response |
| `tokens_used` | INTEGER | DEFAULT 0 | Tokens used in this step |
| `duration_ms` | INTEGER | | Time taken in milliseconds |
| `status` | TEXT | NOT NULL | One of: `started`, `completed`, `failed`, `skipped` |
| `error_message` | TEXT | | Error details if failed |
| `created_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE run_steps (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_index     INTEGER NOT NULL,
    stage          TEXT NOT NULL,
    agent          TEXT,
    description    TEXT NOT NULL,
    file_path      TEXT,
    input_summary  TEXT,
    output_summary TEXT,
    tokens_used    INTEGER DEFAULT 0,
    duration_ms    INTEGER,
    status         TEXT NOT NULL,
    error_message  TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX idx_run_steps_run ON run_steps(run_id);
```

### 3.8 `test_cases`

User-uploaded or user-written test cases.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `tc_id` | TEXT | NOT NULL | Test case identifier (e.g. `TC-001`) |
| `name` | TEXT | NOT NULL | Test name / description |
| `file_path` | TEXT | NOT NULL | Relative path to pytest file in workspace |
| `function_name` | TEXT | | Pytest function name (e.g. `test_add_book`) |
| `linked_req_ids` | TEXT | DEFAULT '[]' | JSON array of linked REQ-IDs |
| `source` | TEXT | NOT NULL, DEFAULT 'user' | One of: `user`, `agent_proposed` |
| `status` | TEXT | NOT NULL, DEFAULT 'not_run' | One of: `not_run`, `passed`, `failed`, `error`, `skipped` |
| `created_at` | TEXT | NOT NULL | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE test_cases (
    id             TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tc_id          TEXT NOT NULL,
    name           TEXT NOT NULL,
    file_path      TEXT NOT NULL,
    function_name  TEXT,
    linked_req_ids TEXT DEFAULT '[]',
    source         TEXT NOT NULL DEFAULT 'user',
    status         TEXT NOT NULL DEFAULT 'not_run',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    UNIQUE(project_id, tc_id)
);

CREATE INDEX idx_test_cases_project ON test_cases(project_id);
```

### 3.9 `test_results`

Results from each pytest execution, per test case.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `run_id` | TEXT | NOT NULL, FK → runs.id | Parent run |
| `test_case_id` | TEXT | NOT NULL, FK → test_cases.id | Which test case |
| `tc_id` | TEXT | NOT NULL | Denormalized TC-ID for fast access |
| `iteration` | INTEGER | NOT NULL, DEFAULT 0 | Fix-loop iteration number (0 = first test) |
| `result` | TEXT | NOT NULL | One of: `passed`, `failed`, `error`, `skipped` |
| `duration_ms` | INTEGER | | Test execution time in milliseconds |
| `stdout` | TEXT | DEFAULT '' | Captured stdout |
| `stderr` | TEXT | DEFAULT '' | Captured stderr |
| `error_message` | TEXT | | Failure/error message from pytest |
| `created_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE test_results (
    id            TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    test_case_id  TEXT NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    tc_id         TEXT NOT NULL,
    iteration     INTEGER NOT NULL DEFAULT 0,
    result        TEXT NOT NULL,
    duration_ms   INTEGER,
    stdout        TEXT DEFAULT '',
    stderr        TEXT DEFAULT '',
    error_message TEXT,
    created_at    TEXT NOT NULL
);

CREATE INDEX idx_test_results_run ON test_results(run_id);
CREATE INDEX idx_test_results_tc ON test_results(test_case_id);
```

### 3.10 `bug_reports`

Structured bug reports generated by the Testing Agent.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `run_id` | TEXT | NOT NULL, FK → runs.id | Run that produced this bug |
| `bug_id` | TEXT | NOT NULL | Display ID (e.g. `B-001`) |
| `req_id` | TEXT | | Linked requirement ID |
| `tc_id` | TEXT | | Linked test case ID |
| `file_path` | TEXT | | File containing the bug |
| `function_name` | TEXT | | Function or class name |
| `severity` | TEXT | NOT NULL, DEFAULT 'medium' | One of: `critical`, `high`, `medium`, `low` |
| `expected_result` | TEXT | NOT NULL | What should happen |
| `actual_result` | TEXT | NOT NULL | What actually happened |
| `probable_cause` | TEXT | | LLM-generated probable cause |
| `iteration` | INTEGER | NOT NULL, DEFAULT 0 | Fix-loop iteration when found |
| `status` | TEXT | NOT NULL, DEFAULT 'open' | One of: `open`, `fixed`, `wont_fix`, `escalated` |
| `fix_description` | TEXT | | Description of applied fix |
| `created_at` | TEXT | NOT NULL | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE bug_reports (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    run_id          TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    bug_id          TEXT NOT NULL,
    req_id          TEXT,
    tc_id           TEXT,
    file_path       TEXT,
    function_name   TEXT,
    severity        TEXT NOT NULL DEFAULT 'medium',
    expected_result TEXT NOT NULL,
    actual_result   TEXT NOT NULL,
    probable_cause  TEXT,
    iteration       INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'open',
    fix_description TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE(project_id, bug_id)
);

CREATE INDEX idx_bugs_project ON bug_reports(project_id);
CREATE INDEX idx_bugs_run ON bug_reports(run_id);
```

### 3.11 `traceability_links`

Links between requirements, code symbols, test cases, and bugs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | UUID4 |
| `project_id` | TEXT | NOT NULL, FK → projects.id | Parent project |
| `req_id` | TEXT | | Requirement identifier |
| `code_chunk_id` | TEXT | | FK → code_chunks.id |
| `test_case_id` | TEXT | | FK → test_cases.id |
| `bug_report_id` | TEXT | | FK → bug_reports.id |
| `link_type` | TEXT | NOT NULL | One of: `req_to_code`, `req_to_test`, `test_to_bug`, `code_to_bug` |
| `created_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE traceability_links (
    id             TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    req_id         TEXT,
    code_chunk_id  TEXT REFERENCES code_chunks(id) ON DELETE SET NULL,
    test_case_id   TEXT REFERENCES test_cases(id) ON DELETE SET NULL,
    bug_report_id  TEXT REFERENCES bug_reports(id) ON DELETE SET NULL,
    link_type      TEXT NOT NULL,
    created_at     TEXT NOT NULL
);

CREATE INDEX idx_trace_project ON traceability_links(project_id);
CREATE INDEX idx_trace_req ON traceability_links(req_id);
```

### 3.12 `settings`

Runtime settings stored as key-value pairs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `key` | TEXT | PRIMARY KEY | Setting name |
| `value` | TEXT | NOT NULL | Setting value (JSON-encoded for complex values) |
| `updated_at` | TEXT | NOT NULL | ISO 8601 |

```sql
CREATE TABLE settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Default settings
INSERT INTO settings (key, value, updated_at) VALUES
    ('model_path', '"models/qwen2.5-coder-3b-instruct-q4_k_m.gguf"', datetime('now')),
    ('n_ctx', '4096', datetime('now')),
    ('n_threads', '4', datetime('now')),
    ('max_tokens', '2048', datetime('now')),
    ('temperature', '0.2', datetime('now')),
    ('iteration_limit', '5', datetime('now')),
    ('test_timeout', '60', datetime('now')),
    ('theme', '"system"', datetime('now'));
```

---

## 4. Chroma Collections

Chroma is used only for semantic (vector) search. Three collections:

| Collection | Document type | Metadata stored | Rebuild from |
|---|---|---|---|
| `requirements` | Requirement chunks | `chunk_id`, `project_id`, `req_id`, `document_id`, `heading` | `chunks` table |
| `code` | Code chunks | `chunk_id`, `project_id`, `file_path`, `symbol_name`, `symbol_type` | `code_chunks` table |
| `tests_bugs` | Test case text and bug report text | `item_id`, `project_id`, `item_type` (`test` or `bug`) | `test_cases` and `bug_reports` tables |

### 4.1 Embedding model

- **Model:** bge-small-en-v1.5 via fastembed (ONNX)
- **Dimension:** 384
- **Distance metric:** cosine

### 4.2 Rebuild procedure

If Chroma data is lost or corrupted:
1. Delete `data/chroma/`.
2. Read all chunks from `chunks` table → embed → insert into `requirements` collection.
3. Read all code chunks from `code_chunks` table → embed → insert into `code` collection.
4. Read all test cases and bug reports → embed → insert into `tests_bugs` collection.

---

## 5. Database Initialization

The `storage/db.py` module initializes the database on first run:

```python
def init_database(db_path: str):
    """Create all tables if they do not exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    # Execute all CREATE TABLE statements
    # Execute all CREATE INDEX statements
    # Execute all CREATE TRIGGER statements
    # Insert default settings if settings table is empty
    conn.commit()
    conn.close()
```

### 5.1 SQLite pragmas

```sql
PRAGMA journal_mode = WAL;     -- Better concurrency for reads during writes
PRAGMA foreign_keys = ON;      -- Enforce foreign key constraints
PRAGMA busy_timeout = 5000;    -- Wait up to 5 seconds for locks
```

---

## 6. Migration Strategy

For the first version, migrations are not needed. The database is created fresh on first run. If the schema changes during development, delete `data/ojas.db` and restart.

For future versions, a simple migration system can be added using a `schema_version` table and numbered SQL scripts.
