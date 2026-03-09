from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.gen_engine_llm import llm
from src.state.state import ContextBuilderState
from src.utils.utils import extract_and_parse_json


# LLM Log Parsing Node
def llm_log_parsing_node(state: ContextBuilderState) -> ContextBuilderState:
    """Phase 01: Extract structural templates and metadata using an LLM"""
    system_prompt = """
    You are an expert log analyst. Your task is to parse a set of raw logs and extract unique structural templates.
    For each unique log pattern, provide:
    1. template: A generalized version of the log (e.g., use placeholders like <IP>, <USER_ID>, <TIMESTAMP>).
    2. severity: (INFO, WARN, ERROR, CRITICAL) based on the log content.
    3. causality: (Network, Auth, Database, Application, System) - the likely category of the log.
    4. summary: A brief, human-readable summary of what this log pattern means.
    5. variables: A few examples of variable values extracted from the logs for this template.

    Return the result as a JSON list of objects.
    """
    
    user_prompt = f"Here are the logs to parse:\n\n{state['log_content']}"
    if state.get('parsing_guidance'):
        user_prompt += f"\n\nAdditional Guidance: {state['parsing_guidance']}"
        
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    templates = extract_and_parse_json(response.content)
    
    if templates and isinstance(templates, list):
        state['extracted_templates'] = templates
        state['messages'].append(f"LLM successfully extracted {len(templates)} unique templates.")
    else:
        state['extracted_templates'] = []
        state['messages'].append("LLM failed to extract structured templates.")
    
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