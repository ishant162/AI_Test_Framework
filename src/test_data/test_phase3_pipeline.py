import os
from dotenv import load_dotenv

from src.vectorstore.phase3_pipeline import EmbeddingPipeline


def test_phase3_pipeline():
    print("\n==============================")
    print("   PHASE‑3 PIPELINE TEST RUN  ")
    print("==============================\n")

    
    # STEP 1: Load API key from .env  
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        raise ValueError("❌ API_KEY missing in .env")

    
    # STEP 2: Prepare sample templates for testing  
    templates = [
        {
            "template": "database connection timeout occurred while querying customer table",
            "severity": "high",
            "summary": "DB timeout failure",
            "causality": "network latency spike"
        },
        {
            "template": "authentication failed for user admin due to incorrect password",
            "severity": "medium",
            "summary": "Login attempt failed",
            "causality": "wrong credentials"
        },
        {
            "template": "payment API responded with 503 service unavailable",
            "severity": "critical",
            "summary": "Payment gateway unreachable",
            "causality": "third‑party outage"
        }
    ]

    print("✅ Sample templates prepared")

    
    # STEP 3: Initialize pipeline  
    pipeline = EmbeddingPipeline(api_key=API_KEY)
    print("✅ Phase‑3 pipeline initialized")

    
    # STEP 4: Run full pipeline (embed → normalize → anomalies → cluster → store)  
    print("\n🚀 Running Phase‑3 pipeline...\n")
    ids = pipeline.run(templates)

    
    # STEP 5: Show stored vector IDs  
    print("\n✅ Pipeline execution complete!")
    print("✅ Stored Vector IDs:")
    for vid in ids:
        print(f"   • {vid}")

    print("\n✅ Phase‑3 storage test complete.\n")


if __name__ == "__main__":
    test_phase3_pipeline()