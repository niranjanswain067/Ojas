"""
Ojas Document and Code Chunker.

Splits requirement documents (TXT, MD, PDF, DOCX) into atomic requirement chunks,
and source code files (Python) into AST-level code chunks.
"""

import ast
import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a piece of text.
    Standard heuristic: ~4 characters per token for English text.
    """
    if not text:
        return 0
    # Words heuristic combined with character length
    words = text.split()
    return max(len(words), len(text) // 4)


@dataclass
class Chunk:
    """An atomic requirement chunk from a document."""

    id: str
    document_id: str
    project_id: str
    req_id: str
    chunk_type: str = "requirement"
    heading: str = ""
    content: str = ""
    token_count: int = 0
    chunk_index: int = 0
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "project_id": self.project_id,
            "req_id": self.req_id,
            "chunk_type": self.chunk_type,
            "heading": self.heading,
            "content": self.content,
            "token_count": self.token_count,
            "chunk_index": self.chunk_index,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class CodeChunk:
    """An AST-derived chunk of source code (function, class, or module)."""

    id: str
    project_id: str
    file_path: str
    symbol_name: str
    symbol_type: str  # 'function', 'class', 'module'
    content: str
    start_line: int
    end_line: int
    content_hash: str
    linked_req_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_hash": self.content_hash,
            "linked_req_ids": self.linked_req_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# Pattern to identify headings: Markdown (#, ##, ###) or numbered (1.1, 2.0, Section 1:)
HEADING_REGEX = re.compile(
    r"^(?:#{1,6}\s+|(?:\d+\.)+\d*\s+|[A-Z][A-Za-z0-9\s]{1,40}:|Section\s+\d+:?)(.+)$",
    re.MULTILINE,
)

# Pattern to extract explicit REQ IDs like REQ-001, REQ_102, REQ-AUTH-01
REQ_ID_REGEX = re.compile(r"\b(REQ[-_]?[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*)\b", re.IGNORECASE)


def extract_req_ids(text: str) -> List[str]:
    """Find all unique explicit requirement identifiers in text."""
    if not text:
        return []
    matches = REQ_ID_REGEX.findall(text)
    # Deduplicate while preserving order, normalize to uppercase
    seen = set()
    result = []
    for m in matches:
        upper = m.upper().replace("_", "-")
        if upper not in seen:
            seen.add(upper)
            result.append(upper)
    return result


def chunk_document(
    text: str,
    document_id: str,
    project_id: str,
    min_tokens: int = 80,
    max_tokens: int = 400,
) -> List[Chunk]:
    """
    Split document text into atomic requirement chunks.

    Strategy:
    1. Split by headings (##, ###, numbered sections).
    2. If a section is > max_tokens, split further at paragraph boundaries.
    3. If a section is < min_tokens, merge with the next section.
    4. Assign REQ-IDs sequentially (REQ-001, REQ-002, ...) or use explicit REQ-IDs found in text.
    5. Each chunk gets: id, req_id, heading, content, token_count, chunk_index.
    """
    if not text or not text.strip():
        return []

    lines = text.splitlines(keepends=True)
    raw_sections: List[Dict[str, str]] = []
    current_heading = "Introduction"
    current_lines: List[str] = []

    for line in lines:
        match = HEADING_REGEX.match(line.strip())
        if match:
            # Save accumulated section if it has content
            body = "".join(current_lines).strip()
            if body:
                raw_sections.append({"heading": current_heading, "content": body})
            current_heading = match.group(0).strip().lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Add final section
    final_body = "".join(current_lines).strip()
    if final_body:
        raw_sections.append({"heading": current_heading, "content": final_body})

    # If no headings were found, fall back to paragraph splitting
    if not raw_sections:
        raw_sections = [{"heading": "General Requirements", "content": text.strip()}]

    # Step 2: Split sections larger than max_tokens at paragraph boundaries
    refined_sections: List[Dict[str, str]] = []
    for sec in raw_sections:
        content = sec["content"]
        heading = sec["heading"]
        tokens = estimate_tokens(content)

        if tokens <= max_tokens:
            refined_sections.append(sec)
        else:
            paragraphs = re.split(r"\n\s*\n", content)
            buf: List[str] = []
            buf_tokens = 0
            part_num = 1

            for p in paragraphs:
                p_trimmed = p.strip()
                if not p_trimmed:
                    continue
                p_toks = estimate_tokens(p_trimmed)

                if buf and (buf_tokens + p_toks > max_tokens):
                    refined_sections.append({
                        "heading": f"{heading} (Part {part_num})",
                        "content": "\n\n".join(buf),
                    })
                    part_num += 1
                    buf = [p_trimmed]
                    buf_tokens = p_toks
                else:
                    buf.append(p_trimmed)
                    buf_tokens += p_toks

            if buf:
                part_title = f"{heading} (Part {part_num})" if part_num > 1 else heading
                refined_sections.append({"heading": part_title, "content": "\n\n".join(buf)})

    # Step 3: Merge tiny fragments (< min_tokens) ONLY if they don't have their own explicit heading or REQ-ID
    merged_sections: List[Dict[str, str]] = []
    i = 0
    while i < len(refined_sections):
        curr = refined_sections[i]
        curr_content = curr["content"]
        curr_heading = curr["heading"]
        curr_tokens = estimate_tokens(curr_content)
        has_explicit_id = bool(extract_req_ids(f"{curr_heading} {curr_content}"))

        # If it has an explicit REQ-ID or meaningful heading, keep it distinct
        if has_explicit_id or curr_tokens >= min_tokens or (i + 1 >= len(refined_sections)):
            merged_sections.append(curr)
            i += 1
        else:
            # Only merge if it's a tiny heading-less fragment (< min_tokens) and next section exists
            nxt = refined_sections[i + 1]
            combined_heading = curr_heading if curr_heading == nxt["heading"] else f"{curr_heading} / {nxt['heading']}"
            combined_content = f"{curr_content}\n\n{nxt['content']}"
            merged_sections.append({
                "heading": combined_heading,
                "content": combined_content,
            })
            i += 2

    # Step 4: Build Chunk objects and assign REQ-IDs
    now = _now_iso()
    chunks: List[Chunk] = []

    for idx, sec in enumerate(merged_sections, start=1):
        content = sec["content"].strip()
        heading = sec["heading"].strip()
        tokens = estimate_tokens(content)

        # Look for explicit REQ ID in heading or text first
        explicit_reqs = extract_req_ids(f"{heading} {content}")
        if explicit_reqs:
            req_id = explicit_reqs[0]
        else:
            req_id = f"REQ-{idx:03d}"

        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunk_uuid = str(uuid.uuid4())

        chunks.append(
            Chunk(
                id=chunk_uuid,
                document_id=document_id,
                project_id=project_id,
                req_id=req_id,
                chunk_type="requirement",
                heading=heading,
                content=content,
                token_count=tokens,
                chunk_index=idx,
                content_hash=chunk_hash,
                metadata={"all_req_ids": explicit_reqs},
                created_at=now,
            )
        )

    return chunks


def chunk_code(
    file_path: str,
    source_code: str,
    project_id: str,
) -> List[CodeChunk]:
    """
    Parse Python source code into AST-level code chunks (functions, classes, modules).
    Extracts linked requirement references from docstrings and comments.
    """
    if not source_code or not source_code.strip():
        return []

    chunks: List[CodeChunk] = []
    lines = source_code.splitlines()
    now = _now_iso()

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError:
        # Fall back to whole-file module chunk on syntax errors
        content_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        reqs = extract_req_ids(source_code)
        chunks.append(
            CodeChunk(
                id=str(uuid.uuid4()),
                project_id=project_id,
                file_path=file_path,
                symbol_name="<module>",
                symbol_type="module",
                content=source_code,
                start_line=1,
                end_line=len(lines),
                content_hash=content_hash,
                linked_req_ids=reqs,
                created_at=now,
                updated_at=now,
            )
        )
        return chunks

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            chunk_lines = lines[start_line - 1 : end_line]
            content = "\n".join(chunk_lines)
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            docstring = ast.get_docstring(node) or ""
            reqs = extract_req_ids(f"{docstring} {content}")

            chunks.append(
                CodeChunk(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    file_path=file_path,
                    symbol_name=node.name,
                    symbol_type="function",
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    content_hash=content_hash,
                    linked_req_ids=reqs,
                    created_at=now,
                    updated_at=now,
                )
            )

        elif isinstance(node, ast.ClassDef):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            chunk_lines = lines[start_line - 1 : end_line]
            content = "\n".join(chunk_lines)
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            docstring = ast.get_docstring(node) or ""
            reqs = extract_req_ids(f"{docstring} {content}")

            chunks.append(
                CodeChunk(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    file_path=file_path,
                    symbol_name=node.name,
                    symbol_type="class",
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    content_hash=content_hash,
                    linked_req_ids=reqs,
                    created_at=now,
                    updated_at=now,
                )
            )

    # If no functions or classes were found (e.g. script with statements only), chunk the whole module
    if not chunks:
        content_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        reqs = extract_req_ids(source_code)
        chunks.append(
            CodeChunk(
                id=str(uuid.uuid4()),
                project_id=project_id,
                file_path=file_path,
                symbol_name="<module>",
                symbol_type="module",
                content=source_code,
                start_line=1,
                end_line=len(lines),
                content_hash=content_hash,
                linked_req_ids=reqs,
                created_at=now,
                updated_at=now,
            )
        )

    return chunks
