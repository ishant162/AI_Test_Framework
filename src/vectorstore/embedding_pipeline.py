"""Embedding Pipeline Module"""

import os
import uuid

import chromadb
import numpy as np
from dotenv import load_dotenv

from src.vectorstore.embedding_manager import EmbeddingManager


class EmbeddingPipeline:
    """
    Orchestrates the end-to-end embedding workflow for log templates.

    This pipeline is responsible for:
    - Generating embeddings for log templates
    - Normalizing vectors for cosine similarity
    - Persisting embeddings and metadata into ChromaDB
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the embedding pipeline and required dependencies.

        This includes loading environment variables, initializing the
        embedding manager, and setting up the ChromaDB persistent collection.

        Args:
            api_key (str, optional): API key for embedding generation.
                                     If not provided, it is read from the environment.
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY missing. Add it to .env or pass explicitly.")

        print("[EmbeddingPipeline] Initializing embedding pipeline...")

        self.embedder = EmbeddingManager(
            api_key=self.api_key, model_name="amazon.titan-embed-text-v2:0"
        )

        self.client = chromadb.PersistentClient(path="./log_embeddings")

        # cosine space
        self.collection = self.client.get_or_create_collection(
            name="log_templates",
            metadata={
                "description": "Semantic embeddings for log templates",
                "hnsw:space": "cosine",
            },
        )

        print("[EmbeddingPipeline] Pipeline initialized successfully.")

    def embed_templates(self, templates):
        """
        Generate raw embedding vectors for a list of log templates.

        Args:
            templates (list): List of template dictionaries containing log text.

        Returns:
            np.ndarray: Array of raw embedding vectors.
        """
        print("[EmbeddingPipeline] Generating embeddings...")
        texts = [t["template"] for t in templates]
        vectors = self.embedder.generate_embeddings(texts)
        return np.asarray(vectors, dtype=np.float32)

    def normalize(self, vectors: np.ndarray) -> np.ndarray:
        """
        Apply L2 normalization to embedding vectors.

        This normalization ensures vectors are suitable for cosine similarity
        during retrieval and comparison.

        Args:
            vectors (np.ndarray): Raw embedding vectors.

        Returns:
            np.ndarray: L2-normalized embedding vectors.
        """
        print("[EmbeddingPipeline] L2-normalizing embeddings...")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def store_vectors(self, templates, vectors):
        """
        Store normalized embeddings and associated metadata in ChromaDB.

        Each template is stored with a unique identifier along with
        relevant metadata fields for downstream retrieval.

        Args:
            templates (list): List of original template records.
            vectors (np.ndarray): Normalized embedding vectors.

        Returns:
            list: List of generated vector IDs.
        """
        print("[EmbeddingPipeline] Storing vectors in ChromaDB...")
        ids = []

        for i, t in enumerate(templates):
            vector_id = str(uuid.uuid4())
            ids.append(vector_id)

            metadata = {
                "template": t.get("template"),
                "severity": t.get("severity"),
                "summary": t.get("summary"),
                "causality": t.get("causality"),
            }

            self.collection.add(
                ids=[vector_id],
                embeddings=[vectors[i].tolist()],
                metadatas=[metadata],
                documents=[t.get("template", "")],
            )

        print(f"[EmbeddingPipeline] Stored {len(ids)} vectors.")
        return ids

    def run(self, templates):
        """
        Execute the complete embedding pipeline.

        This method performs embedding generation, normalization,
        and persistence in a single flow.

        Args:
            templates (list): List of log template records.

        Returns:
            list: List of stored vector IDs.
        """
        print("[EmbeddingPipeline] Running full embedding pipeline...")

        raw_vectors = self.embed_templates(templates)
        normalized_vectors = self.normalize(raw_vectors)
        ids = self.store_vectors(templates, normalized_vectors)

        print("[EmbeddingPipeline] Pipeline complete.")
        return ids
