import os
import json
from src.vectorstore.phase3_pipeline import Phase3Pipeline

def test_phase3():
    print("\n==============================")
    print("   PHASE‑3 PIPELINE TEST RUN  ")
    print("==============================\n")

    # ---------------------------------------------------------
    # STEP 1: Locate sample data file inside test_data folder
    # ---------------------------------------------------------
    BASE_DIR = os.path.dirname(__file__)
    json_path = os.path.join(BASE_DIR, "phase3_sample_data.json")

    print(f"Loading sample Phase‑3 data from:\n{json_path}\n")

    with open(json_path, "r") as f:
        templates = json.load(f)

    print(f"✅ Loaded {len(templates)} templates for vectorization.\n")

    # ---------------------------------------------------------
    # STEP 2: Run the Phase‑3 pipeline
    # ---------------------------------------------------------
    API_KEY = ""

    pipeline = Phase3Pipeline(api_key=API_KEY)

    print("Running Phase‑3 pipeline...\n")
    vector_ids = pipeline.run(templates)

    # ---------------------------------------------------------
    # STEP 3: Show results
    # ---------------------------------------------------------
    print("✅ Phase‑3 Completed Successfully!")
    print(f"✅ Stored {len(vector_ids)} embeddings into ChromaDB.\n")

    print("Generated Vector IDs:")
    for vid in vector_ids:
        print(f" - {vid}")

    print("\nYou can now inspect the folder './phase3_chroma/' to see the stored embeddings.\n")


if __name__ == "__main__":
    test_phase3()