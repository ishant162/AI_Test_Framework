# src/vectorstore/phase3_pipeline.py

import uuid
import numpy as np
import os
from dotenv import load_dotenv

from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor
import hdbscan

import chromadb
from src.vectorstore.embedding_manager import EmbeddingManager


class Phase3Pipeline:
    """
    Phase‑3 Pipeline (Improved):
    Embedding → Normalization → Advanced Anomaly Detection (LOF + HDBSCAN)
    → HDBSCAN Clustering (Auto K) → Chroma Storage
    """

    def __init__(self, api_key: str = None):

        # ✅ Load .env
        load_dotenv()

        # ✅ If no API key passed, load from environment
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY missing. Add it to .env or pass explicitly.")

        # ✅ Embedding model (Amazon Titan)
        self.embedder = EmbeddingManager(
            api_key=self.api_key,
            model_name="amazon.titan-embed-text-v2:0"
        )

        # ✅ Chroma persistence
        self.client = chromadb.PersistentClient(path="./phase3_chroma")

        # ✅ Chroma collection
        self.collection = self.client.get_or_create_collection(
            name="phase3_vectors",
            metadata={"description": "Improved Phase‑3 vector embeddings from logs"}
        )

        # ✅ Normalizer (important for anomaly detection)
        self.scaler = StandardScaler()

    # ---------------------------------------------------------------
    # 1️⃣ EMBEDDING
    # ---------------------------------------------------------------
    def embed_templates(self, templates):
        texts = [t["template"] for t in templates]
        vectors = self.embedder.generate_embeddings(texts)
        return np.array(vectors)

    # ---------------------------------------------------------------
    # 2️⃣ VECTOR NORMALIZATION
    # ---------------------------------------------------------------
    def normalize(self, vectors):
        return self.scaler.fit_transform(vectors)

    # ---------------------------------------------------------------
    # 3️⃣ ADVANCED ANOMALY DETECTION (LOF + HDBSCAN Outlier Score)
    # ---------------------------------------------------------------
    def detect_anomalies(self, norm_vectors):
        # ✅ Local Outlier Factor (LOF)
        lof = LocalOutlierFactor(n_neighbors=20, contamination="auto")
        lof_labels = lof.fit_predict(norm_vectors)
        lof_scores = -lof.negative_outlier_factor_

        # ✅ HDBSCAN anomaly score
        hdb = hdbscan.HDBSCAN(min_cluster_size=5)
        hdb.fit(norm_vectors)
        hdb_scores = hdb.outlier_scores_ if hdb.outlier_scores_ is not None else np.zeros(len(norm_vectors))

        # ✅ Combine scores
        combined_score = (lof_scores + hdb_scores) / 2.0

        # ✅ Threshold = mean + std (dynamic)
        threshold = combined_score.mean() + combined_score.std()

        anomaly_flags = combined_score > threshold

        return anomaly_flags.astype(bool), combined_score.tolist()

    # ---------------------------------------------------------------
    # 4️⃣ ADVANCED CLUSTERING (HDBSCAN Auto Cluster Count)
    # ---------------------------------------------------------------
    def cluster_templates(self, norm_vectors):
        clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
        labels = clusterer.fit_predict(norm_vectors)

        # HDBSCAN cluster probability (confidence)
        probs = clusterer.probabilities_

        return labels.tolist(), probs.tolist()

    # ---------------------------------------------------------------
    # 5️⃣ STORE IN CHROMA
    # ---------------------------------------------------------------
    def store_vectors(self, templates, vectors, anomalies, anomaly_scores, clusters, cluster_conf):

        ids = []
        for i, t in enumerate(templates):
            vid = str(uuid.uuid4())
            ids.append(vid)

            metadata = {
                "template": t.get("template"),
                "severity": t.get("severity"),
                "summary": t.get("summary"),
                "causality": t.get("causality"),

                # ✅ Advanced metadata
                "is_anomaly": bool(anomalies[i]),
                "anomaly_score": float(anomaly_scores[i]),
                "cluster_id": int(clusters[i]),
                "cluster_confidence": float(cluster_conf[i])
            }

            self.collection.add(
                ids=[vid],
                embeddings=[vectors[i].tolist()],
                metadatas=[metadata],
                documents=[t.get("template", "")]
            )

        return ids

    # ---------------------------------------------------------------
    # ✅ ENTIRE PIPELINE
    # ---------------------------------------------------------------
    def run(self, templates):
        raw_vectors = self.embed_templates(templates)
        norm_vectors = self.normalize(raw_vectors)

        anomalies, anomaly_scores = self.detect_anomalies(norm_vectors)
        clusters, cluster_conf = self.cluster_templates(norm_vectors)

        return self.store_vectors(
            templates,
            raw_vectors,
            anomalies,
            anomaly_scores,
            clusters,
            cluster_conf
        )