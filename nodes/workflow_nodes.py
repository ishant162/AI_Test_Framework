import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from state import TestLogState
from tools.jira_tool import jira_tools

load_dotenv()

api_key = os.environ['API_KEY']

# Initialize LLM
llm = ChatOpenAI(
    model="openai.gpt-5.1",  # Specify the OpenAI model you want to use
    base_url="https://openai.generative.engine.capgemini.com/v1",
    api_key=api_key,
    default_headers={"x-api-key": api_key}  # Some implementations require this header
)
llm_with_tools = llm.bind_tools(jira_tools)


def framework_log_analysis(state: TestLogState) -> TestLogState:
    """Analyze test framework logs to determine pass/fail status"""
    
    prompt = f"""
    <LOG>
        {state['log_content']}
    </LOG>
    """

    messages = [
        SystemMessage(
            content="""
                You are a log analyst. Your job is to determine test results from raw logs and return ONLY a strict JSON object.
                Decision rules (apply in order):
                1) If a “TEST EXECUTION SUMMARY” block with totals is present, trust it:
                - Parse “Total test cases:”, “Passed:”, “Failed:”, and “Pass rate:”.
                - overall_status = "ALL_PASSED" if Failed == 0 and Passed == Total; else "SOME_FAILED".
                2) If the summary block is missing, compute from per-test lines:
                - Parse only lines like: "Test case <NAME>: PASSED|FAILED|SKIPPED".
                - Ignore unrelated PASSED/FAILED occurrences such as “Output validation PASSED”.
                - total = number of unique <NAME>.
                - passed = count with PASSED; failed = count with FAILED; pass_rate = (passed/total)*100 rounded to 2 decimals.
                - overall_status = "ALL_PASSED" if failed == 0 and passed == total; else "SOME_FAILED".
                3) If neither summary nor per-test lines are present, return overall_status="UNKNOWN" with reason.

                Output schema (STRICT JSON, no extra text):
                {
                "overall_status": "ALL_PASSED" | "SOME_FAILED" | "UNKNOWN",
                "total": number | null,
                "passed": number | null,
                "failed": number | null,
                "pass_rate": number | null,
                "failed_tests": string[],            // e.g., ["TC_3", "Login_Edge_01"]
                "per_test": { [testName: string]: "PASSED" | "FAILED" | "SKIPPED" },  // optional when summary exists
                "notes": string                      // brief explanation of which rule was used
                }

                Be tolerant to capitalization and spacing. Treat repeated lines as duplicates and prefer the last summary if multiple appear. If counts are inconsistent, prefer the latest summary; otherwise compute from per-test lines and note the discrepancy.

                Now analyze the logs between <LOG> ... </LOG> and return ONLY the JSON object.
            """),
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