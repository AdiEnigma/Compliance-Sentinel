"""
Policy rule engine for deterministic compliance checking.
"""
from typing import List, Dict, Any
import logging

from agents.adk_wrapper import Agent, AgentContext
from tools.rule_definitions import get_rules_for_document_type, POLICY_RULES

logger = logging.getLogger(__name__)


class PolicyRuleEngine(Agent):
    """Checks documents against policy rules."""
    
    def __init__(self):
        super().__init__(
            name="policy_rule_engine",
            description="Applies deterministic policy rules to documents"
        )
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Apply policy rules to document."""
        text = context.document_text
        doc_type = context.metadata.get("document_type", "unknown")
        
        # Get applicable rules
        applicable_rules = get_rules_for_document_type(doc_type)
        
        violations = []
        for rule in applicable_rules:
            rule_violations = rule.check_function(text, context.metadata)
            for violation in rule_violations:
                violation["rule_id"] = rule.rule_id
                violation["rule_name"] = rule.name
                violation["type"] = "policy_violation"
                violations.append(violation)
        
        # Store violations
        context.violations.extend(violations)
        context.agent_outputs["policy_rule_engine"] = {
            "rules_checked": len(applicable_rules),
            "violations_found": len(violations),
            "violations": violations
        }
        
        logger.info(f"Policy Rule Engine found {len(violations)} violations")
        return context

