from typing import TypedDict, Literal, List, Dict, Optional


class TestLogState(TypedDict):
    """State schema for test log analysis workflow"""
    
    # Input
    log_content: str
    
    # Analysis results
    test_status: Optional[Literal["passed", "failed"]]
    failed_testcases: Optional[List[str]]
    
    # Reports
    summary_report: Optional[str]
    failure_report: Optional[str]
    
    # Actions
    action_plan: Optional[str]
    jira_tickets: Optional[List[Dict[str, str]]]
    
    # Messages for LLM
    messages: List[Dict[str, str]]