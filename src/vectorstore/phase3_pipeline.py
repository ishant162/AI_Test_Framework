# src/vectorstore/phase3_pipeline.py

import uuid
import numpy as np
from dotenv import load_dotenv
import os

import chromadb
from src.vectorstore.embedding_manager import EmbeddingManager


class Phase3Pipeline:
    """
    Phase‑3 Pipeline (Simplified):
    Embedding (OpenAI Titan) → Chroma Storage
    """

    def __init__(self, api_key: str = None):

        # ✅ Load .env
        load_dotenv()

        # ✅ If API key is not passed, use .env
        self.api_key = api_key or os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("API_KEY missing. Add it to .env or pass explicitly.")

        # ✅ Titan model for embedding
        self.embedder = EmbeddingManager(
            api_key=self.api_key,
            model_name="amazon.titan-embed-text-v2:0"
        )

        # ✅ Chroma initialization
        self.client = chromadb.PersistentClient(path="./phase3_chroma")

        # ✅ Create or load the collection
        self.collection = self.client.get_or_create_collection(
            name="phase3_vectors",
            metadata={"description": "Phase‑3 vector embeddings from logs"}
        )

    # ----------------------------------------------------------------------
    # 1️⃣ EMBEDDING (Titan model)
    # ----------------------------------------------------------------------
    def embed_templates(self, templates):
        texts = [t["template"] for t in templates]
        vectors = self.embedder.generate_embeddings(texts)
        return vectors

    # ----------------------------------------------------------------------
    # 2️⃣ STORE VECTORS IN CHROMA
    # ----------------------------------------------------------------------
    def store_vectors(self, templates, vectors):
        ids = []

        for i, t in enumerate(templates):
            vid = str(uuid.uuid4())
            ids.append(vid)

            metadata = {
                "template": t.get("template"),
                "severity": t.get("severity"),
                "summary": t.get("summary"),
                "causality": t.get("causality")
            }

            self.collection.add(
                ids=[vid],
                embeddings=[vectors[i].tolist()],
                metadatas=[metadata],
                documents=[t.get("template", "")]
            )

        return ids

    # ----------------------------------------------------------------------
    # ✅ ENTIRE PIPELINE
    # ----------------------------------------------------------------------
    def run(self, templates):
        vectors = self.embed_templates(templates)
        return self.store_vectors(templates, vectors)