"""
Rewrite agent that proposes fixes for violations.
"""
import os
import json
from typing import List, Dict, Any
import logging
import hashlib

from agents.adk_wrapper import Agent, AgentContext
from agents.scanners.pii_scanner import redact_pii

logger = logging.getLogger(__name__)


async def generate_rewrite_with_llm(
    violation_span: str,
    policy_snippet: str,
    template_snippet: str,
    style_constraints: str,
    use_stub: bool = True
) -> Dict[str, Any]:
    """Generate rewrite suggestion using LLM (or stub)."""
    if use_stub or os.getenv("USE_DEV_STUB_LLM", "true").lower() == "true":
        # Stub mode: generate simple fix
        return {
            "replacement": violation_span + " [COMPLIANCE FIX APPLIED]",
            "explanation": [
                "Applied policy compliance fix",
                "Maintains document intent",
                "Follows template guidelines"
            ],
            "citations": ["POLICY_001"],
            "redaction_flag": False
        }
    
    # Real LLM call would go here with redacted context
    return {
        "replacement": violation_span,
        "explanation": ["No changes needed"],
        "citations": [],
        "redaction_flag": False
    }


class RewriteAgent(Agent):
    """Proposes fixes for detected violations."""
    
    def __init__(self, memory_bank):
        super().__init__(
            name="rewrite_agent",
            description="Generates suggested fixes for compliance violations"
        )
        self.memory_bank = memory_bank
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Generate rewrite suggestions for violations."""
        text = context.document_text
        violations = context.violations
        
        suggestions = []
        
        for violation in violations:
            if violation.get("type") == "pii":
                # For PII, suggest redaction
                suggestions.append({
                    "violation_id": violation.get("pii_type"),
                    "span_start": violation["span_start"],
                    "span_end": violation["span_end"],
                    "original_text": violation["text"],
                    "replacement": "[REDACTED]",
                    "explanation": [f"Redact {violation['pii_type']} to protect privacy"],
                    "redaction_flag": True
                })
            else:
                # For policy violations, generate rewrite
                violation_span = text[violation["span_start"]:violation["span_end"]]
                
                # Get policy snippet
                rule_id = violation.get("rule_id", "")
                policy_snippet = await self.memory_bank.get_policy_snippet(rule_id) or ""
                
                # Get template snippet (if available)
                template_results = await self.memory_bank.search_templates(violation_span, top_k=1)
                template_snippet = template_results[0].get("text", "") if template_results else ""
                
                # Redact PII before sending to LLM
                pii_violations = [v for v in violations if v.get("type") == "pii"]
                redacted_span = redact_pii(violation_span, pii_violations)
                
                rewrite = await generate_rewrite_with_llm(
                    redacted_span,
                    policy_snippet,
                    template_snippet,
                    "Maintain professional tone"
                )
                
                suggestions.append({
                    "violation_id": violation.get("rule_id", violation.get("type")),
                    "span_start": violation["span_start"],
                    "span_end": violation["span_end"],
                    "original_text": violation_span,
                    "replacement": rewrite["replacement"],
                    "explanation": rewrite["explanation"],
                    "citations": rewrite.get("citations", []),
                    "redaction_flag": rewrite.get("redaction_flag", False)
                })
        
        context.suggestions = suggestions
        context.agent_outputs["rewrite_agent"] = {
            "suggestions_generated": len(suggestions),
            "suggestions": suggestions
        }
        
        logger.info(f"Rewrite Agent generated {len(suggestions)} suggestions")
        return context

