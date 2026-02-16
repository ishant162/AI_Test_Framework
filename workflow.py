from langgraph.graph import StateGraph, END
from state import TestLogState
from nodes.workflow_nodes import (
    framework_log_analysis,
    pass_analysis,
    failure_analysis,
    execution_layer,
    tool_node,
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
    workflow.add_node("tools", tool_node)
    
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
    sample_log = """
    Test Execution Report
    =====================
    test_login_success: PASSED
    test_login_invalid_credentials: PASSED
    test_checkout_process: FAILED - NullPointerException at line 45
    test_payment_gateway: FAILED - Connection timeout
    test_user_registration: PASSED
    
    Total: 5 tests, 3 passed, 2 failed
    """
    
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
    
    print("\n=== WORKFLOW RESULT ===")
    print(f"\nTest Status: {result.get('test_status')}")
    if result.get('summary_report'):
        print(f"\nSummary Report:\n{result['summary_report']}")
    if result.get('failure_report'):
        print(f"\nFailure Report:\n{result['failure_report']}")
    if result.get('action_plan'):
        print(f"\nAction Plan:\n{result['action_plan']}")
