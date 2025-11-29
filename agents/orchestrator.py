"""
Orchestrator that coordinates the multi-agent pipeline.
"""
import os
import asyncio
from typing import Dict, Any, List
import logging

from agents.adk_wrapper import Controller, AgentContext, InMemorySessionService
from agents.triage_agent import TriageAgent
from agents.scanners.pii_scanner import PIIScanner
from agents.scanners.policy_rule_engine import PolicyRuleEngine
from agents.scanners.template_detector import TemplateDetector
from agents.scanners.signature_checker import SignatureChecker
from agents.rewrite_agent import RewriteAgent
from agents.approval_agent import ApprovalAgent
from memory.memory_bank import MemoryBank

logger = logging.getLogger(__name__)


class ComplianceOrchestrator:
    """Orchestrates the multi-agent compliance checking pipeline."""
    
    def __init__(self, memory_bank: MemoryBank):
        self.memory_bank = memory_bank
        self.controller = Controller()
        self.session_service = InMemorySessionService()
        self.controller.session_service = self.session_service
        
        # Register agents
        self.triage_agent = TriageAgent()
        self.pii_scanner = PIIScanner()
        self.policy_engine = PolicyRuleEngine()
        self.template_detector = TemplateDetector(memory_bank)
        self.signature_checker = SignatureChecker()
        self.rewrite_agent = RewriteAgent(memory_bank)
        self.approval_agent = ApprovalAgent()
        
        self.controller.register_agent(self.triage_agent)
        # Scanners run in parallel after triage
        # Rewrite and approval run sequentially after scanners
    
    async def process_document(
        self,
        document_id: str,
        document_text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a document through the full pipeline."""
        # Create session
        session_id = await self.session_service.create_session(document_id)
        
        # Create context
        context = AgentContext(
            document_id=document_id,
            session_id=session_id,
            document_text=document_text,
            metadata=metadata
        )
        
        # Step 1: Triage (classify document type)
        logger.info(f"Processing document {document_id}: Starting triage")
        context = await self.triage_agent.execute(context)
        
        # Step 2: Run scanners in parallel
        logger.info(f"Processing document {document_id}: Running parallel scanners")
        scanner_results = await self.controller.run_parallel(
            [self.pii_scanner, self.policy_engine, self.template_detector, self.signature_checker],
            context
        )
        
        # Merge scanner results into context
        for agent_name, result_context in scanner_results.items():
            context.agent_outputs[agent_name] = result_context.agent_outputs.get(agent_name, {})
            # Merge violations (avoid duplicates)
            for violation in result_context.violations:
                if violation not in context.violations:
                    context.violations.append(violation)
        
        # Step 3: Enrichment (fetch policy snippets and similar violations)
        logger.info(f"Processing document {document_id}: Enriching with policy context")
        await self._enrich_context(context)
        
        # Step 4: Rewrite agent
        logger.info(f"Processing document {document_id}: Generating rewrite suggestions")
        context = await self.rewrite_agent.execute(context)
        
        # Step 5: Approval agent
        logger.info(f"Processing document {document_id}: Computing approval decision")
        context = await self.approval_agent.execute(context)
        
        # Save final state
        await self.session_service.save_state(session_id, context)
        
        # Return results
        return {
            "document_id": document_id,
            "session_id": session_id,
            "document_type": context.metadata.get("document_type"),
            "violations": context.violations,
            "suggestions": context.suggestions,
            "approval_decision": context.metadata.get("approval_decision"),
            "approval_reason": context.metadata.get("approval_reason"),
            "violation_score": context.metadata.get("violation_score", 0),
            "agent_outputs": context.agent_outputs
        }
    
    async def _enrich_context(self, context: AgentContext):
        """Enrich violations with policy snippets and similar past violations."""
        enriched_violations = []
        
        for violation in context.violations:
            enriched = violation.copy()
            
            # Get policy snippet
            rule_id = violation.get("rule_id")
            if rule_id:
                policy_snippet = await self.memory_bank.get_policy_snippet(rule_id)
                enriched["policy_snippet"] = policy_snippet
            
            # Get similar past violations
            violation_text = violation.get("text", violation.get("message", ""))
            if violation_text:
                similar_violations = await self.memory_bank.search_violations(violation_text, top_k=3)
                enriched["similar_violations"] = similar_violations
            
            enriched_violations.append(enriched)
        
        context.violations = enriched_violations

