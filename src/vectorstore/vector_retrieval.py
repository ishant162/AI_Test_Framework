import os
from typing import Any, dict

import chromadb
import numpy as np
from dotenv import load_dotenv

from src.vectorstore.embedding_manager import EmbeddingManager


class VectorRetriever:
    """
    Handles semantic retrieval of log templates from the vector store.

    This class is responsible for:
    - Generating embeddings for query text
    - Normalizing query vectors for cosine similarity
    - Querying ChromaDB to retrieve the most relevant stored templates
    """

    def __init__(self, api_key: str = None, collection_name="log_templates"):
        """
        Initialize the vector retriever and required dependencies.

        This includes loading environment variables, initializing the
        embedding manager, and connecting to the ChromaDB collection
        configured for cosine similarity.

        Args:
            api_key (str, optional): API key for embedding generation.
                                     If not provided, it is read from the environment.
            collection_name (str): Name of the ChromaDB collection to query.
        """
        print("[VectorRetriever] Initializing vector retriever...")

        load_dotenv()
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY not found in .env or constructor.")

        self.collection_name = collection_name

        self.embedder = EmbeddingManager(
            api_key=self.api_key, model_name="amazon.titan-embed-text-v2:0"
        )

        self.client = chromadb.PersistentClient(path="./log_embeddings")

        # cosine space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Semantic embeddings for log templates",
                "hnsw:space": "cosine",
            },
        )

        print("[VectorRetriever] Vector retriever ready.")

    def embed_query(self, text: str) -> np.ndarray:
        """
        Generate and normalize an embedding vector for a query string.

        The query is embedded using the same model as indexed templates
        and L2-normalized to ensure compatibility with cosine similarity
        during retrieval.

        Args:
            text (str): Query text to embed.

        Returns:
            np.ndarray: Normalized query embedding vector.
        """
        print("[VectorRetriever] Embedding and normalizing query...")
        vec = self.embedder.generate_embeddings([text])[0]

        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec

        return vec / norm

    def retrieve(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """
        Retrieve the most semantically similar log templates for a query.

        This method embeds the query, executes a similarity search against
        the vector store, and returns the top matching templates along
        with their metadata and distance scores.

        Args:
            query (str): Query string used for semantic search.
            top_k (int): Number of top matches to retrieve.

        Returns:
            Dict[str, Any]: Retrieval results including matched templates,
                            metadata, and similarity distances.
        """
        print(f"[VectorRetriever] Retrieving top {top_k} matches...")
        query_vec = self.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vec.tolist()], n_results=top_k
        )

        output = []
        for i in range(len(results["ids"][0])):
            output.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )

        print("[VectorRetriever] Retrieval complete.")
        return {"query": query, "results": output}