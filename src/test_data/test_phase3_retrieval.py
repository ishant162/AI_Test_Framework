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
        meta = r["metadata"]

        print(f"\nResult #{idx + 1}")
        print(f"  ✅ Vector ID:  {r['id']}")
        print(f"  ✅ Template:   {r['document']}")

        print("  ✅ Metadata:")
        print(f"      • Severity:           {meta.get('severity')}")
        print(f"      • Summary:            {meta.get('summary')}")
        print(f"      • Causality:          {meta.get('causality')}")
        print(f"      • Is Anomaly:         {meta.get('is_anomaly')}")
        print(f"      • Anomaly Score:      {meta.get('anomaly_score')}")
        print(f"      • Cluster ID:         {meta.get('cluster_id')}")
        print(f"      • Cluster Confidence: {meta.get('cluster_confidence')}")

        print(f"  ✅ Distance: {r['distance']}")
        print("--------------------------------------------------")

    print("\n✅ Retrieval test complete.\n")


if __name__ == "__main__":
    test_phase3_retrieval()