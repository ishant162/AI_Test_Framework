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
from src.nodes.memory_nodes import (
    commit_to_memory,
    retrieve_historical_context,
)
from src.state.state import TestLogState

# 1. Long-Term Memory: Thread Persistence (SQLite)
conn = sqlite3.connect("memory.db", check_same_thread=False)
memory_saver = SqliteSaver(conn)

# 2. Short-Term Memory: Global Knowledge Store (InMemoryStore)
global_store = InMemoryStore()

def create_workflow():
    """Create and compile the LangGraph workflow with corrected memory layers."""

    workflow = StateGraph(TestLogState)

    # Nodes
    workflow.add_node("framework_log_analysis", framework_log_analysis)
    workflow.add_node("pass_analysis", pass_analysis)
    workflow.add_node("failure_analysis", failure_analysis)
    workflow.add_node("execution_layer", execution_layer)
    workflow.add_node("tools", tools_and_capture)
    workflow.add_node("retrieve_historical_context", retrieve_historical_context)
    workflow.add_node("commit_to_memory", commit_to_memory)

    # Workflow
    workflow.set_entry_point("framework_log_analysis")

    workflow.add_conditional_edges(
        "framework_log_analysis",
        route_after_analysis,
        {
            "pass_analysis": "pass_analysis",
            "failure_analysis": "retrieve_historical_context",
        },
    )

    # Pass Path: Analysis -> Commit -> End
    workflow.add_edge("pass_analysis", "commit_to_memory")

    # Fail Path: Retrieval -> Analysis -> Execution -> (Tools) -> Commit -> End
    workflow.add_edge("retrieve_historical_context", "failure_analysis")
    workflow.add_edge("failure_analysis", "execution_layer")

    workflow.add_conditional_edges(
        "execution_layer",
        route_after_execution,
        {
            "tools": "tools", 
            "end": "commit_to_memory"
        },
    )

    workflow.add_edge("tools", "commit_to_memory")
    workflow.add_edge("commit_to_memory", END)

    # Compile with Long-Term (saver) and Short-Term (store)
    return workflow.compile(checkpointer=memory_saver, store=global_store)

if __name__ == "__main__":
    # --- RUNNABLE SAMPLE CODE ---
    app = create_workflow()
    
    # Configuration for Long-Term Thread Persistence
    config = {"configurable": {"thread_id": "sample_run_001"}}
    
    # Sample Failed Log
    sample_log = """
    [2024-06-01 10:00:00] TESTCASE: test_api_connection FAILED
    Error: Connection timeout after 30s
    Stacktrace: api_client.py:45
    """
    
    print("--- Starting Workflow Execution ---")
    initial_state = {
        "log_content": sample_log,
        "messages": []
    }
    
    # Execute workflow
    result = app.invoke(initial_state, config=config)
    
    print("\n[Status]:", result.get("test_status"))
    if result.get("failure_report"):
        print("\n[Failure Report]:\n", result["failure_report"])
    if result.get("jira_tickets"):
        print("\n[Jira Tickets]:", result["jira_tickets"])
    
    print("\n--- Workflow Execution Complete ---")