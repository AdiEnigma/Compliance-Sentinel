"""
Tests for template drift detection.
"""
import pytest
from agents.scanners.template_detector import TemplateDetector
from memory.memory_bank import MemoryBank
from agents.adk_wrapper import AgentContext


@pytest.mark.asyncio
async def test_template_similarity():
    """Test template similarity detection."""
    memory_bank = MemoryBank()
    
    # Store a template
    await memory_bank.store_template(
        template_id="test_template",
        text="This is a test template with specific wording."
    )
    
    detector = TemplateDetector(memory_bank)
    
    # Test with similar text
    context = AgentContext(
        document_id="test_1",
        session_id="session_1",
        document_text="This is a test template with specific wording. Additional content here."
    )
    
    result = await detector.execute(context)
    # Should have low violations (high similarity)
    assert len(result.violations) == 0 or all(v.get("similarity", 0) > 0.7 for v in result.violations)


@pytest.mark.asyncio
async def test_template_drift():
    """Test template drift detection."""
    memory_bank = MemoryBank()
    
    await memory_bank.store_template(
        template_id="contract_template",
        text="CONTRACT AGREEMENT\n\nTERMINATION: This agreement may be terminated."
    )
    
    detector = TemplateDetector(memory_bank)
    
    # Test with different text (drift)
    context = AgentContext(
        document_id="test_2",
        session_id="session_2",
        document_text="This is completely different content that does not match the template at all."
    )
    
    result = await detector.execute(context)
    # Should detect drift
    assert len(result.violations) > 0

