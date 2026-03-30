import os
from dotenv import load_dotenv

from src.vectorstore.vector_retrieval import VectorRetriever


def test_phase3_retrieval():
    print("\n==============================")
    print("   PHASE‑3 RETRIEVAL TEST RUN ")
    print("==============================\n")

    # ---------------------------------------------------------
    # STEP 1: Load API key from .env
    # ---------------------------------------------------------
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        raise ValueError("❌ API_KEY missing in .env")

    # ---------------------------------------------------------
    # STEP 2: Initialize retriever
    # ---------------------------------------------------------
    retriever = VectorRetriever(api_key=API_KEY)

    # ---------------------------------------------------------
    # STEP 3: Ask a query to retrieve similar log templates
    # ---------------------------------------------------------
    query = "connection timeout issue"
    print(f"🔍 Retrieving matches for query:\n   \"{query}\"\n")

    result = retriever.retrieve(query=query, top_k=3)

    # ---------------------------------------------------------
    # STEP 4: Print Results
    # ---------------------------------------------------------
    print("✅ Retrieval Completed!\n")

    for idx, r in enumerate(result["results"]):
        print(f"Result #{idx + 1}")
        print(f"  ✅ Vector ID:  {r['id']}")
        print(f"  ✅ Template:   {r['document']}")
        print(f"  ✅ Metadata:   {r['metadata']}")
        print(f"  ✅ Distance:   {r['distance']}")
        print("--------------------------------------------------")

    print("\n✅ Retrieval test complete.\n")


if __name__ == "__main__":
    test_phase3_retrieval()