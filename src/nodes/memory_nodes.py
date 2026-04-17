"""Memory Nodes Module"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.state.state import TestLogState
from src.vectorstore.vector_retrieval import VectorRetriever

# Initialize retriever (assuming API key is in environment)
retriever = VectorRetriever()

def retrieve_historical_context(state: TestLogState, config: dict) -> TestLogState:
    """Retrieve similar past failures and global tips for context."""

    # 1. Semantic Memory Retrieval (ChromaDB)
    # Search for similar logs to the current log_content
    search_results = retriever.retrieve(state["log_content"], top_k=2)

    semantic_context = ""
    if search_results["results"]:
        semantic_context = "\n--- Similar Past Failures ---\n"
        for res in search_results["results"]:
            semantic_context += f"Past Issue: {res['document']}\n"
            # Assuming metadata contains resolution/root cause
            resolution = res['metadata'].get('resolution', 'No resolution recorded')
            semantic_context += f"Resolution: {resolution}\n\n"

    # 2. Long-Term/Global Memory (LangGraph Store)
    # Access the shared store for global tips
    store = config.get("store")
    global_tips = ""
    if store:
        # Example: look for tips related to identified failed testcases
        for testcase in (state.get("failed_testcases") or []):
            tip = store.get(("global_tips",), testcase)
            if tip:
                global_tips += f"Tip for {testcase}: {tip.value}\n"

    # Combine all retrieved context
    state["historical_context"] = f"{semantic_context}\n{global_tips}"
    return state

def failure_analysis(state: TestLogState) -> TestLogState:
    """Generate failure analysis report with historical context."""

    context_prompt = ""
    if state.get("historical_context"):
        context_prompt = f"\n\nUSE THIS HISTORICAL CONTEXT FOR ANALYSIS:\n{state['historical_context']}"

    prompt = f"""Analyze the failed test cases and generate a detailed failure report.
{context_prompt}

Test Log:
{state["log_content"]}

Failed Test Cases:
{chr(10).join(state["failed_testcases"]) if state["failed_testcases"] else "None identified"}

Include:
- List of failed tests
- Failure reasons
- Error messages
- Potential root causes (considering historical context if provided)"""

    messages = [
        SystemMessage(content="You are generating a test failure analysis report."),
        HumanMessage(content=prompt),
    ]

    # Assuming llm is available or imported
    # response = llm.invoke(messages)
    # state["failure_report"] = response.content

    # For implementation delivery, we just show the logic update
    return state

def commit_to_memory(state: TestLogState, config: dict) -> TestLogState:
    """Commit the current failure and its analysis to memory."""

    # 1. Update Semantic Memory (ChromaDB)
    # In a real scenario, we'd embed and add the failure_report
    # retriever.add_to_collection(state["log_content"], {"resolution": state["failure_report"]})

    # 2. Update Global Memory (Store)
    store = config.get("store")
    if store and state.get("failed_testcases") and state.get("failure_report"):
        for testcase in state["failed_testcases"]:
            # Store the latest analysis as a tip for this testcase
            store.put(("global_tips",), testcase, {"value": state["failure_report"]})

    return state
