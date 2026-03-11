"""Log Analysis Nodes Module"""


import json
from typing import Dict, List, Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage

from config.log_analysis_prompts import log_analysis_system_prompt

from src.state.state import TestLogState
from src.tools.jira_tool import jira_tools
from src.llm.gen_engine_llm import llm


def framework_log_analysis(state: TestLogState) -> TestLogState:
    """Analyze test framework logs to determine pass/fail status"""
    
    prompt = f"""
    <LOG>
        {state['log_content']}
    </LOG>
    """

    messages = [
        SystemMessage(
            content=log_analysis_system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Parse response to determine status
    response_text = response.content.lower()
    response_json = json.loads(response_text)
    if response_json['overall_status'] == "all_passed":
        status = "passed"
        failed_tests = []
    else:
        status = "failed"
        # Extract failed test cases (simplified parsing)
        failed_tests = response_json.get('failed_tests')
    
    state['test_status'] = status
    state['failed_testcases'] = failed_tests if failed_tests else None
    state['messages'] = [{"role": "assistant", "content": response.content}]
    
    return state


def pass_analysis(state: TestLogState) -> TestLogState:
    """Generate summary report for passed tests"""
    
    prompt = f"""All test cases have passed! Generate a concise summary report.

    Test Log:
    {state['log_content']}

    Include:
    - Total number of tests
    - Execution time (if available)
    - Key highlights"""

    messages = [
        SystemMessage(content="You are generating a test execution summary report."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    state['summary_report'] = response.content
    
    return state


def failure_analysis(state: TestLogState) -> TestLogState:
    """Generate failure analysis report"""
    
    prompt = f"""Analyze the failed test cases and generate a detailed failure report.

    Test Log:
    {state['log_content']}

    Failed Test Cases:
    {chr(10).join(state['failed_testcases']) if state['failed_testcases'] else 'None identified'}

    Include:
    - List of failed tests
    - Failure reasons
    - Error messages
    - Potential root causes"""

    messages = [
        SystemMessage(content="You are analyzing test failures and generating diagnostic reports."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    state['failure_report'] = response.content
    
    return state


def execution_layer(state: TestLogState) -> TestLogState:
    """Plan actions and use tools to create Jira tickets"""

    llm_with_tools = llm.bind_tools(jira_tools)

    prompt = f"""
        Based on the following failed tests, create Jira tickets for each failure.
        Use the available create_jira_ticket TOOLS to create jira tickets for failed
        testcases.

        Failed Test Cases:
        {chr(10).join(state['failed_testcases']) if state.get('failed_testcases') else 'None'}

        Failure Report:
        {state.get('failure_report', '')}

        For each failed test, call the create_jira_ticket tool with:
        - summary: Brief issue summary
        - description: Detailed failure description
        - testcase_name: The test case name

        Create tickets now.
    """
    
    
    sys_msg = SystemMessage(content="You are creating Jira tickets for failed test cases. Use the create_jira_ticket tool for each failed test.")
    human_msg = HumanMessage(content=prompt)

    prior = state.get("messages", []) or []
    response = llm_with_tools.invoke(prior + [sys_msg, human_msg])

    # Explicitly set messages as BaseMessage objects (not dicts)
    state["messages"] = prior + [sys_msg, human_msg, response]
    state["action_plan"] = getattr(response, "content", str(response))
    return state


def route_after_analysis(state: TestLogState) -> str:
    """Route to pass or fail analysis based on test status"""
    if state['test_status'] == "passed":
        return "pass_analysis"
    else:
        return "failure_analysis"


def route_after_execution(state: TestLogState) -> str:
    """Check if tools need to be called"""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "end"


# Tool node for Jira
tool_node = ToolNode(jira_tools)


def _safe_to_dict(content: Any) -> Dict[str, Any]:
    """Convert tool call response content to dict"""
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}
    # Fallback if something exotic comes back
    return {"raw": str(content)}

def tools_and_capture(state: TestLogState) -> Dict[str, Any]:
    update = tool_node.invoke(state)

    # 2) Capture outputs from ToolMessages that came back in this update
    jira_results: List[Dict[str, Any]] = []
    for msg in update.get("messages", []):
        if isinstance(msg, ToolMessage) and getattr(msg, "name", None) == "create_jira_ticket":
            jira_results.append(_safe_to_dict(msg.content))

    # 3) If we found any, also return them as a state update
    if jira_results:
        update["jira_tickets"] = jira_results

    return update