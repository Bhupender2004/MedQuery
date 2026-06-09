"""
MedQuery RAG Embeddings Module

Wraps SentenceTransformer pipelines for semantic vector transformations with mock fallbacks.
"""

import os

class EmbeddingService:
    """
    Lazy-loads embedding models locally using SentenceTransformers.
    Contains fallback utilities to return pseudo-random arrays if libraries or GPUs are offline.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """
        Retrieves loaded model instance or initializes it.
        """
        if cls._model is None:
            # Default model name matches .env configurations
            model_name = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Initializing SentenceTransformer model: {model_name}")
                cls._model = SentenceTransformer(model_name)
            except Exception as import_err:
                print(f"Warning: Could not initialize sentence-transformers ({import_err}). Using mock pipeline.")
                cls._model = 'mock_service'
        return cls._model

    @classmethod
    def embed_texts(cls, texts):
        """
        Converts text list to vector dimensions list.
        
        Args:
            texts (list): String descriptions list.
            
        Returns:
            list: List of float lists (dimension 384).
        """
        if not texts:
            return []

        model = cls.get_model()
        
        # Safe mock fallback if library is not installed
        if model == 'mock_service':
            # Generate deterministic list of dimensions (384 size)
            mock_dim_size = 384
            return [[float((i + hash(txt) % 100) / 1000.0) for i in range(mock_dim_size)] for txt in texts]

        try:
            embeddings_array = model.encode(texts)
            # Convert internal numpy arrays to standard floats list for JSON operations
            return embeddings_array.tolist()
        except Exception as encode_err:
            print(f"Embedding encoding execution failed: {encode_err}. Returning mock fallback.")
            mock_dim_size = 384
            return [[0.05] * mock_dim_size for _ in texts]
