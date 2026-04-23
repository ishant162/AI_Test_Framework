"""Embedding Manager Module"""

import numpy as np
from openai import OpenAI


class EmbeddingManager:
    """
    Manages the generation of semantic embeddings for textual inputs using
    the Generative Engine embedding API.

    This class is responsible for:
    - Initializing the embedding client
    - Splitting large texts into manageable chunks
    - Generating embeddings for each chunk
    - Aggregating chunk-level embeddings into a single vector per input text
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "amazon.titan-embed-text-v2:0",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        """
        Initialize the embedding manager with model configuration and chunking parameters.

        Args:
            api_key (str): API key used to authenticate with the Generative Engine.
            model_name (str): Embedding model identifier.
            chunk_size (int): Maximum number of characters per text chunk.
            chunk_overlap (int): Number of overlapping characters between consecutive chunks.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        print("[EmbeddingManager] Initializing embedding manager...")
        print(f"[EmbeddingManager] Model: {self.model_name}")
        print(f"[EmbeddingManager] Chunk size: {self.chunk_size}")
        print(f"[EmbeddingManager] Chunk overlap: {self.chunk_overlap}")

        self.client = self._initialize_client()
        print("[EmbeddingManager] Client initialized successfully.")

    def _initialize_client(self) -> OpenAI:
        """
        Create and return a Generative Engine client configured for embedding generation.

        Returns:
            OpenAI: Initialized client instance pointing to the Generative Engine endpoint.
        """
        return OpenAI(
            base_url="https://openai.generative.engine.capgemini.com/v1",
            api_key=self.api_key,
        )

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split a text string into overlapping chunks to avoid model context limits.

        Args:
            text (str): Input text to be chunked.

        Returns:
            List[str]: List of text chunks. Returns an empty list for invalid or empty input.
        """
        if not text or not isinstance(text, str):
            return []

        text_length = len(text)
        chunks = []
        start = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def _embed_single_chunk(self, chunk: str) -> list[float]:
        """
        Generate an embedding vector for a single text chunk.

        Args:
            chunk (str): Text chunk to embed.

        Returns:
            List[float]: Embedding vector produced by the model.
        """
        response = self.client.embeddings.create(
            model=self.model_name,
            input=chunk,
        )
        return response.data[0].embedding

    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of input texts.

        Each text is chunked if necessary, embedded at the chunk level,
        and then aggregated into a single vector using mean pooling.

        Args:
            texts (List[str]): List of text inputs to embed.

        Returns:
            np.ndarray: Array of embedding vectors, one per input text.
        """
        if not texts:
            print("[EmbeddingManager] No texts provided. Returning empty embeddings.")
            return np.empty((0, 384), dtype=np.float32)

        print(f"[EmbeddingManager] Generating embeddings for {len(texts)} texts...")
        final_embeddings = []

        for idx, text in enumerate(texts, start=1):
            print(f"[EmbeddingManager] Processing text {idx}/{len(texts)}")
            try:
                chunks = self._chunk_text(text)
                print(f"[EmbeddingManager] Text split into {len(chunks)} chunks")

                if not chunks:
                    print("[EmbeddingManager] Empty text detected. Using zero vector.")
                    final_embeddings.append(np.zeros(384, dtype=np.float32))
                    continue

                chunk_embeddings = []

                for cidx, chunk in enumerate(chunks, start=1):
                    print(f"  └─ Embedding chunk {cidx}/{len(chunks)}")
                    chunk_embeddings.append(self._embed_single_chunk(chunk))

                aggregated_embedding = np.mean(
                    np.asarray(chunk_embeddings, dtype=np.float32),
                    axis=0,
                )

                final_embeddings.append(aggregated_embedding)
                print("[EmbeddingManager] Aggregated chunk embeddings successfully.")

            except Exception as e:
                print(f"[EmbeddingManager] ERROR during embedding: {str(e)}")
                print("[EmbeddingManager] Falling back to zero vector.")
                final_embeddings.append(np.zeros(384, dtype=np.float32))

        embeddings_array = np.vstack(final_embeddings)
        print(
            f"[EmbeddingManager] Embedding generation complete. "
            f"Final shape: {embeddings_array.shape}"
        )

        return embeddings_array
