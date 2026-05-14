"""Memory Nodes Module"""

import uuid
from typing import Any
from src.state.state import TestLogState
from src.vectorstore.vector_retrieval import VectorRetriever

# Initialize retriever
retriever = VectorRetriever()

def retrieve_historical_context(state: TestLogState, config: dict[str, Any] = None) -> dict[str, Any]:
    """Retrieve semantic context and global store tips."""
    
    # Ensure config is available
    config = config or {}

    # 1. Semantic Memory (ChromaDB)
    semantic_context = ""
    try:
        search_results = retriever.retrieve(state["log_content"], top_k=2)
        if search_results.get("results"):
            semantic_context = "\n--- Semantic Memory (ChromaDB) ---\n"
            for res in search_results["results"]:
                semantic_context += f"Past Issue: {res['document']}\n"
                meta = res.get('metadata', {})
                semantic_context += f"Resolution/Analysis: {meta.get('summary', 'N/A')}\n\n"
    except Exception as e:
        semantic_context = f"\n(Semantic retrieval unavailable: {str(e)})\n"

    # 2. Short-Term Memory (Global Knowledge Store)
    store = config.get("store")
    global_tips = ""
    if store and state.get("failed_testcases"):
        global_tips = "\n--- Short-Term Memory (Global Tips) ---\n"
        for testcase in state["failed_testcases"]:
            tip = store.get(("global_tips",), testcase)
            if tip:
                global_tips += f"Tip for {testcase}: {tip.value.get('analysis', 'No details')}\n"

    return {"historical_context": f"{semantic_context}\n{global_tips}".strip()}

def commit_to_memory(state: TestLogState, config: dict[str, Any] = None) -> dict[str, Any]:
    """Commit current analysis to Global Store and Semantic Memory."""
    
    config = config or {}

    # Determine report content
    report_content = state.get("failure_report") or state.get("summary_report")
    if not report_content:
        return {}

    # 1. Update Short-Term Memory (Global Knowledge Store)
    store = config.get("store")
    if store:
        if state.get("failed_testcases"):
            for testcase in state["failed_testcases"]:
                store.put(("global_tips",), testcase, {"analysis": report_content})
        elif state.get("test_status") == "passed":
            store.put(("global_tips",), "last_success", {"analysis": report_content})

    # 2. Update Semantic Memory (ChromaDB)
    try:
        query_vec = retriever.embed_query(state["log_content"])
        metadata = {
            "template": state["log_content"][:500],
            "severity": "high" if state.get("test_status") == "failed" else "low",
            "summary": report_content[:200],
            "causality": report_content[:500],
        }
        retriever.collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[query_vec.tolist()],
            metadatas=[metadata],
            documents=[state["log_content"]]
        )
    except Exception as e:
        print(f"[MemoryNode] Failed to commit to Semantic Memory: {str(e)}")
    
    return {}