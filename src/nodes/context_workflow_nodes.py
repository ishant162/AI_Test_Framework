"""Context Builder Nodes Module"""

import json
import os
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from config.context_building_prompts import (
    augmentation_prompt,
    template_enrichment_prompt,
    template_extraction_prompt,
)
from src.llm.gen_engine_llm import GenEngineLLM
from src.state.state import ContextBuilderState
from src.utils.utils import extract_and_parse_json


class ContextWorkflowNode:
    """Context Workflow node for building context from scratch"""

    def __init__(self, model=None):
        self.llm = GenEngineLLM().get_llm_model()

    # LLM Log Parsing Node
    def llm_log_parsing_node(self, state: ContextBuilderState) -> ContextBuilderState:
        """Phase 01: Extract structural templates and metadata using an LLM"""

        user_prompt = f"Here are the logs to parse:\n\n{state['log_content']}"
        if state.get("parsing_guidance"):
            user_prompt += f"\n\nAdditional Guidance: {state['parsing_guidance']}"

        response = self.llm.invoke(
            [
                SystemMessage(content=template_extraction_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        templates = extract_and_parse_json(response.content)

        if templates and isinstance(templates, list):
            state["extracted_templates"] = templates
            state["messages"].append(
                f"LLM successfully extracted {len(templates)} unique templates."
            )
        else:
            state["extracted_templates"] = []
            state["messages"].append("LLM failed to extract structured templates.")

        return state

    def domain_annotator_node(self, state: ContextBuilderState) -> ContextBuilderState:
        """Enrich extracted templates with severity, causality, summary, and variables"""

        # Load SME Reference Data
        sme_reference_text = "No SME reference data provided."
        if state.get("sme_excel_path") and os.path.exists(state["sme_excel_path"]):
            try:
                df = pd.read_excel(state["sme_excel_path"])
                sme_reference_text = df.to_json(orient="records")
                state["messages"].append(
                    f"Successfully loaded SME reference data from {state['sme_excel_path']}."
                )
            except Exception as e:
                state["messages"].append(f"Error loading SME Excel: {str(e)}")

        if not state.get("extracted_templates"):
            state["messages"].append(
                "Domain annotator skipped: no extracted templates found."
            )
            return state

        enrichment_user_prompt = (
            f"Here are the extracted log templates to enrich:\n\n"
            f"{json.dumps(state['extracted_templates'], indent=2)}"
        )

        response = self.llm.invoke(
            [
                SystemMessage(
                    content=template_enrichment_prompt.replace(
                        "{sme_reference_text}", sme_reference_text
                    )
                ),
                HumanMessage(content=enrichment_user_prompt),
            ]
        )

        enriched_templates = extract_and_parse_json(response.content)

        if enriched_templates and isinstance(enriched_templates, list):
            state["extracted_templates"] = enriched_templates
            state["messages"].append(
                f"Domain annotator successfully enriched {len(enriched_templates)} templates."
            )
        else:
            state["messages"].append(
                "Domain annotator failed to enrich templates. Keeping original extracted templates."
            )

        return state

    def human_review_node(self, state: Any) -> Any:
        """
        Human Review Entry Point.
        This node is reached AFTER the human provides input during the interrupt.
        """
        if state.get("review_approved"):
            state["messages"].append("Human review approved. Proceeding to next steps.")
        else:
            state["messages"].append(
                "Human review rejected or pending. Workflow paused/stopped."
            )
        return state

    def augmentation_node(self, state: ContextBuilderState) -> ContextBuilderState:
        """Phase 02: LLM-based augmentation with Faker-enhanced realism"""

        if not state.get("extracted_templates"):
            state["messages"].append(
                "Augmentation skipped: no extracted templates found."
            )
            return state

        state["messages"].append("Phase 02: Augmentation started..")

        augmentation_user_prompt = (
            f"Here are the enriched log templates to augment:\n\n"
            f"{json.dumps(state['extracted_templates'], indent=2)}"
        )

        # 1. LLM generates the structural variations and domain-specific context
        response = self.llm.invoke(
            [
                SystemMessage(content=augmentation_prompt),
                HumanMessage(content=augmentation_user_prompt),
            ]
        )

        augmented_templates = extract_and_parse_json(response.content)

        if augmented_templates and isinstance(augmented_templates, list):
            # Combine original and augmented data
            state["augmented_data"] = state["extracted_templates"] + augmented_templates
            state["messages"].append(
                f"Augmentation successfully generated {len(augmented_templates)} "
                " synthetic templates."
            )
        else:
            state["augmented_data"] = state["extracted_templates"]
            state["messages"].append(
                "Augmentation failed to generate synthetic templates. Using original data."
            )

        return state

    def vectorization_node(self, state: ContextBuilderState) -> ContextBuilderState:
        """Phase 03: Embedding, anomaly detection, clustering, vector storage"""

        from src.vectorstore.embedding_pipeline import EmbeddingPipeline

        templates = (
            state.get("augmented_data") or state.get("extracted_templates") or []
        )

        if not templates:
            state["messages"].append("No templates available for vectorization.")
            state["vector_ids"] = []
            return state

        try:
            pipeline = EmbeddingPipeline()
            ids = pipeline.run(templates)

            state["vector_ids"] = ids
            state["messages"].append(
                f"Embedding completed: {len(ids)} templates indexed for retrieval."
            )

        except Exception as e:
            state["messages"].append(f"Embedding failed: {str(e)}")
            state["vector_ids"] = []

        return state
