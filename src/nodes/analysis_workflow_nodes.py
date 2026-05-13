"""Log Analysis Nodes Module"""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from config.log_analysis_prompts import log_analysis_system_prompt
from src.llm.gen_engine_llm import GenEngineLLM
from src.state.state import TestLogState
from src.tools.jira_tool import jira_tools

llm = GenEngineLLM().get_llm_model()


def framework_log_analysis(state: TestLogState) -> TestLogState:
    """Analyze test framework logs to determine pass/fail status"""

    prompt = f"""
    <LOG>
        {state["log_content"]}
    </LOG>
    """

    messages = [
        SystemMessage(content=log_analysis_system_prompt),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)

    # Parse response to determine status
    try:
        response_json = json.loads(response.content)
        status = "passed" if response_json.get("overall_status") == "ALL_PASSED" else "failed"
        failed_tests = response_json.get("failed_tests")
    except Exception:
        status = "failed"
        failed_tests = []

    state["test_status"] = status
    state["failed_testcases"] = failed_tests if failed_tests else None
    
    # Update messages for short-term history
    state["messages"] = [AIMessage(content=response.content)]

    return state


def pass_analysis(state: TestLogState) -> TestLogState:
    """Generate summary report for passed tests"""

    prompt = f"""All test cases have passed! Generate a concise summary report.

    Test Log:
    {state["log_content"]}

    Include:
    - Total number of tests
    - Execution time (if available)
    - Key highlights"""

    messages = [
        SystemMessage(content="You are generating a test execution summary report."),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    state["summary_report"] = response.content
    state["messages"] = [AIMessage(content=response.content)]

    return state


def failure_analysis(state: TestLogState) -> TestLogState:
    """Generate failure analysis report with historical context (Long-term memory)"""

    context_prompt = ""
    if state.get("historical_context"):
        context_prompt = f"\n\nUSE THIS HISTORICAL CONTEXT FROM PAST FAILURES TO ASSIST YOUR ANALYSIS:\n{state['historical_context']}"

    prompt = f"""Analyze the failed test cases and generate a detailed failure report.{context_prompt}

    Test Log:
    {state["log_content"]}

    Failed Test Cases:
    {chr(10).join(state["failed_testcases"]) if state["failed_testcases"] else "None identified"}

    Include:
    - List of failed tests
    - Failure reasons
    - Error messages
    - Potential root causes (leveraging historical context if relevant)"""

    messages = [
        SystemMessage(
            content="You are analyzing test failures and generating diagnostic reports."
        ),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    state["failure_report"] = response.content
    state["messages"] = [AIMessage(content=response.content)]

    return state


def execution_layer(state: TestLogState) -> TestLogState:
    """Plan actions and use tools to create Jira tickets with conversation context"""

    llm_with_tools = llm.bind_tools(jira_tools)

    prompt = f"""
        Based on the following failed tests and analysis, create Jira tickets.
        
        Failed Test Cases:
        {chr(10).join(state["failed_testcases"]) if state.get("failed_testcases") else "None"}

        Failure Report:
        {state.get("failure_report", "")}

        For each failed test, call the create_jira_ticket tool.
    """

    sys_msg = SystemMessage(
        content="You are creating Jira tickets for failed test cases. Use the create_jira_ticket tool for each failed test."
    )
    human_msg = HumanMessage(content=prompt)

    # Use existing message history for short-term context
    history = state.get("messages", [])
    response = llm_with_tools.invoke([sys_msg] + history + [human_msg])

    state["messages"] = [response]
    state["action_plan"] = getattr(response, "content", str(response))
    return state


def route_after_analysis(state: TestLogState) -> str:
    """Route to pass or fail analysis based on test status"""
    if state["test_status"] == "passed":
        return "pass_analysis"
    else:
        return "failure_analysis"


def route_after_execution(state: TestLogState) -> str:
    """Check if tools need to be called"""
    if not state["messages"]:
        return "end"
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "end"


# Tool node for Jira
tool_node = ToolNode(jira_tools)


def _safe_to_dict(content: Any) -> dict[str, Any]:
    """Convert tool call response content to dict"""
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}
    return {"raw": str(content)}


def tools_and_capture(state: TestLogState) -> dict[str, Any]:
    update = tool_node.invoke(state)

    jira_results: list[dict[str, Any]] = []
    for msg in update.get("messages", []):
        if (
            isinstance(msg, ToolMessage)
            and getattr(msg, "name", None) == "create_jira_ticket"
        ):
            jira_results.append(_safe_to_dict(msg.content))

    if jira_results:
        update["jira_tickets"] = jira_results

    return update
