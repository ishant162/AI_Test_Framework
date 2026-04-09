# src/vectorstore/vector_retrieval.py

import os
from typing import Any

import chromadb
import numpy as np
from dotenv import load_dotenv

from src.vectorstore.embedding_manager import EmbeddingManager


class VectorRetriever:
    def __init__(self, api_key: str = None, collection_name="log_templates"):

        load_dotenv()
        self.api_key = api_key or os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("API_KEY not found in .env or constructor.")

        self.collection_name = collection_name

        # Titan embedder
        self.embedder = EmbeddingManager(
            api_key=self.api_key, model_name="amazon.titan-embed-text-v2:0"
        )

        # Vector store used by the embedding pipeline
        self.client = chromadb.PersistentClient(path="./log_embeddings")

        # Load the stored vector collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Semantic embeddings for log templates"},
        )

    # Embed user query
    def embed_query(self, text: str) -> np.ndarray:
        vec = self.embedder.generate_embeddings([text])
        return vec[0]

    # Retrieve similar vectors
    def retrieve(self, query: str, top_k: int = 5) -> dict[str, Any]:
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

        return {"query": query, "results": output}
