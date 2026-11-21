"""
Ojas Orchestrator: Coordinates execution of development tasks, planning,
code generation, static checks, workspace updates, and SSE progress events.
"""

import json
import logging
import time
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
from backend.app.storage.file_store import write_file
from backend.app.storage.run_store import (
    get_latest_plan,
    get_run,
    save_run,
    save_run_step,
    update_run,
)
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
