"""Workflow States Module"""

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TestLogState(TypedDict):
    """State schema for test log analysis workflow"""

    # Input
    log_content: str

    # Analysis results
    test_status: Literal["passed", "failed"] | None
    failed_testcases: list[str] | None

    # Reports
    summary_report: str | None
    failure_report: str | None

    # Actions
    action_plan: str | None
    jira_tickets: list[dict[str, str]] | None

    # Messages for LLM
    messages: Annotated[list[BaseMessage], add_messages]


class ContextBuilderState(TypedDict):
    """State schema for the Context Builder workflow"""

    # Input
    log_content: str
    parsing_guidance: str | None
    sme_excel_path: str | None

    # Phase 01: Ingestion Results (LLM-Driven)
    extracted_templates: list[dict[str, Any]] | None

    # Human in the loop
    review_approved: bool
    review_comments: str | None

    # Phase 02: Augmentation Results
    augmented_data: list[dict[str, Any]] | None

    # Phase 03: Vectorization Results
    vector_ids: list[str] | None

    # Messages for tracking progress
    messages: list[str]
