"""Memory Nodes Module"""

import uuid

from src.state.state import TestLogState
from src.vectorstore.vector_retrieval import VectorRetriever

# Initialize retriever
retriever = VectorRetriever()


def retrieve_historical_context(state: TestLogState, config: dict) -> TestLogState:
    """Retrieve similar past failures (Semantic Memory) and global tips (Global Store)."""

    # 1. Semantic Memory Retrieval (ChromaDB)
    semantic_context = ""
    try:
        search_results = retriever.retrieve(state["log_content"], top_k=2)
        if search_results.get("results"):
            semantic_context = "\n--- Semantic Memory (Similar Past Failures) ---\n"
            for res in search_results["results"]:
                semantic_context += f"Past Issue: {res['document']}\n"
                meta = res.get("metadata", {})
                semantic_context += f"Summary: {meta.get('summary', 'N/A')}\n"
                semantic_context += f"Causality: {meta.get('causality', 'N/A')}\n\n"
    except Exception as e:
        semantic_context = f"\n(Semantic retrieval unavailable: {str(e)})\n"

    # 2. Global Knowledge Memory (LangGraph Store)
    store = config.get("store")
    global_tips = ""
    if store and state.get("failed_testcases"):
        global_tips = "\n--- Global Knowledge Store (Known Tips) ---\n"
        for testcase in state["failed_testcases"]:
            tip = store.get(("global_tips",), testcase)
            if tip:
                global_tips += (
                    f"Tip for {testcase}: {tip.value.get('analysis', 'No details')}\n"
                )

    state["historical_context"] = f"{semantic_context}\n{global_tips}".strip()
    return state


def commit_to_memory(state: TestLogState, config: dict) -> TestLogState:
    """Commit current analysis to Global Store and Semantic Memory."""

    # 1. Update Global Knowledge Store (LangGraph Store)
    store = config.get("store")
    if store and state.get("failed_testcases") and state.get("failure_report"):
        for testcase in state["failed_testcases"]:
            store.put(("global_tips",), testcase, {"analysis": state["failure_report"]})

    # 2. Update Semantic Memory (ChromaDB)
    if state.get("log_content") and state.get("failure_report"):
        try:
            # Generate embedding for the current failed log
            query_vec = retriever.embed_query(state["log_content"])

            # Prepare metadata for semantic storage
            # We use a summary of the failure report as the 'summary' and 'causality'
            metadata = {
                "template": state["log_content"][
                    :500
                ],  # Store snippet of log as template
                "severity": "high" if state.get("test_status") == "failed" else "low",
                "summary": state["failure_report"][:200],  # Brief summary of analysis
                "causality": state["failure_report"][
                    :500
                ],  # Full analysis as causality
            }

            # Persist to ChromaDB via the retriever's collection
            retriever.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[query_vec.tolist()],
                metadatas=[metadata],
                documents=[state["log_content"]],
            )
            print("[MemoryNode] Successfully committed log to Semantic Memory.")
        except Exception as e:
            print(f"[MemoryNode] Failed to commit to Semantic Memory: {str(e)}")

    return state
