"""
Tests for PII detection.
"""
import pytest
from agents.scanners.pii_scanner import PIIScanner
from agents.adk_wrapper import AgentContext


@pytest.mark.asyncio
async def test_email_detection():
    """Test email PII detection."""
    scanner = PIIScanner()
    context = AgentContext(
        document_id="test_1",
        session_id="session_1",
        document_text="Contact us at support@example.com for assistance."
    )
    
    result = await scanner.execute(context)
    
    assert len(result.violations) > 0
    email_violations = [v for v in result.violations if v["pii_type"] == "email"]
    assert len(email_violations) > 0
    assert "support@example.com" in email_violations[0]["text"]


@pytest.mark.asyncio
async def test_phone_detection():
    """Test phone number PII detection."""
    scanner = PIIScanner()
    context = AgentContext(
        document_id="test_2",
        session_id="session_2",
        document_text="Call us at 555-123-4567 for support."
    )
    
    result = await scanner.execute(context)
    
    phone_violations = [v for v in result.violations if v["pii_type"] == "phone"]
    assert len(phone_violations) > 0


@pytest.mark.asyncio
async def test_ssn_detection():
    """Test SSN PII detection."""
    scanner = PIIScanner()
    context = AgentContext(
        document_id="test_3",
        session_id="session_3",
        document_text="SSN: 123-45-6789"
    )
    
    result = await scanner.execute(context)
    
    ssn_violations = [v for v in result.violations if v["pii_type"] == "ssn"]
    assert len(ssn_violations) > 0
    assert ssn_violations[0]["severity"] == "high"

