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

# Initialize SQLite checkpointer for Short-Term Memory (Thread Persistence)
conn = sqlite3.connect("memory.db", check_same_thread=False)
memory_saver = SqliteSaver(conn)

# Initialize Global Knowledge Store (Long-Term Cross-Thread Memory)
global_store = InMemoryStore()


def create_workflow():
    """Create and compile the LangGraph workflow with full memory integration."""

    workflow = StateGraph(TestLogState)

    # Core Analysis Nodes
    workflow.add_node("framework_log_analysis", framework_log_analysis)
    workflow.add_node("pass_analysis", pass_analysis)
    workflow.add_node("failure_analysis", failure_analysis)

    # Tool & Execution Nodes
    workflow.add_node("execution_layer", execution_layer)
    workflow.add_node("tools", tools_and_capture)

    # Memory Management Nodes
    workflow.add_node("retrieve_historical_context", retrieve_historical_context)
    workflow.add_node("commit_to_memory", commit_to_memory)

    # Workflow Definition
    workflow.set_entry_point("framework_log_analysis")

    workflow.add_conditional_edges(
        "framework_log_analysis",
        route_after_analysis,
        {
            "pass_analysis": "pass_analysis",
            "failure_analysis": "retrieve_historical_context",
        },
    )

    # Historical context retrieval before failure analysis
    workflow.add_edge("retrieve_historical_context", "failure_analysis")
    workflow.add_edge("failure_analysis", "execution_layer")

    # Execution layer routing
    workflow.add_conditional_edges(
        "execution_layer",
        route_after_execution,
        {"tools": "tools", "end": "commit_to_memory"},
    )

    # Tool execution results back to memory commit
    workflow.add_edge("tools", "commit_to_memory")

    # Pass analysis directly to memory commit
    workflow.add_edge("pass_analysis", "commit_to_memory")

    # Final Step: Persist everything and end
    workflow.add_edge("commit_to_memory", END)

    # Compile with checkpointer (short-term) and store (long-term/global)
    app = workflow.compile(checkpointer=memory_saver, store=global_store)

    return app


if __name__ == "__main__":
    app = create_workflow()

    # Thread ID enables short-term checkpointed memory
    config = {"configurable": {"thread_id": "test_session_001"}}

    initial_state = {"log_content": "Sample log data...", "messages": []}

    # Workflow invocation with memory config
    # result = app.invoke(initial_state, config=config)
