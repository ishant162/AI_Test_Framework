from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from state import TestLogState
from tools.jira_tool import jira_tools

api_key = ""

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
    Analyze the following test framework log and determine if all test cases passed or if any failed.

    Test Log:
    {state['log_content']}

    Respond with:
    1. Overall status: "PASSED" or "FAILED"
    2. If failed, list the names of failed test cases

    Format your response clearly."""

    messages = [
        SystemMessage(content="You are a test automation expert analyzing test framework logs."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Parse response to determine status
    response_text = response.content.lower()
    if "overall status: \"passed\"" in response_text or "overall status: passed" in response_text:
        status = "passed"
        failed_tests = []
    else:
        status = "failed"
        # Extract failed test cases (simplified parsing)
        failed_tests = []
        lines = response.content.split('\n')
        for line in lines:
            if 'failed' in line.lower() and ('test' in line.lower() or 'case' in line.lower()):
                # Basic extraction - can be improved
                failed_tests.append(line.strip())
    
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
    
    prompt = f"""Based on the following failed tests, create Jira tickets for each failure.

    Failed Test Cases:
    {chr(10).join(state['failed_testcases']) if state['failed_testcases'] else 'None'}

    Failure Report:
    {state['failure_report']}

    For each failed test, call the create_jira_ticket tool with:
    - summary: Brief issue summary
    - description: Detailed failure description
    - testcase_name: The test case name

    Create tickets now."""

    messages = [
        SystemMessage(content="You are creating Jira tickets for failed test cases. Use the create_jira_ticket tool for each failed test."),
        HumanMessage(content=prompt)
    ]
    
    response = llm_with_tools.invoke(messages)
    state['messages'] = [{"role": "user", "content": prompt}, {"role": "assistant", "content": str(response)}]
    
    # Store the LLM response that may contain tool calls
    state['action_plan'] = str(response.content) if hasattr(response, 'content') else str(response)
    
    return state


# Tool node for Jira
tool_node = ToolNode(jira_tools)


def route_after_analysis(state: TestLogState) -> str:
    """Route to pass or fail analysis based on test status"""
    if state['test_status'] == "passed":
        return "pass_analysis"
    else:
        return "failure_analysis"


def route_after_execution(state: TestLogState) -> str:
    """Check if tools need to be called"""
    last_message = state['messages'][-1] if state['messages'] else {}
    
    # Check if the last message has tool calls
    if isinstance(last_message, dict) and 'tool_calls' in str(last_message):
        return "tools"
    return "end"