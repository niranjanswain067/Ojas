# Ojas: Project Requirement Documentation

| Item | Detail |
|---|---|
| Project | Ojas, an offline AI-powered software development and testing platform |
| Document | Software Requirements Specification (SRS) |
| Stage | Research and development |
| Team | 4 members, 40-day schedule (22 Oct to 30 Nov 2026) |
| Related documents | 02_System_Architecture.md, 03_UI_Design.md, 04_Technology_Stack.md |

---

## 1. Introduction

### 1.1 Purpose
This document defines what Ojas must do and the limits within which it must work. It is the reference for design, implementation and testing.

### 1.2 Product summary
Ojas runs a locally hosted, quantized LLM on the user's own machine. Two role-separated agents share that model:

- **Development Agent** reads requirement documents and a prompt, plans the project, and generates or fixes source code.
- **Testing Agent** validates the generated project against the requirements and user-written test cases, using real test execution, and records bugs in structured reports.

The user works through a browser-based interface with a code editor (React.js and Monaco Editor) on top of a FastAPI backend. Nothing leaves the user's machine.

### 1.3 Problem statement
- Requirement documents are long and read differently by developers and testers.
- Testing happens late, and the report, fix and re-test cycle is manual.
- Most AI coding assistants are cloud-hosted, so they need internet, cost money and expose proprietary code.
- Most AI tools generate code but do not independently validate it against the requirements.

### 1.4 Objectives
1. Run a full develop, test, fix and re-test cycle offline on one local machine.
2. Keep construction (Development Agent) and validation (Testing Agent) as separate roles.
3. Ground generation and testing in the user's own documents through retrieval.
4. Base pass or fail on real test execution, not on model prediction.
5. Keep traceability from requirement to code to test to bug report.
6. Stay usable on a CPU-only machine.

### 1.5 Scope

**In scope**
- Upload and indexing of requirement documents (docx, pdf, txt).
- Requirement analysis, architecture and development plan generation.
- Code generation and modification (Python projects first).
- User-supplied test cases, test execution with pytest, bug reports, consolidated test report.
- Automatic fix loop with stop rules and user escalation.
- Browser UI with code editor, file tree, run controls, logs and reports.
- Project history, logs and reports stored locally.

**Out of scope**
- Cloud LLM APIs and any internet use at run time.
- Multi-user accounts, authentication, remote access and production deployment.
- GPU-specific optimization.
- Languages other than Python in the first version.
- OCR of scanned documents (optional, only if time allows; see FR-45).

### 1.6 Definitions

| Term | Meaning |
|---|---|
| LLM | Large Language Model |
| Quantization | Storing model weights at lower precision to reduce size and memory |
| GGUF | Model file format used by llama.cpp |
| RAG | Retrieval-Augmented Generation: adding retrieved passages to the prompt |
| REQ-ID | Identifier of a requirement chunk |
| TC-ID | Identifier of a test case |
| Fix loop | Repeated cycle of test, bug report, fix and re-test |

---

## 2. Stakeholders and Users

| User | Description | Main needs |
|---|---|---|
| Student or developer | Builds a small project from a requirement document | Fast first version, clear plan, editable code |
| Tester | Writes test cases and checks results | Reliable pass or fail, traceable bug reports |
| Reviewer or supervisor | Reads the outcome | Logs, reports and requirement coverage |

There is one user role (local user) in this version.

---

## 3. Operating Environment and Constraints

| ID | Constraint |
|---|---|
| C-01 | Runs offline after one-time setup. No outbound network call at run time. |
| C-02 | CPU-only execution. No GPU is required or assumed. |
| C-03 | LLM is a quantized GGUF model (default Qwen2.5-Coder-3B-Instruct, Q4_K_M) run locally. |
| C-04 | Backend in Python 3.10+ with FastAPI. Frontend in React.js with Monaco Editor. |
| C-05 | Servers bind to 127.0.0.1 only. |
| C-06 | All data (documents, code, indexes, logs, reports) stays in the project folder. |
| C-07 | Minimum target machine: 8 GB RAM (16 GB recommended) and a multi-core x64 CPU. To be confirmed. |
| C-08 | Delivery within 40 days by a team of 4. |

---

## 4. Functional Requirements

Priority: **M** = must, **S** = should, **C** = could.

### 4.1 Project management

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The user can create, open, rename and delete a project. | M |
| FR-02 | Each project has its own documents, workspace, index, logs and reports. | M |
| FR-03 | The user can see the status of a project (idle, indexing, developing, testing, done, failed). | M |
| FR-04 | The user can see a history of runs with time, type and result. | S |

### 4.2 Document ingestion and indexing

| ID | Requirement | Priority |
|---|---|---|
| FR-10 | The user can upload requirement, specification and architecture documents in docx, pdf and txt. | M |
| FR-11 | The system splits documents into chunks, one requirement per chunk, each with a REQ-ID. | M |
| FR-12 | The system indexes chunks for semantic search (embeddings) and keyword search (BM25). | M |
| FR-13 | Files with an unchanged hash are not re-indexed. Changed files replace only their own chunks. | M |
| FR-14 | The user can view the list of indexed documents and their requirement chunks. | S |
| FR-15 | The user can edit or add a requirement chunk manually, and it is re-indexed. | C |

### 4.3 Development Agent

| ID | Requirement | Priority |
|---|---|---|
| FR-20 | The user can submit a prompt together with the indexed documents. | M |
| FR-21 | The agent produces a requirement analysis and a development plan (modules, files, order). | M |
| FR-22 | The agent generates source code and supporting files one file or function at a time. | M |
| FR-23 | Every generated Python file is checked with `ast.parse` and ruff. Errors are fed back to the agent. | M |
| FR-24 | Generated files are written to the project workspace and shown in the file tree. | M |
| FR-25 | The agent can modify or debug existing code from a bug report or a revised requirement. | M |
| FR-26 | The user can approve or reject each generated or changed file in a diff view before it is accepted. | S |
| FR-27 | The user can stop a running generation. | M |
| FR-28 | The plan is shown to the user before code generation starts, and the user can edit it. | S |

### 4.4 Testing Agent

| ID | Requirement | Priority |
|---|---|---|
| FR-30 | The user can upload or write test cases (pytest files or structured test-case text), each with a TC-ID. | M |
| FR-31 | The Testing Agent loads requirements and test cases and analyzes the generated project. | M |
| FR-32 | Tests are executed with pytest in a restricted working directory with a timeout. | M |
| FR-33 | Pass or fail is taken from real execution results, never from the LLM. | M |
| FR-34 | Each failure produces a structured bug report: bug ID, REQ-ID, TC-ID, file and function, expected result, actual result, probable cause, severity. | M |
| FR-35 | The agent can detect runtime errors and mismatches between implementation and requirements. | M |
| FR-36 | The agent may propose additional test cases from the requirements, which the user can accept or discard. | C |

### 4.5 Fix loop

| ID | Requirement | Priority |
|---|---|---|
| FR-40 | Bug reports are returned to the Development Agent, which fixes only the failing function using the error and the linked requirement. | M |
| FR-41 | After each fix the project is re-checked statically and re-tested. | M |
| FR-42 | The loop stops when all tests pass, when the iteration limit is reached (default 5), or when the same failure repeats twice. | M |
| FR-43 | When the loop stops without success, it is escalated to the user with the last bug report. | M |
| FR-44 | The user can start, pause, stop and resume the loop. | S |
| FR-45 | OCR for scanned documents (PaddleOCR) feeds the ingestion step. Only if schedule allows. | C |

### 4.6 Editor and workspace

| ID | Requirement | Priority |
|---|---|---|
| FR-50 | The UI shows a file tree and an editor (Monaco) with syntax highlighting for the workspace. | M |
| FR-51 | The user can open, edit, save, create, rename and delete workspace files. | M |
| FR-52 | The editor can show a diff between the previous and the new version of a file. | S |
| FR-53 | The user can see which requirement a function implements (REQ-ID link). | S |

### 4.7 Progress, logs and reports

| ID | Requirement | Priority |
|---|---|---|
| FR-60 | The UI shows live progress of long-running tasks (stage, current file, iteration). | M |
| FR-61 | Model output can be streamed to the UI as it is generated. | S |
| FR-62 | Application and model logs (requests, errors, load time, generation time) are saved and viewable. | M |
| FR-63 | The system produces a development summary, bug reports, pytest results and a consolidated test report. | M |
| FR-64 | The consolidated report shows requirement coverage: which requirements have tests and which tests passed. | S |
| FR-65 | Reports can be downloaded as Markdown, and optionally as PDF or Word. | S |

### 4.8 Settings

| ID | Requirement | Priority |
|---|---|---|
| FR-70 | The user can view and change model path, context size, threads, max tokens, temperature and iteration limit. | S |
| FR-71 | The user can switch to another GGUF model through configuration without code changes. | S |
| FR-72 | A health page shows whether the model is loaded and which paths are in use. | S |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Offline | No feature may need internet at run time. UI assets, fonts, Monaco and models are bundled locally. |
| NFR-02 | Privacy | No telemetry. Data stays on disk in the project folder. |
| NFR-03 | Performance | Model loads once at start-up. Retrieval returns results in under 2 seconds on the target machine. Generation speed is measured, not promised (estimate 10 to 20 tokens per second). |
| NFR-04 | Responsiveness | The UI never blocks during model work. Long tasks run in the background and report progress. |
| NFR-05 | Reliability | One generation at a time. A failed task leaves the workspace in a consistent state. Stop rules prevent endless loops. |
| NFR-06 | Safety | Generated code runs only in a restricted folder with a timeout. |
| NFR-07 | Usability | A new user can create a project, upload a document and start generation without reading a manual. |
| NFR-08 | Maintainability | Model, retrieval, agents and API are separate modules behind interfaces. Settings live in config files. |
| NFR-09 | Portability | Runs on Windows with start.bat. The virtual environment must be rebuildable from requirements.txt. |
| NFR-10 | Traceability | Requirements, code symbols, test cases, results and bugs are linked by IDs and stored. |
| NFR-11 | Auditability | Every run records inputs, model settings, steps and outputs. |
| NFR-12 | Accuracy | The Testing Agent never accepts the Development Agent's output without running tests. |

---

## 6. External Interfaces

| Interface | Description |
|---|---|
| User interface | React.js single-page application with Monaco Editor, served locally. |
| REST API | FastAPI endpoints under `/api` for projects, documents, runs, files and reports. |
| Event stream | Server-Sent Events for progress and streamed model output. |
| Model interface | Internal `LLMClient` wrapper over llama.cpp; no external network. |
| File system | Project folder with `workspace/`, `logs/`, `reports/`, `models/`, `config/`. |

---

## 7. Data Requirements

| Data | Content | Storage |
|---|---|---|
| Documents | Uploaded requirement files | Project folder |
| Chunks | Text, REQ-ID, hash, links | SQLite (source of truth) |
| Vectors | Embeddings and metadata | Chroma (rebuildable from SQLite) |
| Workspace files | Generated and edited code | `workspace/` |
| Runs | Type, time, status, iterations, result | SQLite |
| Bugs and test results | Bug reports, TC-ID results | SQLite and `reports/` |
| Logs | Requests, errors, timings | `logs/` |

---

## 8. Key Use Cases

### UC-1: Generate a project from requirements
1. User creates a project and uploads documents.
2. System indexes them.
3. User enters a prompt and starts the Development Agent.
4. System shows the plan; user confirms.
5. System generates files, runs static checks, and shows the code in the editor.

### UC-2: Test and fix
1. User uploads test cases.
2. User starts the Testing Agent.
3. System runs pytest and shows results and bug reports.
4. User starts the fix loop (or it continues automatically).
5. System stops on success, on the iteration limit, or on a repeated failure.

### UC-3: Review results
1. User opens the report page.
2. User sees requirement coverage, pass or fail per test, bug history and logs.
3. User downloads the consolidated test report.

---

## 9. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-1 | From a clean machine with the setup done, the platform starts with `start.bat` and works with the network disabled. |
| AC-2 | A sample requirement document is indexed and a query returns the relevant requirement chunks. |
| AC-3 | The Development Agent produces a runnable sample project that passes `ast.parse` and ruff. |
| AC-4 | The Testing Agent runs user test cases with pytest and produces structured bug reports with REQ-ID and TC-ID. |
| AC-5 | The fix loop ends by one of its three stop rules on every run. |
| AC-6 | At least 2 of 3 sample projects reach all-tests-passing without manual code edits (target, to be confirmed after evaluation). |
| AC-7 | The consolidated test report lists requirement coverage and results. |
| AC-8 | Measurements are recorded: tokens per second, time per stage, peak RAM, loop iterations, Recall@k and MRR. |

---

## 10. Assumptions and Open Points

**Assumptions used in these documents**
- The LLM runs in the backend process through llama-cpp-python, behind a small `LLMClient` interface, so llama-server can replace it later.
- The first version targets Python projects only.
- The UI is a React single-page application served by FastAPI as static files, so Node.js is needed only to build the frontend.
- One local user, no login.

**Open points to confirm**
- Target hardware (8 GB or 16 GB RAM; CPU model).
- Fallback model if 3B quality is too low (7B is the planned fallback).
- Whether OCR is attempted in this version.
- Licence of the chosen model.
