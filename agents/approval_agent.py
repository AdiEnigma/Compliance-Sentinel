"""
Approval scoring agent that decides final document status.
"""
from typing import Dict, Any
import logging

from agents.adk_wrapper import Agent, AgentContext

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    "critical": 10,
    "high": 5,
    "medium": 2,
    "low": 1
}


class ApprovalAgent(Agent):
    """Makes final approval decision based on violations and suggestions."""
    
    def __init__(self):
        super().__init__(
            name="approval_agent",
            description="Makes final approval decision for documents"
        )
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Compute approval decision."""
        violations = context.violations
        suggestions = context.suggestions
        
        # Compute violation score
        violation_score = 0
        critical_violations = []
        high_violations = []
        medium_violations = []
        low_violations = []
        
        for violation in violations:
            severity = violation.get("severity", "low")
            weight = SEVERITY_WEIGHTS.get(severity, 1)
            violation_score += weight
            
            if severity == "critical":
                critical_violations.append(violation)
            elif severity == "high":
                high_violations.append(violation)
            elif severity == "medium":
                medium_violations.append(violation)
            else:
                low_violations.append(violation)
        
        # Determine decision
        if violation_score == 0:
            decision = "Auto-Approve"
            decision_reason = "No violations detected"
        elif violation_score <= 2 and len(suggestions) > 0:
            # Low severity with fixes available
            decision = "Auto-Fix"
            decision_reason = f"Low severity violations ({violation_score} points) with available fixes"
        elif violation_score <= 5:
            decision = "Require Review"
            decision_reason = f"Medium severity violations ({violation_score} points) require human review"
        else:
            decision = "Reject"
            decision_reason = f"High severity violations ({violation_score} points) cannot be auto-fixed"
        
        # Store decision
        context.metadata["approval_decision"] = decision
        context.metadata["approval_reason"] = decision_reason
        context.metadata["violation_score"] = violation_score
        
        context.agent_outputs["approval_agent"] = {
            "decision": decision,
            "reason": decision_reason,
            "violation_score": violation_score,
            "violation_counts": {
                "critical": len(critical_violations),
                "high": len(high_violations),
                "medium": len(medium_violations),
                "low": len(low_violations)
            }
        }
        
        logger.info(f"Approval Agent decision: {decision} (score: {violation_score})")
        return context

