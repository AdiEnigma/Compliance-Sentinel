"""
Vector store implementation using FAISS with SQLite fallback.
"""
import os
import json
from typing import List, Dict, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

USE_FAISS = os.getenv("USE_FAISS", "true").lower() == "true"

if USE_FAISS:
    try:
        import faiss
        FAISS_AVAILABLE = True
    except ImportError:
        FAISS_AVAILABLE = False
        logger.warning("FAISS not available, falling back to SQLite")
else:
    FAISS_AVAILABLE = False

try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("aiosqlite not available")


class VectorStore:
    """Vector store for embeddings with similarity search."""
    
    def __init__(self, dimension: int = 384, store_path: str = "./data/vector_store"):
        self.dimension = dimension
        self.store_path = store_path
        self.use_faiss = FAISS_AVAILABLE and USE_FAISS
        
        if self.use_faiss:
            self._init_faiss()
        else:
            self._init_sqlite()
    
    def _init_faiss(self):
        """Initialize FAISS index."""
        os.makedirs(self.store_path, exist_ok=True)
        index_path = os.path.join(self.store_path, "faiss.index")
        metadata_path = os.path.join(self.store_path, "metadata.json")
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
        
        self.metadata_path = metadata_path
    
    def _init_sqlite(self):
        """Initialize SQLite-based vector store."""
        os.makedirs(self.store_path, exist_ok=True)
        self.db_path = os.path.join(self.store_path, "vectors.db")
        self.metadata = []
        # SQLite will be initialized on first use
    
    async def add(self, id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Add a vector with metadata."""
        if self.use_faiss:
            vector = np.array([embedding], dtype=np.float32)
            self.index.add(vector)
            self.metadata.append({"id": id, **metadata})
            # Save periodically
            if len(self.metadata) % 100 == 0:
                self._save_faiss()
        else:
            await self._add_sqlite(id, embedding, metadata)
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if self.use_faiss:
            return self._search_faiss(query_embedding, top_k)
        else:
            return await self._search_sqlite(query_embedding, top_k)
    
    def _search_faiss(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """FAISS-based search."""
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["distance"] = float(dist)
                result["similarity"] = 1.0 / (1.0 + dist)  # Convert distance to similarity
                results.append(result)
        
        return results
    
    async def _add_sqlite(self, id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Add to SQLite store."""
        if not SQLITE_AVAILABLE:
            logger.warning("SQLite not available, storing in memory only")
            self.metadata.append({"id": id, "embedding": embedding, **metadata})
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id TEXT PRIMARY KEY,
                    embedding TEXT,
                    metadata TEXT
                )
            """)
            
            embedding_json = json.dumps(embedding)
            metadata_json = json.dumps(metadata)
            await db.execute(
                "INSERT OR REPLACE INTO vectors (id, embedding, metadata) VALUES (?, ?, ?)",
                (id, embedding_json, metadata_json)
            )
            await db.commit()
    
    async def _search_sqlite(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """SQLite-based search (brute force)."""
        if not SQLITE_AVAILABLE:
            return []
        
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, embedding, metadata FROM vectors") as cursor:
                async for row in cursor:
                    stored_embedding = json.loads(row[1])
                    # Compute cosine similarity
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    metadata = json.loads(row[2])
                    results.append({
                        "id": row[0],
                        "similarity": similarity,
                        "distance": 1.0 - similarity,
                        **metadata
                    })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
    
    def _save_faiss(self):
        """Save FAISS index and metadata."""
        index_path = os.path.join(self.store_path, "faiss.index")
        faiss.write_index(self.index, index_path)
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)
    
    def save(self):
        """Save the vector store."""
        if self.use_faiss:
            self._save_faiss()

