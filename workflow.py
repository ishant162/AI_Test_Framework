from langgraph.graph import StateGraph, END
from state import TestLogState
from nodes.workflow_nodes import (
    framework_log_analysis,
    pass_analysis,
    failure_analysis,
    execution_layer,
    tools_and_capture,
    route_after_analysis,
    route_after_execution
)


def create_workflow():
    """Create and compile the LangGraph workflow"""
    
    # Initialize graph
    workflow = StateGraph(TestLogState)
    
    # Add nodes
    workflow.add_node("framework_log_analysis", framework_log_analysis)
    workflow.add_node("pass_analysis", pass_analysis)
    workflow.add_node("failure_analysis", failure_analysis)
    workflow.add_node("execution_layer", execution_layer)
    workflow.add_node("tools", tools_and_capture)   
    
    # Set entry point
    workflow.set_entry_point("framework_log_analysis")
    # Add conditional edges
    workflow.add_conditional_edges(
        "framework_log_analysis",
        route_after_analysis,
        {
            "pass_analysis": "pass_analysis",
            "failure_analysis": "failure_analysis"
        }
    )
    # Pass analysis goes to end
    workflow.add_edge("pass_analysis", END)
    # Failure analysis goes to execution layer
    workflow.add_edge("failure_analysis", "execution_layer")
    # Execution layer conditional routing
    workflow.add_conditional_edges(
        "execution_layer",
        route_after_execution,
        {
            "tools": "tools",
            "end": END
        }
    )
    # Tools go back to end
    workflow.add_edge("tools", END)

    # Compile
    app = workflow.compile()
    
    return app


if __name__ == "__main__":
    # Example usage
    app = create_workflow()
    
    # Sample test log
    with open("./data/test_framework_fail.log", "r") as f:
        sample_log = f.read()
    
    # Run workflow
    initial_state = {
        "log_content": sample_log,
        "test_status": None,
        "failed_testcases": None,
        "summary_report": None,
        "failure_report": None,
        "action_plan": None,
        "jira_tickets": None,
        "messages": []
    }
    
    result = app.invoke(initial_state)
    
    if result.get('summary_report', ""):
        print(f"\nSummary report:\n{result['summary_report']}")
    
    if result.get('jira_tickets', []):
        print(f"\njira_tickets:\n{result['jira_tickets']}")
