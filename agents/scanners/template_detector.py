"""
Template drift detector using embedding similarity.
"""
from typing import List, Dict, Any
import logging

from agents.adk_wrapper import Agent, AgentContext
from memory.memory_bank import MemoryBank

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.7  # Threshold below which we flag as drift


class TemplateDetector(Agent):
    """Detects template drift by comparing document chunks to canonical templates."""
    
    def __init__(self, memory_bank: MemoryBank):
        super().__init__(
            name="template_detector",
            description="Detects deviations from canonical templates"
        )
        self.memory_bank = memory_bank
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Detect template drift."""
        text = context.document_text
        
        # Split into chunks (simple paragraph-based)
        chunks = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        violations = []
        for idx, chunk in enumerate(chunks):
            # Search for similar templates
            similar_templates = await self.memory_bank.search_templates(chunk, top_k=1)
            
            if similar_templates:
                best_match = similar_templates[0]
                similarity = best_match.get("similarity", 0.0)
                
                if similarity < SIMILARITY_THRESHOLD:
                    # Estimate chunk position in document
                    chunk_start = text.find(chunk)
                    chunk_end = chunk_start + len(chunk)
                    
                    violations.append({
                        "type": "template_drift",
                        "chunk_index": idx,
                        "span_start": chunk_start,
                        "span_end": chunk_end,
                        "similarity": similarity,
                        "threshold": SIMILARITY_THRESHOLD,
                        "severity": "medium" if similarity > 0.5 else "high",
                        "message": f"Chunk deviates from template (similarity: {similarity:.2f})"
                    })
            else:
                # No templates found - flag as potential drift
                chunk_start = text.find(chunk)
                chunk_end = chunk_start + len(chunk)
                violations.append({
                    "type": "template_drift",
                    "chunk_index": idx,
                    "span_start": chunk_start,
                    "span_end": chunk_end,
                    "similarity": 0.0,
                    "severity": "low",
                    "message": "No matching template found"
                })
        
        context.violations.extend(violations)
        context.agent_outputs["template_detector"] = {
            "chunks_checked": len(chunks),
            "violations_found": len(violations),
            "violations": violations
        }
        
        logger.info(f"Template Detector found {len(violations)} drift violations")
        return context

