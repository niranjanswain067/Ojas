"""
Development Agent for Ojas: Analyzes requirements, creates development plans,
generates modular Python source code, and corrects code via static checks.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.llm.client import LLMClient
from backend.app.schemas.development import (
    BugReport,
    CheckResult,
    DevelopmentPlan,
    EntitySpec,
    FileSpec,
    GeneratedFile,
    ModuleSpec,
    RequirementAnalysis,
)
from backend.app.validation.static_check import check_file, check_syntax

logger = logging.getLogger(__name__)

# Base directory for prompt templates
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _read_template(template_name: str) -> str:
    """Read a prompt template file from backend/app/agents/prompts/."""
    path = _PROMPTS_DIR / template_name
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


class DevelopmentAgent:
    """
    Autonomous Development Agent responsible for software construction:
    1. Requirement analysis (modules, entities, constraints)
    2. Architecture & file-level development planning
    3. File-by-file code generation with automated AST and lint self-correction
    4. Bug fixing and function remediation from test failures
    """

    def __init__(
        self,
        llm_client: LLMClient,
        search_engine: Optional[Any] = None,
        project_id: str = "",
    ) -> None:
        self.llm_client = llm_client
        self.search_engine = search_engine
        self.project_id = project_id

    # -----------------------------------------------------------------------
    # Helper Utilities
    # -----------------------------------------------------------------------

    def _extract_code_block(self, response: str) -> str:
        """
        Extract code from markdown ```python ... ``` code blocks.
        If no code blocks are present, fallback to raw response.
        """
        # Match ```python ... ```
        match = re.search(r"```(?:python|py)\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Match generic ``` ... ```
        generic_match = re.search(r"```\s*\n(.*?)```", response, re.DOTALL)
        if generic_match:
            return generic_match.group(1).strip()

        # Fallback to stripped text
        return response.strip()

    def _extract_json_block(self, response: str) -> str:
        """
        Extract JSON payload from markdown ```json ... ``` blocks or braces.
        """
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL | re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

        # Find first '{' and last '}'
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1 and end > start:
            return response[start : end + 1].strip()

        return response.strip()

    def _build_context(self, chunks: List[Any]) -> str:
        """Format retrieved requirement chunks into structured prompt context."""
        if not chunks:
            return "No specific requirement specifications found."

        formatted_items = []
        for c in chunks:
            if hasattr(c, "req_id") and hasattr(c, "content"):
                heading = getattr(c, "heading", "") or ""
                header = f"[{c.req_id}] {heading}".strip()
                formatted_items.append(f"{header}:\n{c.content.strip()}")
            elif isinstance(c, dict):
                req_id = c.get("req_id", "REQ")
                heading = c.get("heading", "")
                content = c.get("content", "")
                header = f"[{req_id}] {heading}".strip()
                formatted_items.append(f"{header}:\n{content.strip()}")
            else:
                formatted_items.append(str(c).strip())

        return "\n\n".join(formatted_items)

    def _search_requirements(self, query: str, top_k: int = 5) -> List[Any]:
        """Search relevant requirement chunks via search_engine if available."""
        if not self.search_engine:
            return []
        try:
            return self.search_engine.search(query, top_k=top_k)
        except Exception as exc:
            logger.warning("RAG search failed for query '%s': %s", query, exc)
            return []

    # -----------------------------------------------------------------------
    # 1. Requirement Analysis
    # -----------------------------------------------------------------------

    def analyze_requirements(self, prompt: str, top_k: int = 5) -> RequirementAnalysis:
        """
        Analyze prompt and retrieved requirements to generate a structured
        summary including modules, entities, and relationships.
        """
        template = _read_template("requirement_analysis.txt")
        chunks = self._search_requirements(prompt, top_k=top_k)
        req_context = self._build_context(chunks)

        rendered = template.replace("{{requirements}}", req_context).replace("{{user_prompt}}", prompt)

        raw_output = self.llm_client.generate(
            rendered,
            max_tokens=1500,
            temperature=0.2,
        )

        json_str = self._extract_json_block(raw_output)
        try:
            data = json.loads(json_str)
            modules = [ModuleSpec(**m) for m in data.get("modules", [])]
            entities = [EntitySpec(**e) for e in data.get("entities", [])]
            return RequirementAnalysis(
                summary=data.get("summary", prompt),
                modules=modules,
                entities=entities,
                relationships=data.get("relationships", []),
                constraints=data.get("constraints", []),
            )
        except Exception as exc:
            logger.warning("Could not parse RequirementAnalysis JSON (%s). Using fallback.", exc)
            return RequirementAnalysis(
                summary=prompt,
                modules=[ModuleSpec(name="Core", description="Primary application module", responsibilities=[prompt])],
                entities=[],
                relationships=[],
                constraints=[],
            )

    # -----------------------------------------------------------------------
    # 2. Development Plan Generation
    # -----------------------------------------------------------------------

    def generate_plan(
        self,
        prompt: str,
        analysis: Optional[RequirementAnalysis] = None,
        top_k: int = 5,
    ) -> DevelopmentPlan:
        """
        Generate an ordered development plan specifying files, classes,
        functions, and dependencies from requirements.
        """
        if analysis is None:
            analysis = self.analyze_requirements(prompt, top_k=top_k)

        template = _read_template("development_plan.txt")
        chunks = self._search_requirements(prompt, top_k=top_k)
        req_context = self._build_context(chunks)

        analysis_json = json.dumps(analysis.model_dump(), indent=2)

        rendered = (
            template.replace("{{requirements}}", req_context)
            .replace("{{analysis}}", analysis_json)
            .replace("{{user_prompt}}", prompt)
        )

        raw_output = self.llm_client.generate(
            rendered,
            max_tokens=2048,
            temperature=0.2,
        )

        json_str = self._extract_json_block(raw_output)
        try:
            data = json.loads(json_str)
            raw_files = data.get("files", [])
            files = []
            for i, f in enumerate(raw_files, start=1):
                f_data = dict(f)
                if "order" not in f_data:
                    f_data["order"] = i
                files.append(FileSpec(**f_data))

            return DevelopmentPlan(
                project_name=data.get("project_name", "OjasProject"),
                plan_summary=data.get("plan_summary", "Modular software development plan"),
                files=files,
            )
        except Exception as exc:
            logger.warning("Could not parse DevelopmentPlan JSON (%s). Using fallback plan.", exc)
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
                plan_summary=f"Implementation plan for: {prompt}",
                files=[default_file],
            )

    # -----------------------------------------------------------------------
    # 3. File Generation & Self-Correction Loop
    # -----------------------------------------------------------------------

    def generate_file(
        self,
        file_spec: FileSpec,
        plan: Optional[DevelopmentPlan] = None,
        existing_code: str = "",
        max_retries: int = 2,
    ) -> GeneratedFile:
        """
        Generate Python code for a specific file from the development plan.
        Performs static checks (AST syntax + ruff lint) and executes an
        autonomous self-correction loop up to max_retries upon failure.
        """
        template = _read_template("code_generation.txt")

        # Retrieve requirements specific to this file
        search_query = f"{file_spec.file_path} {file_spec.description} {' '.join(file_spec.classes)} {' '.join(file_spec.functions)}"
        chunks = self._search_requirements(search_query, top_k=4)
        req_context = self._build_context(chunks)

        # Plan context
        plan_context = ""
        if plan:
            file_summaries = [f"- {f.file_path} (Order {f.order}): {f.description}" for f in plan.files]
            plan_context = f"Project: {plan.project_name}\nFiles in plan:\n" + "\n".join(file_summaries)

        classes_functions_str = (
            f"Classes: {', '.join(file_spec.classes) if file_spec.classes else 'None'}; "
            f"Functions: {', '.join(file_spec.functions) if file_spec.functions else 'None'}"
        )

        existing_code_block = ""
        if existing_code.strip():
            existing_code_block = f"### Existing Code in Workspace\n```python\n{existing_code}\n```"

        base_prompt = (
            template.replace("{{file_path}}", file_spec.file_path)
            .replace("{{file_description}}", file_spec.description)
            .replace("{{classes_and_functions}}", classes_functions_str)
            .replace("{{plan_context}}", plan_context)
            .replace("{{requirements}}", req_context)
            .replace("{{existing_code_context}}", existing_code_block)
        )

        # Self-correction loop: attempts 0, 1, ..., max_retries
        attempts = 0
        current_feedback = ""
        last_code = ""
        last_check = CheckResult(passed=False, issues=[])

        while attempts <= max_retries:
            error_section = ""
            if current_feedback:
                error_section = f"\n### Verification Feedback (Correction Attempt {attempts}/{max_retries})\n{current_feedback}\n"

            rendered_prompt = base_prompt.replace("{{error_feedback}}", error_section)

            raw_response = self.llm_client.generate(
                rendered_prompt,
                max_tokens=2048,
                temperature=0.2,
            )

            code = self._extract_code_block(raw_response)
            if not code.startswith("# Generated by Ojas"):
                code = f"# Generated by Ojas\n\n{code}"

            last_code = code
            check_res = check_file(code, file_spec.file_path)
            last_check = check_res

            if check_res.passed:
                logger.info(
                    "File '%s' passed static check on attempt %d.",
                    file_spec.file_path,
                    attempts,
                )
                return GeneratedFile(
                    file_path=file_spec.file_path,
                    content=code,
                    is_generated=True,
                    check_result=check_res,
                    retry_count=attempts,
                )

            # Check failed
            logger.warning(
                "File '%s' failed check on attempt %d (errors: %s). Preparing retry...",
                file_spec.file_path,
                attempts,
                [f"{i.code}: {i.message}" for i in check_res.issues],
            )
            current_feedback = check_res.to_prompt_message()
            attempts += 1

        # Max retries exceeded; return latest code with errors noted
        logger.error(
            "File '%s' failed static check after %d retries.",
            file_spec.file_path,
            max_retries,
        )
        return GeneratedFile(
            file_path=file_spec.file_path,
            content=last_code,
            is_generated=True,
            check_result=last_check,
            retry_count=max_retries,
        )

    # -----------------------------------------------------------------------
    # 4. Bug Remediation & Function Fixing
    # -----------------------------------------------------------------------

    def fix_function(
        self,
        bug_report: BugReport,
        current_code: str,
        max_retries: int = 2,
    ) -> str:
        """
        Fix a failing function given a bug report and current code.
        Performs syntax check on the fixed code with self-correction.
        """
        template = _read_template("code_fix.txt")

        # Retrieve linked requirement
        linked_req = "No linked requirement text available."
        if bug_report.req_id and self.search_engine:
            chunks = self._search_requirements(f"{bug_report.req_id} {bug_report.function_name}", top_k=2)
            if chunks:
                linked_req = self._build_context(chunks)

        base_prompt = (
            template.replace("{{bug_id}}", bug_report.bug_id)
            .replace("{{req_id}}", bug_report.req_id or "N/A")
            .replace("{{tc_id}}", bug_report.tc_id or "N/A")
            .replace("{{file_path}}", bug_report.file_path)
            .replace("{{function_name}}", bug_report.function_name)
            .replace("{{expected_result}}", bug_report.expected_result)
            .replace("{{actual_result}}", bug_report.actual_result)
            .replace("{{probable_cause}}", bug_report.probable_cause or "Not specified")
            .replace("{{linked_requirement}}", linked_req)
            .replace("{{current_code}}", current_code)
        )

        attempts = 0
        feedback = ""
        last_fixed = current_code

        while attempts <= max_retries:
            rendered = base_prompt.replace("{{error_feedback}}", feedback)
            raw_response = self.llm_client.generate(rendered, max_tokens=2048, temperature=0.2)
            fixed_code = self._extract_code_block(raw_response)

            syntax_res = check_syntax(fixed_code, bug_report.file_path)
            if syntax_res.passed:
                return fixed_code

            logger.warning(
                "Fixed function for %s has syntax error on attempt %d: %s",
                bug_report.function_name,
                attempts,
                syntax_res.issues,
            )
            feedback = f"\n### Syntax Error in Fix:\n{syntax_res.to_prompt_message()}\n"
            last_fixed = fixed_code
            attempts += 1

        return last_fixed
