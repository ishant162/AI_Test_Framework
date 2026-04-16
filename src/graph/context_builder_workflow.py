"""Context Builder Workflow Module"""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
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
    workflow.add_node("domain_annotator", context_workflow_node.domain_annotator_node)
    workflow.add_node("human_review", context_workflow_node.human_review_node)
    workflow.add_node("augmentation", context_workflow_node.augmentation_node)
    workflow.add_node("vectorization", context_workflow_node.vectorization_node)

    # Set entry point
    workflow.set_entry_point("llm_log_parsing")

    # Add edges
    workflow.add_edge("llm_log_parsing", "domain_annotator")
    workflow.add_edge("domain_annotator", "human_review")
    workflow.add_edge("human_review", "augmentation")
    workflow.add_edge("augmentation", "vectorization")
    workflow.add_edge("vectorization", END)

    # Use MemorySaver for persistence and interrupts
    memory = MemorySaver()

    # Compile with interrupt BEFORE human_review
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_review"])

    return app


def run_cli_review(app, thread_id: str, initial_state: dict[str, Any]):
    """Helper function to run the workflow with CLI-based HITL review"""
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Start the workflow
    print("\n--- Starting Context Builder Workflow ---")
    for event in app.stream(initial_state, config):
        for node, state in event.items():
            print(f"Node '{node}' completed.")

    # 2. Check if we are at the interrupt point
    state = app.get_state(config)
    if state.next and "human_review" in state.next:
        print("\n--- HUMAN REVIEW REQUIRED ---")
        templates = state.values.get("extracted_templates", [])

        if not templates:
            print("No templates found to review.")
            app.update_state(config, {"review_approved": False}, as_node="human_review")
        else:
            print(f"Please review the following {len(templates)} templates:")
            for i, t in enumerate(templates):
                print(f"\nTemplate {i + 1}:")
                print(f"  Pattern:  {t.get('template')}")
                print(f"  Severity: {t.get('severity', 'N/A')}")
                print(f"  Category: {t.get('causality', 'N/A')}")
                print(f"  Summary:  {t.get('summary', 'N/A')}")

            # CLI Interaction
            choice = input("\nApprove these templates? (y/n/edit): ").lower()

            if choice == "y":
                app.update_state(
                    config, {"review_approved": True}, as_node="human_review"
                )
            elif choice == "edit":
                idx = int(input("Enter template number to edit (1-N): ")) - 1
                if 0 <= idx < len(templates):
                    field = input(
                        "Enter field to edit (Severity/Category/summary): "
                    ).lower()
                    new_val = input(f"Enter new value for {field}: ")
                    templates[idx][field] = new_val
                    app.update_state(
                        config,
                        {"extracted_templates": templates, "review_approved": True},
                        as_node="human_review",
                    )
                else:
                    print("Invalid index.")
                    app.update_state(
                        config, {"review_approved": False}, as_node="human_review"
                    )
            else:
                app.update_state(
                    config, {"review_approved": False}, as_node="human_review"
                )

        # 3. Resume the workflow
        print("\n--- Resuming Workflow ---")
        for event in app.stream(None, config):
            for node, state in event.items():
                print(f"Node '{node}' completed.")

    final_state = app.get_state(config).values
    return final_state


if __name__ == "__main__":
    # Initialize the workflow
    app = create_context_builder_workflow()

    # Load your logs
    with open("./data/sample.log") as f:
        sample_logs = f.read()

    # 3. Define initial state
    initial_state = {
        "log_content": sample_logs,
        "parsing_guidance": "",
        "sme_excel_path": "",
        "extracted_templates": None,
        "review_approved": False,
        "messages": [],
    }

    # Use the helper function to run the workflow with CLI review
    # This single call handles the start, the interrupt, the CLI interaction, and the resume.
    final_result = run_cli_review(
        app=app, thread_id="context_build_001", initial_state=initial_state
    )

    def display_context_builder_state(state: dict):
        print("\n=== ContextBuilderState ===")
        for key, value in state.items():
            print(f"\n▶ {key}")
            print("-" * (len(key) + 4))

            if isinstance(value, list):
                for idx, item in enumerate(value):
                    print()
                    print(f"  [{idx}] {item}")
                    print()
            else:
                print()
                print(f"  {value}")
                print()

    # Usage
    display_context_builder_state(final_result)
    print("Workflow Executed")
