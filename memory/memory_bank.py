"""
Memory Bank for storing templates, violations, and document history.
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from tools.vector_store import VectorStore
from tools.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class MemoryBank:
    """Stores templates, violations, and provides similarity search."""
    
    def __init__(self, store_path: str = "./data/memory_bank", embedding_dim: int = 384):
        self.store_path = store_path
        os.makedirs(store_path, exist_ok=True)
        
        self.embedding_service = EmbeddingService()
        self.template_store = VectorStore(dimension=embedding_dim, store_path=os.path.join(store_path, "templates"))
        self.violation_store = VectorStore(dimension=embedding_dim, store_path=os.path.join(store_path, "violations"))
        
        self.policies_path = os.path.join(store_path, "policies")
        os.makedirs(self.policies_path, exist_ok=True)
        
        self._load_policies()
    
    def _load_policies(self):
        """Load policy files from docs/policies directory."""
        policies_dir = "./docs/policies"
        if os.path.exists(policies_dir):
            for filename in os.listdir(policies_dir):
                if filename.endswith('.txt') or filename.endswith('.md'):
                    policy_id = filename.replace('.txt', '').replace('.md', '')
                    with open(os.path.join(policies_dir, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._save_policy(policy_id, content)
    
    def _save_policy(self, policy_id: str, content: str):
        """Save policy content."""
        policy_file = os.path.join(self.policies_path, f"{policy_id}.txt")
        with open(policy_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def store_template(self, template_id: str, text: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Store a template with its embedding."""
        if embedding is None:
            embedding = self.embedding_service.embed(text)
        
        metadata = metadata or {}
        metadata.update({
            "template_id": template_id,
            "text": text,
            "stored_at": datetime.now().isoformat()
        })
        
        await self.template_store.add(template_id, embedding, metadata)
        logger.info(f"Stored template: {template_id}")
    
    async def search_templates(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar templates."""
        embedding = self.embedding_service.embed(query_text)
        results = await self.template_store.search(embedding, top_k)
        return results
    
    async def store_violation(self, violation: Dict[str, Any], embedding: Optional[List[float]] = None):
        """Store a violation example."""
        violation_id = violation.get("id", f"violation_{datetime.now().timestamp()}")
        violation_text = violation.get("text", violation.get("description", ""))
        
        if embedding is None and violation_text:
            embedding = self.embedding_service.embed(violation_text)
        elif embedding is None:
            embedding = [0.0] * 384
        
        metadata = violation.copy()
        metadata["stored_at"] = datetime.now().isoformat()
        
        await self.violation_store.add(violation_id, embedding, metadata)
        logger.info(f"Stored violation: {violation_id}")
    
    async def search_violations(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar past violations."""
        embedding = self.embedding_service.embed(query_text)
        results = await self.violation_store.search(embedding, top_k)
        return results
    
    async def get_policy_snippet(self, policy_id: str) -> Optional[str]:
        """Retrieve a policy snippet by ID."""
        policy_file = os.path.join(self.policies_path, f"{policy_id}.txt")
        if os.path.exists(policy_file):
            with open(policy_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Also check docs/policies
        docs_policy = os.path.join("./docs/policies", f"{policy_id}.txt")
        if os.path.exists(docs_policy):
            with open(docs_policy, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def save(self):
        """Save all stores."""
        self.template_store.save()
        self.violation_store.save()

