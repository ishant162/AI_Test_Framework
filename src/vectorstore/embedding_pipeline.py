# src/vectorstore/embedding_pipeline.py

import uuid
import numpy as np
import os
from dotenv import load_dotenv

from sklearn.preprocessing import StandardScaler

import chromadb
from src.vectorstore.embedding_manager import EmbeddingManager


class EmbeddingPipeline:
    """
    Embedding Pipeline (Simplified):

    Steps performed by this pipeline:
    1. Generate embeddings for log templates using Amazon Titan
    2. Normalize embeddings for numerical stability
    3. Store embeddings and metadata in ChromaDB

    Note:
    - Anomaly detection will be implemented in next phase
    - Clustering will be implemented in next phase
    - This version focuses purely on clean vector storage for retrieval
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the embedding pipeline.

        - Loads API key
        - Initializes embedding model
        - Connects to ChromaDB persistent storage
        """

        # Load environment variables from .env
        load_dotenv()

        # Read API key from argument or environment
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY missing. Add it to .env or pass explicitly.")

        # Initialize embedding manager (Amazon Titan)
        self.embedder = EmbeddingManager(
            api_key=self.api_key,
            model_name="amazon.titan-embed-text-v2:0"
        )

        # Initialize Chroma persistent client
        self.client = chromadb.PersistentClient(path="./log_embeddings")

        # Create or load the vector collection
        self.collection = self.client.get_or_create_collection(
            name="log_templates",
            metadata={"description": "Semantic embeddings for log templates"}
        )

        # Scaler used to normalize embedding vectors
        self.scaler = StandardScaler()

    
    # EMBEDDING GENERATION
    def embed_templates(self, templates):
        """
        Generate embeddings for all log templates.

        Args:
            templates (list): List of template dictionaries

        Returns:
            np.ndarray: Array of embedding vectors
        """

        texts = [t["template"] for t in templates]
        vectors = self.embedder.generate_embeddings(texts)
        return np.array(vectors)

    
    # VECTOR NORMALIZATION
    def normalize(self, vectors):
        """
        Normalize embeddings to improve numerical consistency.

        Args:
            vectors (np.ndarray): Raw embedding vectors

        Returns:
            np.ndarray: Normalized vectors
        """

        return self.scaler.fit_transform(vectors)

    
    # STORE VECTORS IN CHROMA
    def store_vectors(self, templates, vectors):
        """
        Store embeddings along with metadata in ChromaDB.

        Args:
            templates (list): Original template records
            vectors (np.ndarray): Embedding vectors

        Returns:
            list: List of stored vector IDs
        """

        ids = []

        for i, t in enumerate(templates):
            vector_id = str(uuid.uuid4())
            ids.append(vector_id)

            metadata = {
                "template": t.get("template"),
                "severity": t.get("severity"),
                "summary": t.get("summary"),
                "causality": t.get("causality")
            }

            self.collection.add(
                ids=[vector_id],
                embeddings=[vectors[i].tolist()],
                metadatas=[metadata],
                documents=[t.get("template", "")]
            )

        return ids

    
    # COMPLETE PIPELINE EXECUTION
    def run(self, templates):
        """
        Run the complete embedding pipeline:
        - Embed templates
        - Normalize vectors
        - Store results in ChromaDB

        Args:
            templates (list): List of log templates

        Returns:
            list: Stored vector IDs
        """

        raw_vectors = self.embed_templates(templates)
        normalized_vectors = self.normalize(raw_vectors)

        return self.store_vectors(
            templates,
            normalized_vectors
        )
