"""
Document type classification agent.
"""
import os
from typing import Dict, Any
import logging
import re

from agents.adk_wrapper import Agent, AgentContext

logger = logging.getLogger(__name__)


async def classify_with_llm(text: str, use_stub: bool = True) -> Dict[str, Any]:
    """Classify document type using LLM (or stub)."""
    if use_stub or os.getenv("USE_DEV_STUB_LLM", "true").lower() == "true":
        # Stub mode: use rule-based classification
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["contract", "agreement", "terms and conditions"]):
            return {"document_type": "contract", "confidence": 0.9}
        elif any(keyword in text_lower for keyword in ["policy", "procedure", "guideline"]):
            return {"document_type": "policy", "confidence": 0.9}
        elif any(keyword in text_lower for keyword in ["invoice", "bill", "payment", "amount due"]):
            return {"document_type": "invoice", "confidence": 0.9}
        elif any(keyword in text_lower for keyword in ["employee", "hr", "human resources", "approval form"]):
            return {"document_type": "hr_form", "confidence": 0.9}
        else:
            return {"document_type": "unknown", "confidence": 0.5}
    
    # Real LLM call would go here
    return {"document_type": "unknown", "confidence": 0.5}


class TriageAgent(Agent):
    """Classifies document type."""
    
    def __init__(self):
        super().__init__(
            name="triage_agent",
            description="Classifies document type and extracts metadata"
        )
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Classify document and extract metadata."""
        text = context.document_text[:1000]  # Use first 1000 chars for classification
        
        classification = await classify_with_llm(text)
        doc_type = classification["document_type"]
        confidence = classification["confidence"]
        
        context.metadata["document_type"] = doc_type
        context.metadata["classification_confidence"] = confidence
        
        context.agent_outputs["triage_agent"] = {
            "document_type": doc_type,
            "confidence": confidence
        }
        
        logger.info(f"Triage Agent classified document as: {doc_type} (confidence: {confidence})")
        return context

