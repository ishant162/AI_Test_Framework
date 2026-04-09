import os

from dotenv import load_dotenv

from src.vectorstore.vector_retrieval import VectorRetriever


def test_retrieval_pipeline():
    print("\n==============================")
    print("   RETRIEVAL PIPELINE TEST RUN ")
    print("==============================\n")

    # Load environment variables and read the API key
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        raise ValueError("API_KEY is missing from the environment")

    # Initialize the vector retriever
    retriever = VectorRetriever(api_key=API_KEY)

    # Query used to test semantic retrieval
    query = "connection timeout issue"
    print(f'Running retrieval for query:\n"{query}"\n')

    result = retriever.retrieve(query=query, top_k=3)

    # Display retrieval results
    print("Retrieval completed successfully\n")

    for idx, r in enumerate(result["results"]):
        meta = r["metadata"]

        print(f"Result {idx + 1}")
        print(f"Vector ID       : {r['id']}")
        print(f"Template        : {r['document']}")

        print("Metadata")
        print(f"  Severity            : {meta.get('severity')}")
        print(f"  Summary             : {meta.get('summary')}")
        print(f"  Causality           : {meta.get('causality')}")

        print(f"Distance          : {r['distance']}")
        print("-" * 50)

    print("\nRetrieval test finished\n")


if __name__ == "__main__":
    test_retrieval_pipeline()
