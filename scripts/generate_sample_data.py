"""
Generate synthetic test data for evaluation.
"""
import os
import json
from pathlib import Path
from datetime import datetime
import random

# Create directories
os.makedirs("data/labeled", exist_ok=True)
os.makedirs("docs/templates", exist_ok=True)

# Sample data templates
CONTRACT_TEMPLATE = """CONTRACT AGREEMENT

This Agreement is entered into on {date} between Party A and Party B.

TERMINATION: This agreement may be terminated by either party with 30 days written notice.

PAYMENT TERMS: Payment shall be made within 30 days of invoice receipt.

SIGNED BY:
Party A: ___________________
Party B: ___________________
"""

HR_FORM_TEMPLATE = """EMPLOYEE REQUEST FORM

Employee Name: {name}
Department: {department}
Request Type: {request_type}

MANAGER APPROVAL REQUIRED:
Manager Signature: ___________________
Date: {date}
"""

POLICY_TEMPLATE = """COMPANY POLICY DOCUMENT

Version: {version}
Effective Date: {date}

POLICY STATEMENT:
{policy_text}

This policy is subject to review and update.
"""

INVOICE_TEMPLATE = """INVOICE

Invoice Number: {invoice_number}
Date: {date}
Bill To: {company}

Items:
{items}

Total Amount: ${amount}

TAX ID: {tax_id}
"""

# Generate contracts (10)
contracts = []
for i in range(10):
    doc_id = f"contract_{i+1:02d}"
    has_termination = i < 8  # 8 have termination, 2 don't
    has_pii = i < 5  # 5 have PII
    
    text = CONTRACT_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        party_a="Acme Corp",
        party_b="Tech Solutions Inc"
    )
    
    if not has_termination:
        text = text.replace("TERMINATION: This agreement may be terminated by either party with 30 days written notice.", "")
    
    if has_pii:
        # Inject PII
        text = text.replace("Party A", "John Doe (john.doe@example.com, Phone: 555-123-4567)")
    
    # Save document
    with open(f"data/labeled/{doc_id}.txt", "w") as f:
        f.write(text)
    
    # Create labels
    labels = {
        "document_type": "contract",
        "pii_spans": [],
        "violations": []
    }
    
    if has_pii:
        # Find PII spans
        email_start = text.find("john.doe@example.com")
        if email_start >= 0:
            labels["pii_spans"].append({
                "span_start": email_start,
                "span_end": email_start + len("john.doe@example.com"),
                "pii_type": "email",
                "text": "john.doe@example.com"
            })
        phone_start = text.find("555-123-4567")
        if phone_start >= 0:
            labels["pii_spans"].append({
                "span_start": phone_start,
                "span_end": phone_start + len("555-123-4567"),
                "pii_type": "phone",
                "text": "555-123-4567"
            })
    
    if not has_termination:
        labels["violations"].append({
            "rule_id": "CONTRACT_001",
            "type": "policy_violation",
            "severity": "high"
        })
    
    with open(f"data/labeled/{doc_id}.json", "w") as f:
        json.dump(labels, f, indent=2)
    
    contracts.append(doc_id)

# Generate policies (8)
for i in range(8):
    doc_id = f"policy_{i+1:02d}"
    has_version = i < 6
    has_date = i < 7
    
    text = POLICY_TEMPLATE.format(
        version=f"v{i+1}.0" if has_version else "",
        date=datetime.now().strftime("%Y-%m-%d") if has_date else "",
        policy_text="This policy outlines the company's compliance requirements."
    )
    
    if not has_version:
        text = text.replace("Version: {version}\n", "")
    if not has_date:
        text = text.replace("Effective Date: {date}\n", "")
    
    with open(f"data/labeled/{doc_id}.txt", "w") as f:
        f.write(text)
    
    labels = {
        "document_type": "policy",
        "violations": []
    }
    
    if not has_version:
        labels["violations"].append({
            "rule_id": "POLICY_001",
            "type": "policy_violation",
            "severity": "medium"
        })
    if not has_date:
        labels["violations"].append({
            "rule_id": "POLICY_002",
            "type": "policy_violation",
            "severity": "medium"
        })
    
    with open(f"data/labeled/{doc_id}.json", "w") as f:
        json.dump(labels, f, indent=2)

# Generate HR forms (6)
for i in range(6):
    doc_id = f"hr_form_{i+1:02d}"
    has_approval = i < 4
    
    text = HR_FORM_TEMPLATE.format(
        name=f"Employee {i+1}",
        department="Engineering",
        request_type="Vacation Request",
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    if not has_approval:
        text = text.replace("MANAGER APPROVAL REQUIRED:\nManager Signature: ___________________\nDate: {date}", "")
    
    with open(f"data/labeled/{doc_id}.txt", "w") as f:
        f.write(text)
    
    labels = {
        "document_type": "hr_form",
        "violations": []
    }
    
    if not has_approval:
        labels["violations"].append({
            "rule_id": "HR_001",
            "type": "policy_violation",
            "severity": "medium"
        })
    
    with open(f"data/labeled/{doc_id}.json", "w") as f:
        json.dump(labels, f, indent=2)

# Generate invoices (6)
for i in range(6):
    doc_id = f"invoice_{i+1:02d}"
    has_tax_id = i < 4
    
    text = INVOICE_TEMPLATE.format(
        invoice_number=f"INV-{i+1:04d}",
        date=datetime.now().strftime("%Y-%m-%d"),
        company="Client Corp",
        items="Item 1: $100\nItem 2: $200",
        amount=300,
        tax_id=f"TAX-{i+1:06d}" if has_tax_id else ""
    )
    
    if not has_tax_id:
        text = text.replace("TAX ID: {tax_id}\n", "")
    
    with open(f"data/labeled/{doc_id}.txt", "w") as f:
        f.write(text)
    
    labels = {
        "document_type": "invoice",
        "violations": []
    }
    
    if not has_tax_id:
        labels["violations"].append({
            "rule_id": "INVOICE_001",
            "type": "policy_violation",
            "severity": "high"
        })
    
    with open(f"data/labeled/{doc_id}.json", "w") as f:
        json.dump(labels, f, indent=2)

# Create canonical templates
templates = {
    "contract_template": CONTRACT_TEMPLATE.format(
        date="{date}",
        party_a="{party_a}",
        party_b="{party_b}"
    ),
    "hr_form_template": HR_FORM_TEMPLATE.format(
        name="{name}",
        department="{department}",
        request_type="{request_type}",
        date="{date}"
    ),
    "policy_template": POLICY_TEMPLATE.format(
        version="{version}",
        date="{date}",
        policy_text="{policy_text}"
    ),
    "invoice_template": INVOICE_TEMPLATE.format(
        invoice_number="{invoice_number}",
        date="{date}",
        company="{company}",
        items="{items}",
        amount="{amount}",
        tax_id="{tax_id}"
    )
}

for template_id, template_text in templates.items():
    with open(f"docs/templates/{template_id}.txt", "w") as f:
        f.write(template_text)

print("Generated 30 labeled documents and 4 templates")

