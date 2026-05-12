"""Log Analysis Workflow Module"""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.store.memory import InMemoryStore

from src.nodes.analysis_workflow_nodes import (
    execution_layer,
    failure_analysis,
    framework_log_analysis,
    pass_analysis,
    route_after_analysis,
    route_after_execution,
    tools_and_capture,
)

# New nodes for memory implementation
from src.nodes.memory_nodes import (
    commit_to_memory,
    retrieve_historical_context,
)
from src.state.state import TestLogState

# Initialize SQLite checkpointer for Long-Term Memory (History)
conn = sqlite3.connect("memory.db", check_same_thread=False)
memory_saver = SqliteSaver(conn)

# Initialize Global Knowledge Store (InMemoryStore)
global_store = InMemoryStore()


def create_workflow():
    """Create and compile the LangGraph workflow with memory layers."""

    # Initialize graph with state schema
    workflow = StateGraph(TestLogState)

    # Add nodes
    workflow.add_node("framework_log_analysis", framework_log_analysis)
    workflow.add_node("pass_analysis", pass_analysis)

    # Memory retrieval node
    workflow.add_node("retrieve_historical_context", retrieve_historical_context)

    workflow.add_node("failure_analysis", failure_analysis)
    workflow.add_node("execution_layer", execution_layer)
    workflow.add_node("tools", tools_and_capture)

    # Memory commit node (after analysis/action)
    workflow.add_node("commit_to_memory", commit_to_memory)

    # Set entry point
    workflow.set_entry_point("framework_log_analysis")

    # Add conditional edges
    workflow.add_conditional_edges(
        "framework_log_analysis",
        route_after_analysis,
        {
            "pass_analysis": "pass_analysis",
            "failure_analysis": "retrieve_historical_context",  # Route to retrieval before analysis
        },
    )

    # Retrieval flows into failure analysis
    workflow.add_edge("retrieve_historical_context", "failure_analysis")

    # Pass analysis goes to end
    workflow.add_edge("pass_analysis", END)

    # Failure analysis goes to execution layer
    workflow.add_edge("failure_analysis", "execution_layer")

    # Execution layer conditional routing
    workflow.add_conditional_edges(
        "execution_layer",
        route_after_execution,
        {"tools": "tools", "end": "commit_to_memory"},  # Commit to memory before ending
    )

    # Tools go back to end (via commit_to_memory)
    workflow.add_edge("tools", "commit_to_memory")

    # Final step: Commit to memory and then end
    workflow.add_edge("commit_to_memory", END)

    # Compile with memory saver (Long-Term Memory) and global store
    app = workflow.compile(checkpointer=memory_saver, store=global_store)

    return app


if __name__ == "__main__":
    # Example usage
    app = create_workflow()

    config = {"configurable": {"thread_id": "project_alpha"}}

    # Sample run
    # initial_state = {"log_content": "..."}
    # result = app.invoke(initial_state, config=config)

    # Sample test log
    with open("./data/test_framework_fail.log") as f:
        sample_log = f.read()

    # sample_log = """
    # [2024-06-01 10:23:44] TESTCASE: test_login FAILED
    # Error: Timeout waiting for response
    # Stacktrace: file.py line 22
    # ------------------------------------------------
    # [2024-06-01 10:23:50] TESTCASE: test_signup PASSED
    # """

    # Run workflow
    initial_state = {
        "log_content": sample_log,
        "test_status": None,
        "failed_testcases": None,
        "summary_report": None,
        "failure_report": None,
        "action_plan": None,
        "jira_tickets": None,
        "messages": [],
    }

    result = app.invoke(initial_state)

    if result.get("summary_report", ""):
        print(f"\nSummary report:\n{result['summary_report']}")

    if result.get("jira_tickets", []):
        print(f"\njira_tickets:\n{result['jira_tickets']}")
