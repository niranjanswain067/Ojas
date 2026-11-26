"""
Pydantic schemas for Reports API in Ojas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ReportSummaryItem(BaseModel):
    name: str = Field(..., description="Unique filename slug (e.g. consolidated_test_report)")
    title: str = Field(..., description="Human-readable title")
    type: str = Field("markdown", description="Report format type")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    run_id: Optional[str] = Field(None, description="Linked run ID if applicable")
    file_size: Optional[int] = Field(None, description="Size in bytes")


class ReportListResponse(BaseModel):
    reports: List[ReportSummaryItem] = Field(default_factory=list)


class ReportCoverageTest(BaseModel):
    tc_id: str
    result: str = "not_run"


class ReportCoverageItem(BaseModel):
    req_id: str
    heading: str
    tests: List[ReportCoverageTest] = Field(default_factory=list)
    bugs: List[str] = Field(default_factory=list)
    status: Optional[str] = "uncovered"


class ReportSummaryStats(BaseModel):
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    iterations: int = 0
    total_time_s: int = 0


class ReportDetailResponse(BaseModel):
    report_name: str
    title: str
    content: str
    summary: Optional[ReportSummaryStats] = None
    coverage: Optional[List[ReportCoverageItem]] = None


class TraceabilitySymbol(BaseModel):
    file_path: str
    symbol_name: str
    start_line: int
    end_line: int


class TraceabilityCoverageItem(BaseModel):
    req_id: str
    heading: str
    description: Optional[str] = ""
    code_symbols: List[TraceabilitySymbol] = Field(default_factory=list)
    test_cases: List[dict] = Field(default_factory=list)
    results: List[dict] = Field(default_factory=list)
    bugs: List[dict] = Field(default_factory=list)
    status: str = "uncovered"


class TraceabilityResponse(BaseModel):
    project_id: str
    coverage: List[TraceabilityCoverageItem] = Field(default_factory=list)
    total_requirements: int = 0
    covered_by_code: int = 0
    covered_by_tests: int = 0
    passing_requirements: int = 0
