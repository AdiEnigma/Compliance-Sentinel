"""
End-to-end tests for the compliance system.
"""
import pytest
import os
import json
from pathlib import Path
from httpx import AsyncClient
from api.main import app
from memory.memory_bank import MemoryBank


@pytest.mark.asyncio
async def test_upload_and_process():
    """Test document upload and processing."""
    # Create a test document
    test_doc = "This is a test contract. TERMINATION: This agreement may be terminated."
    test_file_path = "data/originals/test_doc.txt"
    os.makedirs("data/originals", exist_ok=True)
    
    with open(test_file_path, "w") as f:
        f.write(test_doc)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload document
        with open(test_file_path, "rb") as f:
            response = await client.post(
                "/upload",
                files={"file": ("test_doc.txt", f, "text/plain")},
                params={"uploader_id": "test_user", "department": "test"}
            )
        
        assert response.status_code == 200
        data = response.json()
        processing_id = data["processing_id"]
        
        # Wait for processing (simple polling)
        import asyncio
        for _ in range(10):
            await asyncio.sleep(1)
            status_response = await client.get(f"/status/{processing_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    assert "approval_decision" in status_data
                    break
        
        # Check final status
        status_response = await client.get(f"/status/{processing_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"


@pytest.mark.asyncio
async def test_evaluation_harness():
    """Run evaluation on labeled dataset."""
    labeled_dir = Path("data/labeled")
    if not labeled_dir.exists():
        pytest.skip("Labeled dataset not found. Run generate_sample_data.py first.")
    
    # Load labeled documents
    test_files = list(labeled_dir.glob("*.txt"))
    assert len(test_files) > 0, "No test files found"
    
    # Initialize memory bank and load templates
    memory_bank = MemoryBank()
    
    # Load templates
    template_dir = Path("docs/templates")
    if template_dir.exists():
        for template_file in template_dir.glob("*.txt"):
            template_id = template_file.stem
            with open(template_file, "r") as f:
                template_text = f.read()
            await memory_bank.store_template(template_id, template_text)
    
    # Process a subset of documents
    results = []
    for test_file in test_files[:10]:  # Process first 10 for speed
        with open(test_file, "r") as f:
            text = f.read()
        
        # Load labels
        label_file = test_file.with_suffix(".json")
        if label_file.exists():
            with open(label_file, "r") as f:
                labels = json.load(f)
            
            # Run through orchestrator (simplified)
            from agents.orchestrator import ComplianceOrchestrator
            orchestrator = ComplianceOrchestrator(memory_bank)
            
            result = await orchestrator.process_document(
                document_id=test_file.stem,
                document_text=text,
                metadata={"document_type": labels.get("document_type", "unknown")}
            )
            
            results.append({
                "file": test_file.name,
                "labels": labels,
                "result": result
            })
    
    # Compute metrics
    pii_true_positives = 0
    pii_false_positives = 0
    pii_false_negatives = 0
    
    for item in results:
        labels = item["labels"]
        result = item["result"]
        
        # Check PII detection
        ground_truth_pii = labels.get("pii_spans", [])
        detected_pii = [v for v in result.get("violations", []) if v.get("type") == "pii"]
        
        # Simple matching (can be improved)
        for gt in ground_truth_pii:
            gt_text = gt.get("text", "")
            if any(gt_text in d.get("text", "") for d in detected_pii):
                pii_true_positives += 1
            else:
                pii_false_negatives += 1
        
        for det in detected_pii:
            det_text = det.get("text", "")
            if not any(gt.get("text", "") in det_text for gt in ground_truth_pii):
                pii_false_positives += 1
    
    # Calculate precision and recall
    pii_precision = pii_true_positives / (pii_true_positives + pii_false_positives) if (pii_true_positives + pii_false_positives) > 0 else 0
    pii_recall = pii_true_positives / (pii_true_positives + pii_false_negatives) if (pii_true_positives + pii_false_negatives) > 0 else 0
    pii_f1 = 2 * (pii_precision * pii_recall) / (pii_precision + pii_recall) if (pii_precision + pii_recall) > 0 else 0
    
    print(f"\nEvaluation Metrics:")
    print(f"PII Precision: {pii_precision:.2f}")
    print(f"PII Recall: {pii_recall:.2f}")
    print(f"PII F1: {pii_f1:.2f}")
    
    # Assert minimum thresholds (adjustable)
    assert pii_precision >= 0.70, f"PII precision {pii_precision:.2f} below threshold 0.70"
    assert pii_recall >= 0.70, f"PII recall {pii_recall:.2f} below threshold 0.70"

