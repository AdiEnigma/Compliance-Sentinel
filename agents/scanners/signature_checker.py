"""
Signature and approval checker agent.
"""
import re
from typing import List, Dict, Any
import logging

from agents.adk_wrapper import Agent, AgentContext

logger = logging.getLogger(__name__)


class SignatureChecker(Agent):
    """Checks for signatures and approval fields in documents."""
    
    def __init__(self):
        super().__init__(
            name="signature_checker",
            description="Detects signatures and approval fields"
        )
        
        self.signature_patterns = [
            re.compile(r'signed\s+by', re.IGNORECASE),
            re.compile(r'signature', re.IGNORECASE),
            re.compile(r'approved\s+by', re.IGNORECASE),
            re.compile(r'authorized\s+signature', re.IGNORECASE),
        ]
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Check for signatures and approvals."""
        text = context.document_text
        text_lower = text.lower()
        
        violations = []
        signatures_found = []
        
        # Check for signature patterns
        for pattern in self.signature_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                signatures_found.append({
                    "span_start": match.start(),
                    "span_end": match.end(),
                    "text": match.group(),
                    "type": "signature_field"
                })
        
        # Check for image signatures (heuristic: look for image references)
        if "signature" in text_lower and ("image" in text_lower or "png" in text_lower or "jpg" in text_lower):
            signatures_found.append({
                "type": "signature_image",
                "confidence": 0.7
            })
        
        # Determine if signature is missing based on document type
        doc_type = context.metadata.get("document_type", "")
        requires_signature = doc_type in ["contract", "hr_form", "agreement", "policy"]
        
        if requires_signature and not signatures_found:
            violations.append({
                "type": "missing_signature",
                "severity": "high",
                "message": f"{doc_type} document missing required signature/approval",
                "span_start": 0,
                "span_end": len(text)
            })
        
        context.agent_outputs["signature_checker"] = {
            "signatures_found": len(signatures_found),
            "signatures": signatures_found,
            "violations": violations
        }
        
        if violations:
            context.violations.extend(violations)
        
        logger.info(f"Signature Checker found {len(signatures_found)} signatures, {len(violations)} violations")
        return context

