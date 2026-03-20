"""Context Builder Workflow Module"""


import json

from langgraph.graph import END, StateGraph

from src.nodes.context_workflow_nodes import ContextWorkflowNode
from src.state.state import ContextBuilderState


# Create the Context Builder Graph
def create_context_builder_workflow():
    """Create and compile the Context Builder LangGraph workflow"""

    workflow = StateGraph(ContextBuilderState)
    context_workflow_node = ContextWorkflowNode()

    # Add nodes
    workflow.add_node("llm_log_parsing", context_workflow_node.llm_log_parsing_node)
    workflow.add_node("augmentation", context_workflow_node.augmentation_node)
    workflow.add_node("vectorization", context_workflow_node.vectorization_node)

    # Set entry point
    workflow.set_entry_point("llm_log_parsing")

    # Add edges
    workflow.add_edge("llm_log_parsing", "augmentation")
    workflow.add_edge("augmentation", "vectorization")
    workflow.add_edge("vectorization", END)

    # Compile
    app = workflow.compile()

    return app

if __name__ == "__main__":
    # Example usage for testing Phase 01
    app = create_context_builder_workflow()

    with open("./data/sample.log") as f:
        sample_logs = f.read()

    initial_state = {
        "log_content": sample_logs,
        "parsing_guidance": "",
        "sme_excel_path": None,
        "extracted_templates": None,
        "augmented_data": None,
        "vector_ids": None,
        "messages": []
    }

    result = app.invoke(initial_state)

    print("\nWorkflow Execution Log:")
    for msg in result['messages']:
        print(f"- {msg}")

    if result['extracted_templates']:
        print("\nExtracted Templates (LLM-Driven):")
        print(json.dumps(result['extracted_templates'], indent=2))
