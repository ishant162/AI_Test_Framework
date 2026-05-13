"""Memory Nodes Module"""

from src.state.state import TestLogState
from src.vectorstore.vector_retrieval import VectorRetriever

# Initialize retriever
retriever = VectorRetriever()


def retrieve_historical_context(state: TestLogState, config: dict) -> TestLogState:
    """Retrieve similar past failures (Semantic Memory) and global tips (Global Store)."""

    # 1. Semantic Memory Retrieval (ChromaDB)
    # Search for similar logs to the current log_content
    semantic_context = ""
    try:
        search_results = retriever.retrieve(state["log_content"], top_k=2)
        if search_results.get("results"):
            semantic_context = "\n--- Semantic Memory (Similar Past Failures) ---\n"
            for res in search_results["results"]:
                semantic_context += f"Past Issue: {res['document']}\n"
                # Matching metadata from embedding_pipeline.py: severity, summary, causality
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
            # Retrieve global tips stored under namespace ("global_tips",)
            tip = store.get(("global_tips",), testcase)
            if tip:
                global_tips += (
                    f"Tip for {testcase}: {tip.value.get('analysis', 'No details')}\n"
                )

    # Combine all retrieved context into state
    state["historical_context"] = f"{semantic_context}\n{global_tips}".strip()
    return state


def commit_to_memory(state: TestLogState, config: dict) -> TestLogState:
    """Commit current analysis to Global Store and Semantic Memory."""

    # 1. Update Global Knowledge Store
    store = config.get("store")
    if store and state.get("failed_testcases") and state.get("failure_report"):
        for testcase in state["failed_testcases"]:
            # Persist analysis as a global tip for future runs
            store.put(("global_tips",), testcase, {"analysis": state["failure_report"]})

    # 2. Update Semantic Memory (ChromaDB)
    # Note: In a production flow, this would trigger the embedding pipeline
    # to store the current log and its successful analysis.

    return state
