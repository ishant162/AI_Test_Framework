from langchain_core.tools import tool
from typing import Dict


@tool
def create_jira_ticket(summary: str, description: str, testcase_name: str) -> Dict[str, str]:
    """
    Create a Jira ticket for a failed test case.
    
    Args:
        summary: Brief summary of the issue
        description: Detailed description of the failure
        testcase_name: Name of the failed test case
    
    Returns:
        Dictionary with ticket information
    """
    # TODO: Replace with actual Jira API implementation
    # from jira import JIRA
    # jira = JIRA(server='https://your-domain.atlassian.net', basic_auth=('email', 'api_token'))
    # issue = jira.create_issue(project='PROJECT_KEY', summary=summary, description=description, issuetype={'name': 'Bug'})
    
    # Mock implementation for POC
    ticket_id = f"TEST-{hash(testcase_name) % 10000}"
    
    return {
        "ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "testcase": testcase_name,
        "status": "created"
    }


# Tool list for LangGraph
jira_tools = [create_jira_ticket]