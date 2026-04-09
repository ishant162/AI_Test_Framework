import numpy as np
from openai import OpenAI


class EmbeddingManager:
    """Handles document embedding generation using Generative Engine API"""

    def __init__(self, api_key: str, model_name: str = "amazon.titan-embed-text-v2:0"):

        self.model_name = model_name
        self.api_key = api_key
        self.client = None
        self._load_model()

    def _load_model(self):
        try:
            print(f"Initializing Generative Engine embedding model: {self.model_name}")

            self.client = OpenAI(
                base_url="https://openai.generative.engine.capgemini.com/v1",
                api_key=self.api_key,
            )

            print("Generative Engine client initialized successfully.")
        except Exception as e:
            print(f"Error initializing Generative Engine client: {e}")
            raise

    def generate_embeddings(self, texts: list[str]) -> np.ndarray:

        if not self.client:
            raise ValueError("Client not initialized")

        print(f"Generating embeddings for {len(texts)} texts...")
        all_embeddings = []

        for text in texts:
            try:
                response = self.client.embeddings.create(
                    input=text, model=self.model_name
                )
                embedding = response.data[0].embedding
                all_embeddings.append(embedding)

            except Exception as e:
                print(f"Error generating embedding for text: {e}")
                all_embeddings.append([0] * 384)  # fallback vector

        embeddings = np.array(all_embeddings)
        print(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
