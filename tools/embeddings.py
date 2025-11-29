"""
Embedding utilities using sentence-transformers.
"""
import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not available, embeddings disabled")


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            logger.warning("Embeddings not available, using dummy embeddings")
            return
        
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.model is None:
            # Return dummy embedding of dimension 384 (all-MiniLM-L6-v2 dimension)
            return [0.0] * 384
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * 384
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.model is None:
            return [[0.0] * 384] * len(texts)
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * 384] * len(texts)
    
    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return 384  # all-MiniLM-L6-v2 dimension

