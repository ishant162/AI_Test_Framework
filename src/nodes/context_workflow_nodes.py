"""Context Builder Nodes Module"""

import json
import os
import time
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
from src.vectorstore.embedding_pipeline import EmbeddingPipeline


class ContextWorkflowNode:
    """Context Workflow node for building context from scratch"""

    def __init__(self):
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
        templates = state["extracted_templates"]

        # Batch Processing
        batch_size = (
            3  # Smaller batch size for augmentation as it generates more tokens
        )
        augmented_all = []

        for i in range(0, len(templates), batch_size):
            batch = templates[i : i + batch_size]
            prompt = f"Augment these templates:\n\n{json.dumps(batch, indent=2)}"

            # Retry Mechanism with Exponential Backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.llm.invoke(
                        [
                            SystemMessage(content=augmentation_prompt),
                            HumanMessage(content=prompt),
                        ]
                    )
                    augmented_batch = extract_and_parse_json(response.content)
                    if augmented_batch and isinstance(augmented_batch, list):
                        augmented_all.extend(augmented_batch)
                        break
                    else:
                        raise ValueError("Invalid JSON response")
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt
                        state["messages"].append(
                            f"Augmentation Retry "
                            f"{attempt + 1}/{max_retries} after {wait_time}s: {str(e)}"
                        )
                        time.sleep(wait_time)
                    else:
                        state["messages"].append(
                            f"Augmentation Batch "
                            f"{i // batch_size + 1} failed after {max_retries} attempts."
                        )
        if augmented_all:
            state["augmented_data"] = state["extracted_templates"] + augmented_all
            state["messages"].append(
                f"Augmentation successfully generated {len(augmented_all)} synthetic templates."
            )
        else:
            state["augmented_data"] = state["extracted_templates"]
            state["messages"].append(
                "Augmentation failed to generate synthetic templates. Using original data."
            )

        return state

    def vectorization_node(self, state: ContextBuilderState) -> ContextBuilderState:
        """Phase 03: Embedding, anomaly detection, clustering, vector storage"""

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
