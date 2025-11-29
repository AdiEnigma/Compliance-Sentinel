"""
Policy rule definitions for compliance checking.
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PolicyRule:
    """Represents a compliance policy rule."""
    rule_id: str
    name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    document_types: List[str]  # Which document types this applies to
    check_function: callable  # Function that takes (text, metadata) and returns violations


# Rule implementations
def check_contract_termination_clause(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if contract has termination clause."""
    violations = []
    text_lower = text.lower()
    
    termination_keywords = ["termination", "terminate", "end of agreement", "contract end"]
    has_termination = any(keyword in text_lower for keyword in termination_keywords)
    
    if not has_termination:
        violations.append({
            "rule_id": "CONTRACT_001",
            "severity": "high",
            "message": "Contract missing termination clause",
            "span_start": 0,
            "span_end": len(text)
        })
    
    return violations


def check_hr_manager_approval(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if HR form has manager approval field."""
    violations = []
    text_lower = text.lower()
    
    approval_keywords = ["manager approval", "approved by", "signature", "manager sign"]
    has_approval = any(keyword in text_lower for keyword in approval_keywords)
    
    if not has_approval:
        violations.append({
            "rule_id": "HR_001",
            "severity": "medium",
            "message": "HR form missing manager approval field",
            "span_start": 0,
            "span_end": len(text)
        })
    
    return violations


def check_policy_version_date(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if policy document has version and date."""
    violations = []
    text_lower = text.lower()
    
    has_version = "version" in text_lower or "v." in text_lower or "v " in text_lower
    has_date = any(keyword in text_lower for keyword in ["effective date", "date:", "dated", "as of"])
    
    if not has_version:
        violations.append({
            "rule_id": "POLICY_001",
            "severity": "medium",
            "message": "Policy document missing version number",
            "span_start": 0,
            "span_end": len(text)
        })
    
    if not has_date:
        violations.append({
            "rule_id": "POLICY_002",
            "severity": "medium",
            "message": "Policy document missing effective date",
            "span_start": 0,
            "span_end": len(text)
        })
    
    return violations


def check_invoice_tax_id(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if invoice has tax ID."""
    violations = []
    text_lower = text.lower()
    
    tax_keywords = ["tax id", "tax identification", "tin", "ein", "vat"]
    has_tax_id = any(keyword in text_lower for keyword in tax_keywords)
    
    if not has_tax_id:
        violations.append({
            "rule_id": "INVOICE_001",
            "severity": "high",
            "message": "Invoice missing tax identification number",
            "span_start": 0,
            "span_end": len(text)
        })
    
    return violations


# Rule registry
POLICY_RULES: List[PolicyRule] = [
    PolicyRule(
        rule_id="CONTRACT_001",
        name="Contract Termination Clause",
        description="Contracts must include a termination clause",
        severity="high",
        document_types=["contract", "agreement"],
        check_function=check_contract_termination_clause
    ),
    PolicyRule(
        rule_id="HR_001",
        name="HR Manager Approval",
        description="HR forms must include manager approval field",
        severity="medium",
        document_types=["hr_form", "hr_document"],
        check_function=check_hr_manager_approval
    ),
    PolicyRule(
        rule_id="POLICY_001",
        name="Policy Version",
        description="Policy documents must include version number",
        severity="medium",
        document_types=["policy", "policy_document"],
        check_function=check_policy_version_date
    ),
    PolicyRule(
        rule_id="INVOICE_001",
        name="Invoice Tax ID",
        description="Invoices must include tax identification number",
        severity="high",
        document_types=["invoice", "bill"],
        check_function=check_invoice_tax_id
    ),
]


def get_rules_for_document_type(doc_type: str) -> List[PolicyRule]:
    """Get all rules that apply to a document type."""
    return [rule for rule in POLICY_RULES if doc_type in rule.document_types or "all" in rule.document_types]

