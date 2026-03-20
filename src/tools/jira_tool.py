"""Jira Tool Module"""


import os

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

JIRA_INSTANCE_URL = os.environ['JIRA_INSTANCE_URL']
JIRA_USERNAME = os.environ["JIRA_USERNAME"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
JIRA_PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]


@tool
def create_jira_ticket(summary: str, description: str, testcase_name: str) -> dict[str, str]:
    """
    Create a Jira ticket for a failed test case.

    Args:
        summary: Brief summary of the issue
        description: Detailed description of the failure
        testcase_name: Name of the failed test case

    Returns:
        Dictionary with ticket information
    """
    from jira import JIRA
    jira = JIRA(server=JIRA_INSTANCE_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))
    issue = jira.create_issue(project=JIRA_PROJECT_KEY, summary=summary, description=description, issuetype={'name': 'Task'})

    # Mock implementation for POC
    print("Jira called...")
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
