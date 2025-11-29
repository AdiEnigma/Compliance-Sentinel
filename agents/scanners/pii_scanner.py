"""
PII Scanner agent using regex patterns and optional LLM confirmation.
"""
import re
import os
from typing import List, Dict, Any
import logging
import hashlib

from agents.adk_wrapper import Agent, AgentContext

logger = logging.getLogger(__name__)

# PII regex patterns
PII_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone": re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "credit_card": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    "iban": re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b'),
    "account_number": re.compile(r'\b\d{8,12}\b'),
}


def redact_pii(text: str, spans: List[Dict[str, Any]]) -> str:
    """Redact PII from text by replacing with hash."""
    redacted = text
    # Sort spans by start position (reverse to maintain indices)
    sorted_spans = sorted(spans, key=lambda x: x["span_start"], reverse=True)
    
    for span in sorted_spans:
        start = span["span_start"]
        end = span["span_end"]
        pii_text = text[start:end]
        # Hash the PII
        pii_hash = hashlib.sha256(pii_text.encode()).hexdigest()[:8]
        redacted = redacted[:start] + f"[REDACTED_{pii_hash}]" + redacted[end:]
    
    return redacted


async def confirm_pii_with_llm(span_text: str, context_text: str, pii_type: str, use_stub: bool = True) -> Dict[str, Any]:
    """Confirm PII detection with LLM (or stub)."""
    if use_stub or os.getenv("USE_DEV_STUB_LLM", "true").lower() == "true":
        # Stub mode: return high confidence for obvious patterns
        return {
            "confirmed": True,
            "confidence": 0.9,
            "rationale": "Stub LLM: Pattern matches expected format"
        }
    
    # Real LLM call would go here
    # For now, return stub response
    return {
        "confirmed": True,
        "confidence": 0.85,
        "rationale": "Pattern matches expected format"
    }


class PIIScanner(Agent):
    """Scans documents for PII using regex and LLM confirmation."""
    
    def __init__(self):
        super().__init__(
            name="pii_scanner",
            description="Detects personally identifiable information in documents"
        )
        self.use_llm_confirmation = os.getenv("USE_LLM_PII_CONFIRM", "false").lower() == "true"
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Scan document for PII."""
        text = context.document_text
        violations = []
        
        # Scan for each PII type
        for pii_type, pattern in PII_PATTERNS.items():
            matches = pattern.finditer(text)
            for match in matches:
                span_start = match.start()
                span_end = match.end()
                span_text = match.group()
                
                # For ambiguous patterns, use LLM confirmation
                if self.use_llm_confirmation and pii_type in ["account_number", "iban"]:
                    # Get context around match
                    context_start = max(0, span_start - 100)
                    context_end = min(len(text), span_end + 100)
                    context_snippet = text[context_start:context_end]
                    
                    confirmation = await confirm_pii_with_llm(span_text, context_snippet, pii_type)
                    if not confirmation["confirmed"]:
                        continue
                    confidence = confirmation["confidence"]
                else:
                    confidence = 0.95  # High confidence for regex matches
                
                violations.append({
                    "type": "pii",
                    "pii_type": pii_type,
                    "span_start": span_start,
                    "span_end": span_end,
                    "text": span_text,
                    "confidence": confidence,
                    "severity": "high" if pii_type in ["ssn", "credit_card"] else "medium"
                })
        
        # Store violations in context
        context.violations.extend(violations)
        context.agent_outputs["pii_scanner"] = {
            "violations_found": len(violations),
            "violations": violations
        }
        
        logger.info(f"PII Scanner found {len(violations)} PII instances")
        return context

