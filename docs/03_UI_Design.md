# Ojas: UI Design

| Item | Detail |
|---|---|
| Related documents | 01_Project_Requirement_Documentation.md, 02_System_Architecture.md, 04_Technology_Stack.md |
| Framework | React.js (single-page app, built with Vite) |
| Code editor | Monaco Editor |
| Backend | FastAPI over REST and Server-Sent Events |

---

## 1. Design Goals

1. **Familiar like an IDE.** File tree on the left, editor in the centre, panels around it.
2. **Honest about slowness.** Model work on a CPU takes seconds to minutes, so the UI always shows what is happening.
3. **Human in control.** The user can review a plan, approve or reject generated changes, stop a run, and edit code.
4. **Traceable.** Requirements, code, tests and bugs are linked and one click apart.
5. **Fully offline.** No CDN, no web fonts, no remote icons.
6. **Simple.** One user, no login, few screens.

---

## 2. Users and Main Tasks

| Task | Where |
|---|---|
| Create or open a project | Projects page |
| Upload requirement documents | Workspace → Documents |
| Enter a prompt and start development | Workspace → Run panel |
| Review the plan and generated code | Workspace → Editor and diff |
| Upload or write test cases | Workspace → Tests |
| Run tests and the fix loop | Workspace → Run panel |
| Read bugs and the final report | Reports page |
| Change model settings | Settings page |

---

## 3. Information Architecture

```
Ojas
|-- Projects            list, create, open
|-- Workspace           (per project)
|     |-- Documents     uploaded files, indexed requirements
|     |-- Code          file tree + Monaco editor
|     |-- Tests         test cases and results
|     `-- Run           prompt, controls, progress
|-- Reports             plan, bugs, test results, consolidated report
`-- Settings            model and runtime settings, health
```

Top navigation: **Projects | Workspace | Reports | Settings**, with a status chip showing the model state (Loading, Ready, Busy).

---

## 4. Screens

### 4.1 Projects page

Purpose: list projects and start a new one.

```
+------------------------------------------------------------------+
| Ojas        Projects | Workspace | Reports | Settings   [Model: Ready] |
+------------------------------------------------------------------+
|  Projects                                        [ + New project ] |
|  +----------------------+  +----------------------+               |
|  | Library System       |  | Billing Module       |               |
|  | Status: Done         |  | Status: Testing      |               |
|  | Updated 21 Oct       |  | Updated 20 Oct       |               |
|  | [Open]  [Delete]     |  | [Open]  [Delete]     |               |
|  +----------------------+  +----------------------+               |
+------------------------------------------------------------------+
```

- Card shows name, status chip, last updated, requirement count and last test result.
- New project dialog: name and optional description.
- Delete asks for confirmation.

### 4.2 Workspace page (main screen)

Four regions: left sidebar, centre editor, right run panel, bottom panel.

```
+------------------------------------------------------------------------------+
| Ojas   Projects | Workspace | Reports | Settings            [Model: Ready]   |
+--------------+-----------------------------------------+---------------------+
| SIDEBAR      | EDITOR TABS:  app.py x  models.py x     | RUN PANEL           |
| [Docs][Code] +-----------------------------------------+ Prompt:             |
| [Tests]      |                                         | +-----------------+ |
|              |   Monaco Editor                         | | Build a library | |
| Files        |   (code or diff view)                   | | system ...      | |
| v workspace  |                                         | +-----------------+ |
|   v app      |                                         | [Plan] [Develop]    |
|     app.py   |                                         | [Test] [Fix loop]   |
|     models.py|                                         |                     |
|   > tests    |                                         | Stage: Generating   |
|              |                                         | File: models.py     |
|              |                                         | Iteration: 2 / 5    |
|              |                                         | [Stop]              |
+--------------+-----------------------------------------+---------------------+
| BOTTOM PANEL:  Logs | Test results | Bug reports | Model output              |
| 10:42 generated models.py (ast ok, ruff ok)                                  |
+------------------------------------------------------------------------------+
```

#### Left sidebar (three tabs)

| Tab | Content |
|---|---|
| Docs | Upload area (drag and drop), list of documents with indexing status, expandable list of requirement chunks (REQ-ID, heading, snippet). Click a requirement to see linked code and tests |
| Code | File tree of `workspace/` with create, rename, delete. Icons for changed or generated files. Badge for files waiting for approval |
| Tests | List of test cases with TC-ID and last result (pass, fail, not run). Add or upload tests |

#### Centre: Monaco editor

- Tabbed multi-file editing with syntax highlighting (Python first), line numbers and minimap off by default.
- **Edit mode:** user edits and saves with Ctrl+S.
- **Diff mode:** Monaco DiffEditor shows old vs new for a generated or fixed file, with **Accept** and **Reject** buttons above it.
- **Requirement hints:** a small REQ-ID label above each function that implements a requirement (from the REQ-ID link). Clicking it opens the requirement.
- **Read-only while generating** the same file, with a "Model is writing this file" banner.
- Light and dark editor themes follow the app theme.

#### Right: Run panel

| Element | Behaviour |
|---|---|
| Prompt box | Multi-line text for the task or change request |
| Buttons | **Plan**, **Develop**, **Test**, **Fix loop** (Run all). Only valid buttons are enabled |
| Status block | Current stage, current file, iteration (n / limit), elapsed time |
| Stage stepper | Index → Plan → Generate → Static check → Test → Fix → Done |
| Stop | Stops the running task. Shows "Stopping…" until the backend confirms |
| Plan review | After **Plan**, the plan appears as editable text with **Approve and generate** |

#### Bottom panel (tabs)

| Tab | Content |
|---|---|
| Logs | Live, time-stamped events (stage changes, file written, check results). Auto-scroll with pause |
| Test results | Table: TC-ID, name, result, duration. Click a row to jump to the test and the code |
| Bug reports | List of bugs: ID, severity, REQ-ID, TC-ID, file and function, expected, actual, probable cause. Click opens the code at that function |
| Model output | Streamed raw model text (optional, collapsed by default) |

### 4.3 Reports page

Purpose: read results and download them.

```
+------------------------------------------------------------------+
| Reports   Project: [Library System v]                [Download v]|
+------------------------------------------------------------------+
| Summary:  Tests 24 | Passed 22 | Failed 2 | Iterations 3 | Time 18m |
+------------------------------------------------------------------+
| Requirement coverage                                              |
|  REQ-001  Add book         TC-001 pass   TC-002 pass              |
|  REQ-002  Issue book       TC-003 fail   Bug B-002                |
|  REQ-003  Return book      (no test)                              |
+------------------------------------------------------------------+
| Tabs: Development plan | Bug reports | Test results | Run history  |
+------------------------------------------------------------------+
```

- Coverage table shows each requirement, its tests and results. Requirements with no tests are highlighted.
- Reports render Markdown. Download as Markdown (PDF or Word later, if added).
- Run history lists each run with type, time, iterations and outcome.

### 4.4 Settings page

| Section | Fields |
|---|---|
| Model | Model path, context size, threads, max tokens, temperature (read-only while a run is active) |
| Fix loop | Iteration limit, test timeout |
| Appearance | Light, dark or system theme, editor font size |
| Health | Model loaded, load time, backend version, paths, last error |

Changing model-related settings may need a model reload. The UI says so and shows loading status.

---

## 5. Key Flows

### 5.1 First run

1. Projects → **New project**.
2. Workspace → **Docs** → drop requirement files. Status moves Uploaded → Indexing → Indexed.
3. Enter a prompt → **Plan**. Review and edit the plan → **Approve and generate**.
4. Watch files appear in the tree. Open one in Monaco.
5. Review each generated file in diff view → **Accept** or **Reject**.

### 5.2 Test and fix

1. **Tests** tab → upload or write test cases.
2. **Test** → results fill the bottom panel.
3. **Fix loop** → each iteration shows the failing function, the fix as a diff, and the new result.
4. The loop ends with Success, Iteration limit reached, or Same failure repeated. The last case shows an **Escalation** message with the latest bug report and a button to open the code.

### 5.3 Manual edit during a run
Files not being generated stay editable. A file being generated is read-only. If the user edits a file the agent later wants to change, the diff view shows the user's version as the base.

---

## 6. Components

| Component | Purpose |
|---|---|
| `AppShell` | Top bar, navigation, model status chip, routing outlet |
| `ProjectCard`, `NewProjectDialog` | Projects page |
| `Sidebar`, `DocsPanel`, `FileTree`, `TestsPanel` | Left side of workspace |
| `EditorTabs`, `CodeEditor` (Monaco), `DiffEditorView` | Centre |
| `RequirementBadge` | REQ-ID label linking code, requirement and tests |
| `RunPanel`, `StageStepper`, `PlanReview` | Right side |
| `BottomPanel`, `LogView`, `TestResultsTable`, `BugList`, `ModelOutput` | Bottom |
| `ReportViewer`, `CoverageTable` | Reports page |
| `SettingsForm`, `HealthCard` | Settings page |
| `StatusChip`, `ConfirmDialog`, `Toast`, `EmptyState` | Shared |

### 6.1 Monaco setup
- Use the bundled `monaco-editor` package and configure `@monaco-editor/react` to use the local copy (`loader.config({ monaco })`) so nothing loads from a CDN.
- Configure web workers through Vite (`?worker` imports) so syntax features work offline.
- Languages needed: Python, Markdown, JSON, YAML, plain text. Others are optional.
- Editor options: `automaticLayout`, `minimap` off, `wordWrap` off, `scrollBeyondLastLine` off.

---

## 7. States and Feedback

| Situation | UI behaviour |
|---|---|
| Model loading at start-up | Status chip "Loading model…", run buttons disabled, short explanation |
| Indexing | Progress per file, then "Indexed" |
| Generating | Stage stepper moves, current file highlighted, optional streamed text |
| Long wait | Elapsed timer and a note that CPU generation can take minutes. No fake progress bars |
| Backend busy | Another run is active: buttons disabled with a tooltip, link to the active run |
| Cancel | "Stopping…" until confirmed, then partial results are kept and marked |
| Error | Toast with a short message, details in Logs, retry button where it makes sense |
| Backend unreachable | Full-width banner "Backend not reachable" with retry |
| Empty states | Clear call to action, for example "Upload a requirement document to begin" |
| SSE disconnect | Auto-reconnect with the last event ID, then refresh run status |

---

## 8. Visual Design

### 8.1 Layout
- Desktop-first (minimum 1280 px wide). The workspace uses resizable panes. Small screens show a notice rather than a broken layout.
- Spacing scale of 4 px steps. Cards have rounded corners and a thin border.

### 8.2 Colour tokens (light / dark)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | #FFFFFF | #14181F | Page background |
| `--surface` | #F5F7FA | #1C222B | Panels |
| `--border` | #D5DBE3 | #2D3541 | Lines |
| `--text` | #1B2430 | #E6EAF0 | Main text |
| `--muted` | #5F6B7A | #98A3B3 | Secondary text |
| `--primary` | #1F3A5F | #6FA0E0 | Actions, active tab |
| `--success` | #2E7D32 | #66BB6A | Pass, indexed, done |
| `--warning` | #B26A00 | #FFB74D | Waiting, limit reached |
| `--danger` | #C62828 | #EF5350 | Fail, error |
| `--llm` | #F8E3C5 | #4A3A22 | Marks LLM-produced content |

Agent colours: Development Agent uses the primary colour, Testing Agent uses a teal accent. Both are always shown with a text label, not only colour.

### 8.3 Typography
- UI: system font stack (no web fonts).
- Code and logs: a monospace stack (Consolas, Menlo, monospace).
- Sizes: 14 px body, 13 px tables and logs, 12 px captions.

### 8.4 Status chips

| Status | Colour |
|---|---|
| Idle | Grey |
| Indexing, Developing, Testing | Blue with spinner |
| Done, Passed | Green |
| Failed | Red |
| Needs attention (escalated) | Amber |

---

## 9. Data Binding and API Use

| UI area | API |
|---|---|
| Projects | `GET/POST /api/projects`, `PATCH/DELETE /api/projects/{id}` |
| Docs | `POST /api/projects/{id}/documents`, `GET .../documents`, `GET .../requirements` |
| Code | `GET .../files`, `GET/PUT/DELETE .../files/{path}`, `POST .../files/{path}/accept` |
| Tests | `POST .../tests`, `GET .../bugs` |
| Run panel | `POST .../runs`, `POST /api/runs/{id}/cancel` |
| Live updates | `GET /api/runs/{id}/events` (SSE) |
| Reports | `GET .../reports`, `GET .../reports/{name}` |
| Settings and health | `GET/PUT /api/settings`, `GET /api/health` |

State rules: server data (projects, files, reports) is fetched and cached by a query library. Run progress arrives through SSE and updates a small UI store. After a `done` event the relevant queries are refreshed.

---

## 10. Accessibility and Usability

- Keyboard: Tab order follows regions; Ctrl+S saves; Esc closes dialogs; focus visible everywhere.
- Contrast meets WCAG AA in both themes.
- Status is never colour-only (icon and text too).
- Buttons have text labels or tooltips; icon-only buttons have `aria-label`.
- Confirm dialogs for delete and for discarding unsaved edits.
- Unsaved-changes dot on editor tabs.

---

## 11. Out of Scope for the First Version

- Login and multi-user features.
- Mobile layouts.
- Real-time collaboration.
- Plugin system and extra languages beyond Python.
- Visual diagrams generated from code.

---

## 12. Open Items

- Final choice of panes (resizable split library) and icon set.
- Whether to stream model tokens by default or keep the Model output tab collapsed.
- Whether PDF or Word export is built in this version.
- Whether the Tests tab includes a form for structured test cases or only file upload.
