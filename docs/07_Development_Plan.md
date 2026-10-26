# Ojas: Development Plan

| Item | Detail |
|---|---|
| Related documents | All project documents (01 through 06) |
| Duration | 40 days (22 Oct – 30 Nov 2026) |
| Team size | 4 members |
| Methodology | Sprint-based, 5-day sprints (8 sprints total) |

---

## 1. Team Roles

| Member | Primary Role | Secondary Role |
|---|---|---|
| **Member 1** | Backend Lead (FastAPI, orchestrator, agents) | DevOps (setup, start.bat) |
| **Member 2** | AI/ML Lead (LLM, RAG, embeddings, prompts) | Backend support |
| **Member 3** | Frontend Lead (React, Monaco, UI components) | Testing support |
| **Member 4** | Quality Lead (testing, validation, bug reports) | Backend support, documentation |

All members participate in integration, testing, and bug fixing in the final sprints.

---

## 2. Sprint Overview

| Sprint | Dates | Focus | Milestone |
|---|---|---|---|
| **Sprint 0** | Oct 22 – 26 | Setup, scaffolding, model verification | ✅ Dev environment working, model loads |
| **Sprint 1** | Oct 27 – 31 | Core backend + basic frontend shell | ✅ Project CRUD, file API, UI shell with routing |
| **Sprint 2** | Nov 01 – 05 | Document ingestion + RAG pipeline | ✅ Upload → parse → chunk → embed → search works |
| **Sprint 3** | Nov 06 – 10 | Development Agent + code generation | ✅ Plan + code generation from requirements |
| **Sprint 4** | Nov 11 – 15 | Testing Agent + validation | ✅ pytest execution + bug reports from failures |
| **Sprint 5** | Nov 16 – 20 | Fix loop + orchestrator + Monaco editor | ✅ Full develop → test → fix cycle end-to-end |
| **Sprint 6** | Nov 21 – 25 | Reports, settings, polish, SSE streaming | ✅ Consolidated report, settings page, live progress |
| **Sprint 7** | Nov 26 – 30 | Integration testing, bug fixes, demo prep | ✅ Acceptance criteria met, demo-ready |

---

## 3. Detailed Sprint Plans

### Sprint 0: Setup and Scaffolding (Oct 22 – 26)

**Goal:** Every team member has a working dev environment and can run the platform.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| Create project folder structure per architecture doc | Member 1 | M | Folder tree created |
| Set up Python venv and `requirements.txt` | Member 1 | M | `runtime/venv` working |
| Install and test llama-cpp-python with GGUF model | Member 2 | M | Model loads, generates text |
| Download and test embedding model (bge-small-en-v1.5) | Member 2 | M | Embeddings generated |
| Scaffold FastAPI app (`main.py`, routers, health endpoint) | Member 1 | M | `GET /api/health` returns 200 |
| Scaffold React app with Vite, install dependencies | Member 3 | M | `npm run dev` serves blank app |
| Configure Monaco Editor to load offline (no CDN) | Member 3 | M | Monaco renders in browser |
| Set up SQLite database initialization (`storage/db.py`) | Member 4 | M | All tables created on first run |
| Create `start.bat` launcher | Member 1 | S | Double-click starts Uvicorn |
| Set up Git repo, `.gitignore`, README | Member 4 | M | Repo initialized |
| Benchmark: measure tokens/second with llama-bench | Member 2 | S | Performance baseline recorded |

**Sprint 0 Milestone:** `start.bat` launches the backend, health endpoint returns model status, frontend shows a blank page with navigation.

---

### Sprint 1: Core Backend + Frontend Shell (Oct 27 – 31)

**Goal:** Project management works end-to-end. UI has working navigation and layout.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Backend** | | | |
| Projects API (CRUD): `GET/POST/PATCH/DELETE /api/projects` | Member 1 | M | All project endpoints working |
| Pydantic schemas for projects | Member 1 | M | Request/response validation |
| Files API: `GET/PUT/DELETE /api/projects/{id}/files/{path}` | Member 1 | M | Workspace file operations |
| Path safety: reject paths escaping workspace | Member 1 | M | Security check |
| SQLite storage layer (`storage/db.py`, `storage/files.py`) | Member 4 | M | DB access functions |
| Config loader (`config/settings.py`) | Member 4 | S | Settings from file or defaults |
| **Frontend** | | | |
| App shell: top nav, routing (Projects, Workspace, Reports, Settings) | Member 3 | M | Navigation works |
| Projects page: list, create, delete projects | Member 3 | M | Project CRUD via UI |
| API client: typed fetch wrappers | Member 3 | M | Frontend ↔ backend connected |
| Basic Workspace layout: sidebar + editor + right panel + bottom panel | Member 3 | M | Layout structure visible |
| File tree component: browse workspace files | Member 3 | S | Tree renders from API |
| **AI** | | | |
| `LLMClient` interface and llama-cpp implementation | Member 2 | M | `generate()` and `stream()` work |
| Generation lock (one at a time) | Member 2 | M | Concurrent requests blocked |

**Sprint 1 Milestone:** User can create a project, see it listed, open it, browse workspace files in the tree, open a file in Monaco editor.

---

### Sprint 2: Document Ingestion + RAG (Nov 01 – 05)

**Goal:** Documents can be uploaded, parsed, chunked, embedded, and searched.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **RAG Pipeline** | | | |
| Document parser: `python-docx`, `pypdf`, plain text (`rag/parser.py`) | Member 2 | M | Extracts text from all 3 formats |
| Chunker: split into requirement chunks with REQ-IDs (`rag/chunker.py`) | Member 2 | M | ~250-400 token chunks with IDs |
| Embedder: fastembed with bge-small-en-v1.5 (`rag/embedder.py`) | Member 2 | M | Vectors generated |
| Index manager: Chroma + SQLite upsert (`rag/index.py`) | Member 2 | M | Chunks stored in both stores |
| Search: semantic (Chroma) + keyword (FTS5) + RRF merge (`rag/search.py`) | Member 2 | M | Top-k chunks returned |
| Hash-based change detection: skip unchanged docs | Member 2 | M | Re-index only changed files |
| **Backend** | | | |
| Documents API: upload, list, delete | Member 1 | M | `POST/GET/DELETE` endpoints |
| Index API: trigger indexing | Member 1 | M | `POST /api/projects/{id}/index` |
| Requirements API: list chunks with REQ-IDs | Member 1 | S | `GET /api/projects/{id}/requirements` |
| Background task manager (`tasks/`) | Member 1 | M | Indexing runs in background |
| Event bus (`events/`) | Member 1 | M | Events published internally |
| **Frontend** | | | |
| Documents panel: upload area (drag & drop), document list | Member 3 | M | Upload and status display |
| Requirements list: show REQ-IDs and snippets | Member 3 | S | Expandable requirement chunks |
| **Testing** | | | |
| Test RAG accuracy: Recall@k, MRR on sample documents | Member 4 | S | Baseline retrieval metrics |

**Sprint 2 Milestone:** Upload a PDF → system parses, chunks, embeds → query returns relevant requirement chunks.

---

### Sprint 3: Development Agent + Code Generation (Nov 06 – 10)

**Goal:** The Development Agent generates a plan and code from requirements.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Agents** | | | |
| Prompt templates for: requirement analysis, plan, code generation (`agents/prompts/`) | Member 2 | M | Tested prompt templates |
| Development Agent: plan generation (`agents/development_agent.py`) | Member 2 | M | Generates structured plan |
| Development Agent: file-by-file code generation | Member 2 | M | Generates Python files |
| Prompt builder: retrieve chunks → build context → format prompt | Member 2 | M | Short, focused prompts |
| Code output parser: extract code blocks from LLM response | Member 2 | M | Clean code extraction |
| **Validation** | | | |
| Static checker: `ast.parse` + ruff (`validation/static_check.py`) | Member 4 | M | Syntax and lint check |
| Error feedback: send errors back to LLM for self-correction | Member 2 | M | Auto-fix syntax errors |
| **Backend** | | | |
| Runs API: start plan/develop run (`POST /api/projects/{id}/runs`) | Member 1 | M | Run creation and status |
| Orchestrator: plan → generate → static check flow (`orchestrator.py`) | Member 1 | M | State machine works |
| SSE endpoint: stream progress events (`GET /api/runs/{id}/events`) | Member 1 | M | Live events to frontend |
| Code chunk indexing: `ast`-based code splitting into `code_chunks` | Member 4 | S | Code searchable in Chroma |
| **Frontend** | | | |
| Run panel: prompt box, Plan/Develop buttons, progress display | Member 3 | M | Start runs from UI |
| Plan review: show plan text, edit, approve | Member 3 | S | User confirms plan |
| SSE listener: update UI from progress events | Member 3 | M | Live progress in UI |
| Stage stepper component | Member 3 | S | Visual stage indicator |

**Sprint 3 Milestone:** Enter a prompt → Development Agent generates a plan → user approves → code files generated and shown in editor.

---

### Sprint 4: Testing Agent + Validation (Nov 11 – 15)

**Goal:** Tests execute with pytest, failures produce structured bug reports.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Testing Agent** | | | |
| Testing Agent: load requirements + test cases + code (`agents/testing_agent.py`) | Member 2 | M | Agent analyzes project |
| Test runner: pytest subprocess with timeout (`validation/test_runner.py`) | Member 4 | M | pytest runs in workspace |
| pytest XML report parser | Member 4 | M | Results extracted from XML |
| Bug report generator: LLM fills structured fields | Member 2 | M | Bug reports with REQ-ID, TC-ID |
| Bug report template and prompt | Member 2 | M | Consistent bug format |
| **Backend** | | | |
| Tests API: upload/save test cases | Member 1 | M | `POST /api/projects/{id}/tests` |
| Bugs API: list bug reports | Member 1 | M | `GET /api/projects/{id}/bugs` |
| Orchestrator: test flow integration | Member 1 | M | Test stage in state machine |
| Test results storage in SQLite | Member 4 | M | Results persisted per run |
| **Frontend** | | | |
| Tests panel: list test cases, upload tests | Member 3 | M | Test management in sidebar |
| Test results table in bottom panel | Member 3 | M | TC-ID, result, duration |
| Bug reports list in bottom panel | Member 3 | M | Bug details with links |
| Diff view for generated changes (Monaco DiffEditor) | Member 3 | M | Accept/Reject buttons |

**Sprint 4 Milestone:** Upload test cases → Testing Agent runs pytest → test results and bug reports shown in UI.

---

### Sprint 5: Fix Loop + Orchestrator + Editor Polish (Nov 16 – 20)

**Goal:** Full automated develop → test → fix → re-test cycle works end-to-end.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Fix Loop** | | | |
| Fix loop controller in orchestrator | Member 1 | M | Loop runs automatically |
| Stop rule 1: all tests pass → success | Member 1 | M | Clean exit |
| Stop rule 2: iteration limit reached | Member 1 | M | Stop and report |
| Stop rule 3: same failure repeats → escalate | Member 1 | M | Escalation to user |
| Development Agent: fix from bug report | Member 2 | M | Targeted function fixes |
| Re-test after each fix | Member 4 | M | pytest re-runs |
| **Backend** | | | |
| Run cancellation: `POST /api/runs/{id}/cancel` | Member 1 | M | Stop running task |
| Traceability links in SQLite | Member 4 | S | REQ → code → test → bug |
| Run history with results | Member 1 | S | `GET /api/projects/{id}/runs` |
| **Frontend** | | | |
| Fix loop progress: iteration counter, failing function, diff | Member 3 | M | Live fix loop in UI |
| Escalation message with bug report and code link | Member 3 | M | User notified |
| Monaco editor polish: read-only during generation, banner | Member 3 | S | Editor states |
| File tree: badges for generated/pending files | Member 3 | S | Visual indicators |
| **End-to-end** | | | |
| Test with sample project: requirements → code → test → fix | All | M | Full cycle works |

**Sprint 5 Milestone:** Full end-to-end cycle: upload requirements → generate code → run tests → fix failures → re-test → done/escalate.

---

### Sprint 6: Reports, Settings, Polish (Nov 21 – 25)

**Goal:** Reports page complete, settings working, SSE streaming, UI polish.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Reports** | | | |
| Report writer: development plan, bug reports, test results (`storage/reports.py`) | Member 4 | M | Reports as Markdown files |
| Consolidated test report with requirement coverage | Member 4 | M | Coverage table generated |
| Reports API: list and download | Member 1 | M | Reports endpoint working |
| **Settings** | | | |
| Settings API: GET/PUT with model reload | Member 1 | S | Settings endpoint |
| Settings page in frontend | Member 3 | S | Settings form |
| Health card component | Member 3 | S | Model status display |
| **Streaming** | | | |
| Token streaming from LLM to UI | Member 2 | S | Live model output |
| Model output tab in bottom panel | Member 3 | S | Streamed text display |
| **Frontend polish** | | | |
| Reports page: summary, coverage table, tabs, download | Member 3 | M | Reports viewable |
| Requirement badges on code (REQ-ID links) | Member 3 | S | Click REQ-ID → requirement |
| Dark/light theme toggle | Member 3 | S | Theme switching |
| Loading states, empty states, error handling | Member 3 | M | Professional UX |
| Log view: auto-scroll, pause, timestamps | Member 3 | S | Usable log panel |

**Sprint 6 Milestone:** Reports page shows requirement coverage. Settings page works. UI is polished with proper loading/error states.

---

### Sprint 7: Integration Testing + Demo Prep (Nov 26 – 30)

**Goal:** All acceptance criteria met. Platform is demo-ready.

| Task | Owner | Priority | Deliverable |
|---|---|---|---|
| **Testing** | | | |
| Test with 3 sample projects end-to-end | All | M | AC-6: 2/3 pass without manual edits |
| Offline test: disable network, run full cycle | Member 1 | M | AC-1: works offline |
| Verify all acceptance criteria (AC-1 through AC-8) | Member 4 | M | Checklist complete |
| Record measurements: tokens/s, time/stage, RAM, iterations | Member 2 | M | AC-8: metrics recorded |
| **Bug fixes** | | | |
| Fix bugs found in integration testing | All | M | Stability |
| Edge cases: large documents, empty tests, cancel during run | All | S | Robustness |
| **Documentation** | | | |
| Update README with setup and usage instructions | Member 4 | M | User can set up from README |
| Final `start.bat` testing on clean machine | Member 1 | M | Clean setup works |
| **Demo** | | | |
| Prepare demo scenario with sample project | Member 4 | S | Demo script ready |
| Record demo video (optional) | Member 3 | C | Video walkthrough |

**Sprint 7 Milestone:** All acceptance criteria verified. Platform starts from `start.bat`, works offline, generates code, runs tests, produces reports.

---

## 4. Acceptance Criteria Checklist

| # | Criterion | Sprint | Owner |
|---|---|---|---|
| AC-1 | Starts with `start.bat`, works offline | Sprint 7 | Member 1 |
| AC-2 | Sample document indexed, query returns relevant chunks | Sprint 2 | Member 2 |
| AC-3 | Development Agent produces runnable code (ast + ruff pass) | Sprint 3 | Member 2 |
| AC-4 | Testing Agent runs pytest, produces bug reports with REQ-ID/TC-ID | Sprint 4 | Member 4 |
| AC-5 | Fix loop ends by one of three stop rules | Sprint 5 | Member 1 |
| AC-6 | 2/3 sample projects pass all tests without manual edits | Sprint 7 | All |
| AC-7 | Consolidated report shows requirement coverage | Sprint 6 | Member 4 |
| AC-8 | Metrics recorded: tokens/s, time/stage, RAM, iterations, Recall@k, MRR | Sprint 7 | Member 2 |

---

## 5. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| 3B model quality too low | Code doesn't compile or pass tests | Medium | Fall back to 7B model; improve prompts; accept more iterations |
| CPU generation too slow | Development takes 10+ minutes per file | Medium | Shorter prompts, smaller context, generate less code per call |
| RAG retrieval misses key requirements | Agent generates wrong code | Medium | Tune chunk size, test with real docs, adjust top-k |
| llama-cpp-python installation issues on team machines | Setup blocked | Low | Pre-built wheels; document exact versions; share working venv |
| Monaco offline config complexity | Editor doesn't load | Low | Test offline mode in Sprint 0; fall back to CodeMirror if needed |
| Team member unavailable | Sprint delayed | Low | Cross-train on critical paths; documented code |
| Scope creep (OCR, PDF export, etc.) | Schedule overrun | Medium | Strict "Could" priority; defer to post-v1 |

---

## 6. Definition of Done

A task is done when:
1. Code is committed and passes ruff checks.
2. Related API endpoints return expected responses.
3. UI components render correctly and handle error states.
4. At least one happy-path test exists (manual or automated).
5. Documentation is updated if behaviour changes.

---

## 7. Communication

- **Daily standup:** 15 minutes, what's done, what's next, blockers.
- **Sprint review:** End of each sprint, demo the milestone.
- **Sprint planning:** First day of each sprint, assign tasks.
- **Code reviews:** All code merged via pull request with at least one reviewer.
