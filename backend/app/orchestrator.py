"""
Ojas Orchestrator: Coordinates execution of development tasks, planning,
code generation, static checks, workspace updates, and SSE progress events.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.agents.development_agent import DevelopmentAgent
from backend.app.events.event_bus import EventBus, get_event_bus
from backend.app.llm.client import LLMClient
from backend.app.rag.chunker import chunk_code

try:
    from backend.app.rag.index import IndexManager
except ImportError:
    IndexManager = None  # type: ignore

try:
    from backend.app.rag.search import SearchEngine
except ImportError:
    SearchEngine = None  # type: ignore
from backend.app.schemas.development import DevelopmentPlan, FileSpec
from backend.app.storage.file_store import read_file, resolve_safe_path, write_file
from backend.app.storage.run_store import (
    get_latest_plan,
    get_run,
    save_run,
    save_run_step,
    update_run,
)
from backend.app.storage.test_store import (
    get_next_tc_id,
    get_test_case_by_name_or_function,
    get_test_cases,
    save_test_case,
    save_test_result,
)
from backend.app.storage.bug_store import get_bug_reports, save_bug_report
from backend.app.validation.static_check import check_file
from backend.app.validation.test_runner import TestCaseResult, TestRunResult, TestRunner
from backend.app.tasks.task_manager import TaskManager, get_task_manager

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@dataclass
class RunResult:
    """Structured result of an orchestrated run."""

    run_id: str
    success: bool
    status: str
    message: str = ""
    plan_text: Optional[str] = None
    files_generated: List[str] = field(default_factory=list)
    stop_reason: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class Orchestrator:
    """
    State-machine coordinator for Ojas agent execution:
    IDLE → PLANNING → PLAN_REVIEW → GENERATING → CHECKING → DONE / FAILED
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        search_engine: Optional[SearchEngine] = None,
        task_manager: Optional[TaskManager] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.llm_client = llm_client
        self.search_engine = search_engine
        self.task_manager = task_manager or get_task_manager()
        self.event_bus = event_bus or get_event_bus()

    def _get_llm_client(self) -> LLMClient:
        """Resolve LLM client singleton if not explicitly injected."""
        if self.llm_client is not None:
            return self.llm_client
        from backend.app.main import get_llm_client

        client = get_llm_client()
        if client is None:
            raise RuntimeError("LLM client is not initialized or loaded.")
        return client

    def _publish(self, run_id: str, event_type: str, data: Any) -> None:
        """Publish an event to the EventBus."""
        if self.event_bus:
            try:
                self.event_bus.publish(run_id, event_type, data)
            except Exception as exc:
                logger.warning("Failed to publish SSE event %s for run %s: %s", event_type, run_id, exc)

    def _is_cancelled(self, run_id: str) -> bool:
        """Cooperative cancellation probe."""
        if self.task_manager:
            return self.task_manager.is_cancelled(run_id)
        return False

    # -----------------------------------------------------------------------
    # 1. Plan Execution (PLANNING stage)
    # -----------------------------------------------------------------------

    def run_plan(
        self,
        project_id: str,
        prompt: str,
        run_id: Optional[str] = None,
    ) -> RunResult:
        """
        Execute requirement analysis and development plan generation.
        Transitions run into PLAN_REVIEW (status: pending_approval).
        """
        now = _now_iso()
        existing = get_run(run_id) if run_id else None
        if not existing:
            saved = save_run(
                project_id=project_id,
                run_type="plan",
                prompt=prompt,
                status="running",
                run_id=run_id,
            )
            r_id = saved["id"]
        else:
            r_id = existing["id"]
            update_run(r_id, status="running", started_at=now)

        logger.info("Starting run_plan for project %s (run_id: %s)", project_id, r_id)
        start_time = time.time()

        # Step 0: Record audit step & publish event
        save_run_step(r_id, step_index=0, stage="planning", status="started", message="Analyzing requirements")
        self._publish(r_id, "stage", {"stage": "planning", "status": "started", "message": "Analyzing requirements..."})

        try:
            llm = self._get_llm_client()
            agent = DevelopmentAgent(
                llm_client=llm,
                search_engine=self.search_engine,
                project_id=project_id,
            )

            if self._is_cancelled(r_id):
                update_run(r_id, status="cancelled", stop_reason="user_cancelled")
                self._publish(r_id, "done", {"status": "cancelled", "stop_reason": "user_cancelled"})
                return RunResult(run_id=r_id, success=False, status="cancelled", stop_reason="user_cancelled")

            # 1. Analyze requirements
            analysis = agent.analyze_requirements(prompt)

            if self._is_cancelled(r_id):
                update_run(r_id, status="cancelled", stop_reason="user_cancelled")
                self._publish(r_id, "done", {"status": "cancelled", "stop_reason": "user_cancelled"})
                return RunResult(run_id=r_id, success=False, status="cancelled", stop_reason="user_cancelled")

            # 2. Generate plan
            plan = agent.generate_plan(prompt, analysis=analysis)
            plan_text = json.dumps(plan.model_dump(), indent=2)

            duration_ms = int((time.time() - start_time) * 1000)
            update_run(
                r_id,
                status="pending_approval",
                plan_text=plan_text,
                completed_at=_now_iso(),
            )
            save_run_step(
                r_id,
                step_index=1,
                stage="planning",
                status="completed",
                message="Plan generated and awaiting user review",
                duration_ms=duration_ms,
            )

            # Publish completion events
            self._publish(
                r_id,
                "stage",
                {"stage": "planning", "status": "completed", "plan": plan.model_dump()},
            )
            self._publish(
                r_id,
                "plan_ready",
                {"run_id": r_id, "plan_text": plan_text, "status": "pending_approval"},
            )

            return RunResult(
                run_id=r_id,
                success=True,
                status="pending_approval",
                message="Development plan generated successfully. Awaiting approval.",
                plan_text=plan_text,
            )

        except Exception as exc:
            logger.exception("run_plan failed for run %s: %s", r_id, exc)
            update_run(r_id, status="failed", error_message=str(exc), completed_at=_now_iso())
            save_run_step(r_id, step_index=1, stage="planning", status="failed", message=str(exc))
            self._publish(r_id, "error", {"message": f"Planning failed: {exc}"})
            self._publish(r_id, "done", {"status": "failed", "error": str(exc)})
            return RunResult(run_id=r_id, success=False, status="failed", message=str(exc), errors=[str(exc)])

    # -----------------------------------------------------------------------
    # 2. Develop Execution (GENERATING & CHECKING stage)
    # -----------------------------------------------------------------------

    def run_develop(
        self,
        project_id: str,
        prompt: str = "",
        plan_text: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> RunResult:
        """
        Execute code generation for each file in the plan with static checks,
        cooperative cancellation, workspace persistence, and code vector indexing.
        """
        now = _now_iso()
        existing = get_run(run_id) if run_id else None
        if not existing:
            saved = save_run(
                project_id=project_id,
                run_type="develop",
                prompt=prompt,
                plan_text=plan_text,
                status="running",
                run_id=run_id,
            )
            r_id = saved["id"]
        else:
            r_id = existing["id"]
            update_run(r_id, status="running", started_at=now)

        logger.info("Starting run_develop for project %s (run_id: %s)", project_id, r_id)

        try:
            llm = self._get_llm_client()
            agent = DevelopmentAgent(
                llm_client=llm,
                search_engine=self.search_engine,
                project_id=project_id,
            )

            # Resolve plan
            active_plan_text = plan_text
            if not active_plan_text:
                latest = get_latest_plan(project_id)
                if latest and latest.get("plan_text"):
                    active_plan_text = latest["plan_text"]

            if not active_plan_text:
                # If no plan exists, run planning first
                logger.info("No plan found for develop run %s. Generating plan first.", r_id)
                plan_res = self.run_plan(project_id, prompt or "Build system", run_id=r_id)
                if not plan_res.success:
                    return plan_res
                active_plan_text = plan_res.plan_text

            # Parse plan
            plan_obj = self._parse_plan_object(active_plan_text, prompt)

            self._publish(
                r_id,
                "stage",
                {"stage": "generating", "status": "started", "file_count": len(plan_obj.files)},
            )

            files_generated: List[str] = []
            step_idx = 0

            # Loop through each file in plan
            for file_spec in plan_obj.files:
                if self._is_cancelled(r_id):
                    logger.info("run_develop cancelled by user between files (run %s)", r_id)
                    update_run(r_id, status="cancelled", stop_reason="user_cancelled", completed_at=_now_iso())
                    self._publish(r_id, "done", {"status": "cancelled", "stop_reason": "user_cancelled"})
                    return RunResult(
                        run_id=r_id,
                        success=False,
                        status="cancelled",
                        stop_reason="user_cancelled",
                        files_generated=files_generated,
                    )

                step_idx += 1
                f_path = file_spec.file_path
                self._publish(r_id, "stage", {"stage": "generating", "file": f_path, "status": "started"})
                self._publish(r_id, "file", {"path": f_path, "action": "generating", "status": "started"})

                # Generate code with AST and ruff self-correction
                f_start = time.time()
                gen_file = agent.generate_file(file_spec, plan=plan_obj, max_retries=2)
                duration_ms = int((time.time() - f_start) * 1000)

                # Persist to project workspace
                write_file(project_id, f_path, gen_file.content)
                files_generated.append(f_path)

                # AST code chunk indexing
                if IndexManager is not None:
                    try:
                        code_chunks = chunk_code(f_path, gen_file.content, project_id)
                        idx_mgr = IndexManager(project_id)
                        idx_mgr.index_code(f_path, code_chunks)
                    except Exception as exc:
                        logger.warning("Code indexing failed for %s: %s", f_path, exc)

                # Publish file result event
                check_status = "ast_ok" if gen_file.check_result.passed else "check_failed"
                self._publish(
                    r_id,
                    "stage",
                    {"stage": "checking", "file": f_path, "status": "completed", "check_status": check_status},
                )
                self._publish(
                    r_id,
                    "file",
                    {
                        "path": f_path,
                        "action": "created",
                        "status": check_status,
                        "retries": gen_file.retry_count,
                        "issues": [i.model_dump() for i in gen_file.check_result.issues],
                    },
                )

                save_run_step(
                    r_id,
                    step_index=step_idx,
                    stage="generating",
                    status="completed" if gen_file.check_result.passed else "failed",
                    message=f"Created {f_path} (retries={gen_file.retry_count})",
                    duration_ms=duration_ms,
                )

            # Completion
            update_run(r_id, status="completed", completed_at=_now_iso())
            self._publish(r_id, "stage", {"stage": "generating", "status": "completed"})
            self._publish(
                r_id,
                "done",
                {"status": "completed", "stop_reason": "completed", "files_generated": files_generated},
            )

            try:
                from backend.app.storage.report_writer import ReportWriter
                ReportWriter(project_id).generate_consolidated_report()
            except Exception as rw_exc:
                logger.debug("Failed auto-generating report: %s", rw_exc)

            return RunResult(
                run_id=r_id,
                success=True,
                status="completed",
                message=f"Generated {len(files_generated)} files successfully.",
                files_generated=files_generated,
                plan_text=active_plan_text,
            )

        except Exception as exc:
            logger.exception("run_develop failed for run %s: %s", r_id, exc)
            update_run(r_id, status="failed", error_message=str(exc), completed_at=_now_iso())
            self._publish(r_id, "error", {"message": f"Development failed: {exc}"})
            self._publish(r_id, "done", {"status": "failed", "error": str(exc)})
            return RunResult(run_id=r_id, success=False, status="failed", message=str(exc), errors=[str(exc)])

    # -----------------------------------------------------------------------
    # 3. Test Execution (TESTING stage)
    # -----------------------------------------------------------------------

    def run_test(
        self,
        project_id: str,
        run_id: Optional[str] = None,
        test_file: Optional[str] = None,
    ) -> RunResult:
        """
        Execute tests via TestRunner, record results, and generate bug reports on failure.
        """
        r_id = run_id or str(uuid.uuid4())
        existing = get_run(r_id)
        if not existing:
            save_run(project_id=project_id, run_type="test", status="running", run_id=r_id)
        else:
            update_run(r_id, status="running", started_at=_now_iso())

        self._publish(r_id, "stage", {"stage": "testing", "status": "started"})
        save_run_step(r_id, step_index=0, stage="testing", status="started", message="Running pytest suite")

        runner = TestRunner()
        test_res = runner.run_tests(project_id, test_file=test_file)

        # Save test results
        for tc in test_res.results:
            tc_rec = get_test_case_by_name_or_function(project_id, tc.name)
            if not tc_rec:
                tc_id = tc.tc_id or get_next_tc_id(project_id)
                tc_rec = save_test_case(
                    project_id=project_id,
                    tc_id=tc_id,
                    name=tc.name,
                    file_path=tc.file_path or "tests/test_suite.py",
                    function_name=tc.name,
                )
            tc_record_id = tc_rec["id"]
            tc_id = tc_rec["tc_id"]
            save_test_result(
                run_id=r_id,
                test_case_id=tc_record_id,
                tc_id=tc_id,
                result=tc.result,
                duration_ms=tc.duration_ms,
                stdout=tc.stdout,
                stderr=tc.stderr,
                error_message=tc.error_message,
                project_id=project_id,
            )
            self._publish(r_id, "test", {
                "tc_id": tc_id,
                "name": tc.name,
                "result": tc.result,
                "duration_ms": tc.duration_ms,
                "error_message": tc.error_message,
            })

        # Analyze failures if any
        failures = [t for t in test_res.results if t.result in ("failed", "error")]
        bug_reports = []
        if failures:
            llm_client = None
            try:
                llm_client = self._get_llm_client()
            except Exception:
                pass
            from backend.app.agents.testing_agent import TestingAgent

            agent = TestingAgent(
                llm_client=llm_client,
                search_engine=self.search_engine,
                project_id=project_id,
            )
            bug_reports = agent.analyze_failures(failures, project_id=project_id, run_id=r_id, iteration=0)
            for b in bug_reports:
                self._publish(r_id, "bug", b)

        final_status = "completed" if test_res.success else "failed"
        update_run(r_id, status=final_status, completed_at=_now_iso())
        self._publish(r_id, "stage", {"stage": "testing", "status": "completed"})
        self._publish(r_id, "done", {
            "status": final_status,
            "passed": test_res.passed,
            "failed": test_res.failed,
            "summary": test_res.summary,
        })
        save_run_step(
            r_id,
            step_index=1,
            stage="testing",
            status=final_status,
            message=test_res.summary,
            duration_ms=test_res.duration_ms,
        )

        return RunResult(
            run_id=r_id,
            success=test_res.success,
            status=final_status,
            message=test_res.summary,
            stop_reason="all_passed" if test_res.success else "test_failures",
        )

    # -----------------------------------------------------------------------
    # 4. Automated Fix Loop (FIX_LOOP stage with 3 Stop Conditions)
    # -----------------------------------------------------------------------

    def run_fix_loop(
        self,
        project_id: str,
        iteration_limit: int = 5,
        run_id: Optional[str] = None,
    ) -> RunResult:
        """
        Automated test-and-repair fix loop with three mandatory stop rules:
        1. Stop when all tests pass.
        2. Stop when the same failure repeats across consecutive iterations.
        3. Stop when the iteration limit (e.g. 5) is reached.
        """
        r_id = run_id or str(uuid.uuid4())
        existing = get_run(r_id)
        if not existing:
            save_run(project_id=project_id, run_type="fix_loop", status="running", run_id=r_id, iteration_limit=iteration_limit)
        else:
            update_run(r_id, status="running", started_at=_now_iso())

        iteration = 0
        previous_failures: Optional[frozenset] = None
        step_index = 0

        runner = TestRunner()
        llm_client = None
        try:
            llm_client = self._get_llm_client()
        except Exception:
            pass

        from backend.app.agents.testing_agent import TestingAgent

        testing_agent = TestingAgent(
            llm_client=llm_client,
            search_engine=self.search_engine,
            project_id=project_id,
        )
        dev_agent = DevelopmentAgent(
            llm_client=llm_client,
            search_engine=self.search_engine,
            project_id=project_id,
        )

        while iteration < iteration_limit:
            iteration += 1
            update_run(r_id, iteration_count=iteration)
            self._publish(r_id, "iteration", {"iteration": iteration, "limit": iteration_limit})
            self._publish(r_id, "stage", {"stage": "testing", "status": "started", "iteration": iteration})

            # Check cooperative cancellation
            if self._is_cancelled(r_id):
                update_run(r_id, status="cancelled", stop_reason="user_cancelled", completed_at=_now_iso())
                self._publish(r_id, "done", {"status": "cancelled", "stop_reason": "user_cancelled"})
                return RunResult(run_id=r_id, success=False, status="cancelled", stop_reason="user_cancelled", message="Run cancelled by user.")

            # 1. Run tests
            test_run = runner.run_tests(project_id)
            step_index += 1
            save_run_step(
                r_id,
                step_index=step_index,
                stage="testing",
                status="completed",
                message=f"Iteration {iteration}: {test_run.summary}",
                duration_ms=test_run.duration_ms,
            )

            failures = [t for t in test_run.results if t.result in ("failed", "error")]
            for tc in test_run.results:
                tc_rec = get_test_case_by_name_or_function(project_id, tc.name)
                if not tc_rec:
                    tc_id = tc.tc_id or get_next_tc_id(project_id)
                    tc_rec = save_test_case(
                        project_id=project_id,
                        tc_id=tc_id,
                        name=tc.name,
                        file_path=tc.file_path or "tests/test_suite.py",
                        function_name=tc.name,
                    )
                tc_record_id = tc_rec["id"]
                tc_id = tc_rec["tc_id"]
                save_test_result(
                    run_id=r_id,
                    test_case_id=tc_record_id,
                    tc_id=tc_id,
                    iteration=iteration,
                    result=tc.result,
                    duration_ms=tc.duration_ms,
                    stdout=tc.stdout,
                    stderr=tc.stderr,
                    error_message=tc.error_message,
                    project_id=project_id,
                )
                self._publish(r_id, "test", {
                    "tc_id": tc_id,
                    "name": tc.name,
                    "result": tc.result,
                    "iteration": iteration,
                    "duration_ms": tc.duration_ms,
                    "error_message": tc.error_message,
                })

            # 2. Stop condition 1: All tests pass
            if not failures and test_run.total > 0:
                update_run(r_id, status="completed", stop_reason="all_passed", completed_at=_now_iso())
                self._publish(r_id, "stage", {"stage": "done", "status": "completed"})
                self._publish(r_id, "done", {
                    "status": "completed",
                    "stop_reason": "all_passed",
                    "message": "All tests passed successfully!",
                    "iteration": iteration,
                })
                try:
                    from backend.app.storage.report_writer import ReportWriter
                    ReportWriter(project_id).generate_consolidated_report()
                except Exception:
                    pass
                return RunResult(
                    run_id=r_id,
                    success=True,
                    status="completed",
                    stop_reason="all_passed",
                    message=f"All tests passed on iteration {iteration}.",
                )

            # If no tests exist in project workspace
            if test_run.total == 0:
                update_run(r_id, status="completed", stop_reason="no_tests", completed_at=_now_iso())
                self._publish(r_id, "done", {"status": "completed", "stop_reason": "no_tests", "message": "No tests found."})
                return RunResult(run_id=r_id, success=True, status="completed", stop_reason="no_tests", message="No tests found.")

            # 3. Stop condition 2: Same failure repeats
            current_failure_set = frozenset((f.name, f.error_message or "") for f in failures)
            if previous_failures is not None and current_failure_set == previous_failures:
                msg = f"Fix loop stopped: same {len(failures)} failure(s) repeated across iterations. Manual intervention required."
                update_run(r_id, status="failed", stop_reason="repeated_failure", error_message=msg, completed_at=_now_iso())
                self._publish(r_id, "error", {"message": msg, "stop_reason": "repeated_failure"})
                self._publish(r_id, "done", {
                    "status": "failed",
                    "stop_reason": "repeated_failure",
                    "message": msg,
                    "iteration": iteration,
                })
                return RunResult(
                    run_id=r_id,
                    success=False,
                    status="failed",
                    stop_reason="repeated_failure",
                    message=msg,
                )
            previous_failures = current_failure_set

            # 4. Generate bug reports
            bug_reports = testing_agent.analyze_failures(failures, project_id=project_id, run_id=r_id, iteration=iteration)
            for b in bug_reports:
                self._publish(r_id, "bug", b)

            # 5. Fix each failing function
            for bug in bug_reports:
                if self._is_cancelled(r_id):
                    update_run(r_id, status="cancelled", stop_reason="user_cancelled", completed_at=_now_iso())
                    self._publish(r_id, "done", {"status": "cancelled", "stop_reason": "user_cancelled"})
                    return RunResult(run_id=r_id, success=False, status="cancelled", stop_reason="user_cancelled", message="Run cancelled by user.")

                f_path = bug.get("file_path")
                func_name = bug.get("function_name")
                if not f_path:
                    continue

                self._publish(r_id, "stage", {"stage": "fixing", "file": f_path, "function": func_name, "status": "started"})
                try:
                    res = read_file(project_id, f_path)
                    current_code = res.content if hasattr(res, "content") else str(res)
                except Exception:
                    current_code = ""

                if not current_code:
                    continue

                fixed_code = dev_agent.fix_function(bug, current_code)
                write_file(project_id, f_path, fixed_code)

                # Re-check syntax / lint on fixed file
                full_path = resolve_safe_path(project_id, f_path)
                check_res = check_file(full_path)
                step_index += 1
                save_run_step(
                    r_id,
                    step_index=step_index,
                    stage="fixing",
                    status="completed" if check_res.passed else "failed",
                    message=f"Applied fix to {f_path}:{func_name or ''} (syntax={'ok' if check_res.passed else 'failed'})",
                )
                self._publish(r_id, "file", {
                    "path": f_path,
                    "action": "fixed",
                    "function": func_name,
                    "status": "ast_ok" if check_res.passed else "check_failed",
                })

        # 6. Stop condition 3: Iteration limit reached
        limit_msg = f"Fix loop stopped: maximum iteration limit ({iteration_limit}) reached without resolving all test failures."
        update_run(r_id, status="failed", stop_reason="iteration_limit", error_message=limit_msg, completed_at=_now_iso())
        self._publish(r_id, "error", {"message": limit_msg, "stop_reason": "iteration_limit"})
        self._publish(r_id, "done", {
            "status": "failed",
            "stop_reason": "iteration_limit",
            "message": limit_msg,
            "iteration": iteration,
        })
        return RunResult(
            run_id=r_id,
            success=False,
            status="failed",
            stop_reason="iteration_limit",
            message=limit_msg,
        )

    # -----------------------------------------------------------------------
    # Helper: Plan Parsing
    # -----------------------------------------------------------------------

    def _parse_plan_object(self, plan_text: str, fallback_prompt: str = "") -> DevelopmentPlan:
        """Parse raw plan JSON or markdown into a structured DevelopmentPlan."""
        try:
            # Try raw json
            data = json.loads(plan_text)
            return DevelopmentPlan(**data)
        except Exception:
            pass

        # Try extracting ```json block
        from backend.app.agents.development_agent import DevelopmentAgent

        dummy_agent = DevelopmentAgent(llm_client=None)  # type: ignore
        extracted = dummy_agent._extract_json_block(plan_text)
        try:
            data = json.loads(extracted)
            return DevelopmentPlan(**data)
        except Exception:
            pass

        # Fallback to single file plan
        default_file = FileSpec(
            file_path="main.py",
            description="Core implementation file",
            classes=[],
            functions=["main"],
            dependencies=[],
            order=1,
        )
        return DevelopmentPlan(
            project_name="OjasProject",
            plan_summary=fallback_prompt or "Default plan",
            files=[default_file],
        )
