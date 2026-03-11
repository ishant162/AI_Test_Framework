"""Context Builder Nodes Module"""


import json
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.gen_engine_llm import llm
from src.state.state import ContextBuilderState
from src.utils.utils import extract_and_parse_json
from config.context_building_prompts import template_extraction_prompt, template_enrichment_prompt


# LLM Log Parsing Node
def llm_log_parsing_node(state: ContextBuilderState) -> ContextBuilderState:
    """Phase 01: Extract structural templates and metadata using an LLM"""

    user_prompt = f"Here are the logs to parse:\n\n{state['log_content']}"
    if state.get('parsing_guidance'):
        user_prompt += f"\n\nAdditional Guidance: {state['parsing_guidance']}"
        
    response = llm.invoke([
        SystemMessage(content=template_extraction_prompt),
        HumanMessage(content=user_prompt)
    ])

    templates = extract_and_parse_json(response.content)

    if templates and isinstance(templates, list):
        state['extracted_templates'] = templates
        state['messages'].append(f"LLM successfully extracted {len(templates)} unique templates.")
    else:
        state['extracted_templates'] = []
        state['messages'].append("LLM failed to extract structured templates.")

    # Domain annotator
    state = domain_annotator(state)

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

def domain_annotator(state: ContextBuilderState) -> ContextBuilderState:
    """Enrich extracted templates with severity, causality, summary, and variables"""

    if not state.get('extracted_templates'):
        state['messages'].append("Domain annotator skipped: no extracted templates found.")
        return state

    enrichment_user_prompt = (
        f"Here are the extracted log templates to enrich:\n\n"
        f"{json.dumps(state['extracted_templates'], indent=2)}"
    )

    response = llm.invoke([
        SystemMessage(content=template_enrichment_prompt),
        HumanMessage(content=enrichment_user_prompt)
    ])

    enriched_templates = extract_and_parse_json(response.content)

    if enriched_templates and isinstance(enriched_templates, list):
        state['extracted_templates'] = enriched_templates
        state['messages'].append(f"Domain annotator successfully enriched {len(enriched_templates)} templates.")
    else:
        state['messages'].append("Domain annotator failed to enrich templates. Keeping original extracted templates.")
    
    # TODO: Add Human in the loop for SME and validate if the data is related properly with the domain

    return state
