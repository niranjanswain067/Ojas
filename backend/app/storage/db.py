"""
Ojas database module.

Manages the SQLite database lifecycle:
- get_db_path()     → resolved path to data/ojas.db
- get_connection()  → open connection with WAL, FK, busy_timeout
- init_database()   → create all tables / indexes / triggers if absent
- execute_query()   → run a write query, return cursor
- fetch_one()       → return first row as dict or None
- fetch_all()       → return list of row dicts
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root and DB path
# ---------------------------------------------------------------------------

# This file lives at:  <root>/backend/app/storage/db.py
# So the project root is 3 levels up.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def get_db_path() -> str:
    """Return the absolute path to data/ojas.db as a string."""
    return str(_PROJECT_ROOT / "data" / "ojas.db")


# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Open and return a sqlite3.Connection with:
    - WAL journal mode (better read/write concurrency)
    - Foreign keys enforced
    - Busy timeout of 5 000 ms to wait for locks instead of raising immediately
    - Row factory set so rows behave like dicts
    """
    db_path = get_db_path()
    # Ensure the parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows accessible by column name

    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")

    return conn


# ---------------------------------------------------------------------------
# DDL — all CREATE TABLE / INDEX / TRIGGER / INSERT statements
# ---------------------------------------------------------------------------

_DDL_STATEMENTS: List[str] = [
    # ------------------------------------------------------------------
    # projects
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS projects (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT '',
        status      TEXT NOT NULL DEFAULT 'idle',
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    )
    """,

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS documents (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id)",

    # ------------------------------------------------------------------
    # chunks
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS chunks (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_project  ON chunks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_req_id   ON chunks(req_id)",

    # ------------------------------------------------------------------
    # chunks_fts  (FTS5 virtual table — content-backed)
    # ------------------------------------------------------------------
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        content,
        heading,
        req_id,
        content='chunks',
        content_rowid='rowid'
    )
    """,

    # FTS5 sync triggers
    """
    CREATE TRIGGER IF NOT EXISTS chunks_ai
    AFTER INSERT ON chunks BEGIN
        INSERT INTO chunks_fts(rowid, content, heading, req_id)
        VALUES (new.rowid, new.content, new.heading, new.req_id);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS chunks_ad
    AFTER DELETE ON chunks BEGIN
        INSERT INTO chunks_fts(chunks_fts, rowid, content, heading, req_id)
        VALUES ('delete', old.rowid, old.content, old.heading, old.req_id);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS chunks_au
    AFTER UPDATE ON chunks BEGIN
        INSERT INTO chunks_fts(chunks_fts, rowid, content, heading, req_id)
        VALUES ('delete', old.rowid, old.content, old.heading, old.req_id);
        INSERT INTO chunks_fts(rowid, content, heading, req_id)
        VALUES (new.rowid, new.content, new.heading, new.req_id);
    END
    """,

    # ------------------------------------------------------------------
    # code_chunks
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS code_chunks (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_code_chunks_project ON code_chunks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_code_chunks_file    ON code_chunks(project_id, file_path)",

    # ------------------------------------------------------------------
    # runs
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS runs (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_runs_status  ON runs(status)",

    # ------------------------------------------------------------------
    # run_steps
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS run_steps (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_run_steps_run ON run_steps(run_id)",

    # ------------------------------------------------------------------
    # test_cases
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS test_cases (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_test_cases_project ON test_cases(project_id)",

    # ------------------------------------------------------------------
    # test_results
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS test_results (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_test_results_run ON test_results(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_test_results_tc  ON test_results(test_case_id)",

    # ------------------------------------------------------------------
    # bug_reports
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS bug_reports (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_bugs_project ON bug_reports(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_bugs_run     ON bug_reports(run_id)",

    # ------------------------------------------------------------------
    # traceability_links
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS traceability_links (
        id             TEXT PRIMARY KEY,
        project_id     TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        req_id         TEXT,
        code_chunk_id  TEXT REFERENCES code_chunks(id) ON DELETE SET NULL,
        test_case_id   TEXT REFERENCES test_cases(id)  ON DELETE SET NULL,
        bug_report_id  TEXT REFERENCES bug_reports(id) ON DELETE SET NULL,
        link_type      TEXT NOT NULL,
        created_at     TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_trace_project ON traceability_links(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_trace_req     ON traceability_links(req_id)",

    # ------------------------------------------------------------------
    # settings  (key-value store)
    # ------------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
]

# Default rows to seed into the settings table (only if absent)
_DEFAULT_SETTINGS: List[Tuple[str, str]] = [
    ("model_path",       '"models/qwen2.5-coder-3b-instruct-q4_k_m.gguf"'),
    ("n_ctx",            "4096"),
    ("n_threads",        "4"),
    ("max_tokens",       "2048"),
    ("temperature",      "0.2"),
    ("iteration_limit",  "5"),
    ("test_timeout",     "60"),
    ("theme",            '"system"'),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_database() -> None:
    """
    Create all tables, indexes, and triggers in data/ojas.db if they do not
    already exist.  Seed the settings table with defaults where no row is
    present yet.  Safe to call on every startup (idempotent).
    """
    db_path = get_db_path()
    logger.info("Initialising database at %s", db_path)

    conn = get_connection()
    try:
        with conn:
            for stmt in _DDL_STATEMENTS:
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)

            # Seed default settings — INSERT OR IGNORE so existing rows are
            # never overwritten.
            now = _now_iso()
            for key, value in _DEFAULT_SETTINGS:
                conn.execute(
                    "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, value, now),
                )

        logger.info("Database initialised successfully.")
    except Exception:
        logger.exception("Failed to initialise database")
        raise
    finally:
        conn.close()


def execute_query(
    sql: str,
    params: Sequence[Any] = (),
) -> sqlite3.Cursor:
    """
    Execute a write query (INSERT / UPDATE / DELETE / PRAGMA …).
    Opens a fresh connection, runs the statement inside a transaction,
    commits, and returns the cursor (so callers can read lastrowid etc.).

    The connection is left open — the caller must close it if they need to,
    or just discard it (it will be closed by GC).  For most write helpers the
    auto-commit context manager inside the `with conn` block is sufficient.
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(sql, params)
        return cur
    except Exception:
        logger.exception("execute_query failed.\nSQL: %s\nParams: %s", sql, params)
        raise
    finally:
        conn.close()


def fetch_one(
    sql: str,
    params: Sequence[Any] = (),
) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT and return the first row as a plain dict, or None.
    """
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row is not None else None
    except Exception:
        logger.exception("fetch_one failed.\nSQL: %s\nParams: %s", sql, params)
        raise
    finally:
        conn.close()


def fetch_all(
    sql: str,
    params: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    """
    Execute a SELECT and return all rows as a list of plain dicts.
    """
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    except Exception:
        logger.exception("fetch_all failed.\nSQL: %s\nParams: %s", sql, params)
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string (no microseconds)."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

