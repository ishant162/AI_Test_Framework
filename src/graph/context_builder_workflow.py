from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from tools.log_parser import LogParser

# Define State for Context Builder
class ContextBuilderState(TypedDict):
    """State schema for the Context Builder workflow"""

    log_content: str
    custom_templates: Optional[List[Dict[str, str]]]

    extracted_templates: Optional[List[Dict[str, Any]]]

    augmented_data: Optional[List[Dict[str, Any]]]

    vector_ids: Optional[List[str]]

    messages: List[str]

def log_parsing_node(state: ContextBuilderState) -> ContextBuilderState:
    """Phase 01: Extract structural templates using Drain3"""
    
    log_lines = state['log_content'].split('\n')
    parser = LogParser()
    
    # Apply custom templates if provided
    if state.get('custom_templates'):
        parser.add_custom_templates(state['custom_templates'])
        
    templates = parser.parse_logs(log_lines)
    
    state['extracted_templates'] = templates
    state['messages'].append(f"Successfully extracted {len(templates)} unique templates.")
    
    return state

def augmentation_node(state: ContextBuilderState) -> ContextBuilderState:
    """Phase 02: LLM-based augmentation and domain knowledge injection (Placeholder)"""

    #TODO: To be implemented in Phase 2
    state['messages'].append("Phase 02: Augmentation started (Placeholder).")
    return state

def vectorization_node(state: ContextBuilderState) -> ContextBuilderState:
    """Phase 03: Vectorization and storage in ChromaDB (Placeholder)"""

    #TODO: To be implemented in Phase 3
    state['messages'].append("Phase 03: Vectorization started (Placeholder).")
    return state

# Create the Context Builder Graph
def create_context_builder_workflow():
    """Create and compile the Context Builder LangGraph workflow"""
    
    workflow = StateGraph(ContextBuilderState)
    
    # Add nodes
    workflow.add_node("log_parsing", log_parsing_node)
    workflow.add_node("augmentation", augmentation_node)
    workflow.add_node("vectorization", vectorization_node)
    
    # Set entry point
    workflow.set_entry_point("log_parsing")
    
    # Add edges
    workflow.add_edge("log_parsing", "augmentation")
    workflow.add_edge("augmentation", "vectorization")
    workflow.add_edge("vectorization", END)
    
    # Compile
    app = workflow.compile()
    
    return app

if __name__ == "__main__":
    # Example usage for testing Phase 01
    app = create_context_builder_workflow()
    
    sample_logs = """
    2023-10-01 10:00:01 INFO Connected to database at 192.168.1.1:5432
    2023-10-01 10:00:02 INFO Connected to database at 192.168.1.2:5432
    2023-10-01 10:00:05 ERROR User 123 failed login from 10.0.0.5
    2023-10-01 10:00:10 WARN Disk usage at 90% on /dev/sda1
    2023-10-01 10:00:15 WARN Disk usage at 95% on /dev/sdb1
    """
    
    initial_state = {
        "log_content": sample_logs,
        "custom_templates": [{"regex": r"User \d+ failed login", "label": "USER_LOGIN_FAILURE"}],
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
        print("\nExtracted Templates:")
        for t in result['extracted_templates']:
            print(f"Source: {t['source']} | Template: {t['template']} | Count: {t['count']}")
