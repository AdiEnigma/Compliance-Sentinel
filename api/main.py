"""
FastAPI main application for Compliance Sentinel.
"""
import os
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from tools.parsers import parse_document
from agents.orchestrator import ComplianceOrchestrator
from memory.memory_bank import MemoryBank
from api.audit_trail import AuditTrailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
memory_bank = MemoryBank()
orchestrator = ComplianceOrchestrator(memory_bank)
audit_trail = AuditTrailService()

# Prometheus metrics
documents_processed = Counter('documents_processed_total', 'Total documents processed')
violations_total = Counter('violations_total', 'Total violations detected', ['severity'])
autopasses_total = Counter('autopasses_total', 'Total auto-approved documents')
auto_fix_accept_rate = Counter('auto_fix_applied_total', 'Total auto-fixes applied')
processing_time = Histogram('processing_time_seconds', 'Document processing time', buckets=[1, 5, 10, 30, 60])

app = FastAPI(title="Compliance Sentinel API", version="1.0.0")

# In-memory storage for processing status
processing_status = {}


class UploadResponse(BaseModel):
    processing_id: str
    message: str


class StatusResponse(BaseModel):
    processing_id: str
    status: str
    document_type: Optional[str] = None
    violations: list = []
    suggestions: list = []
    approval_decision: Optional[str] = None
    approval_reason: Optional[str] = None
    violation_score: int = 0
    agent_outputs: dict = {}


async def process_document_background(processing_id: str, file_path: str, uploader_id: str, department: str):
    """Background task to process document."""
    try:
        with processing_time.time():
            # Parse document
            parsed = parse_document(file_path)
            document_text = parsed["full_text"]
            
            # Hash uploader ID if configured
            if os.getenv("HASH_UPLOADER_IDS", "true").lower() == "true":
                uploader_id = hashlib.sha256(uploader_id.encode()).hexdigest()[:16]
            
            # Process through orchestrator
            result = await orchestrator.process_document(
                document_id=processing_id,
                document_text=document_text,
                metadata={
                    "uploader_id": uploader_id,
                    "department": department,
                    "file_path": file_path,
                    "parsed_metadata": parsed["metadata"]
                }
            )
            
            # Update status
            processing_status[processing_id] = {
                "status": "completed",
                **result
            }
            
            # Save audit trail
            await audit_trail.save_audit_trail(
                processing_id=processing_id,
                original_file=file_path,
                result=result,
                parsed_document=parsed
            )
            
            # Update metrics
            documents_processed.inc()
            for violation in result.get("violations", []):
                severity = violation.get("severity", "unknown")
                violations_total.labels(severity=severity).inc()
            
            if result.get("approval_decision") == "Auto-Approve":
                autopasses_total.inc()
            elif result.get("approval_decision") == "Auto-Fix":
                auto_fix_accept_rate.inc()
            
            logger.info(f"Document {processing_id} processed successfully")
    
    except Exception as e:
        logger.error(f"Error processing document {processing_id}: {e}", exc_info=True)
        processing_status[processing_id] = {
            "status": "error",
            "error": str(e)
        }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    uploader_id: str = "anonymous",
    department: str = "unknown",
    doc_id: Optional[str] = None
):
    """Upload a document for compliance checking."""
    # Generate processing ID
    processing_id = doc_id or str(uuid.uuid4())
    
    # Save uploaded file
    os.makedirs("data/originals", exist_ok=True)
    file_path = f"data/originals/{processing_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Initialize status
    processing_status[processing_id] = {"status": "processing"}
    
    # Start background processing
    background_tasks.add_task(process_document_background, processing_id, file_path, uploader_id, department)
    
    return UploadResponse(
        processing_id=processing_id,
        message="Document uploaded and processing started"
    )


@app.get("/status/{processing_id}", response_model=StatusResponse)
async def get_status(processing_id: str):
    """Get processing status for a document."""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    status = processing_status[processing_id]
    
    if status["status"] == "processing":
        return StatusResponse(
            processing_id=processing_id,
            status="processing"
        )
    elif status["status"] == "error":
        raise HTTPException(status_code=500, detail=status.get("error", "Processing error"))
    else:
        return StatusResponse(
            processing_id=processing_id,
            status="completed",
            document_type=status.get("document_type"),
            violations=status.get("violations", []),
            suggestions=status.get("suggestions", []),
            approval_decision=status.get("approval_decision"),
            approval_reason=status.get("approval_reason"),
            violation_score=status.get("violation_score", 0),
            agent_outputs=status.get("agent_outputs", {})
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "compliance-sentinel"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/audit/{processing_id}/download")
async def download_audit_trail(processing_id: str):
    """Download audit trail bundle."""
    audit_path = await audit_trail.get_audit_bundle_path(processing_id)
    if not audit_path or not os.path.exists(audit_path):
        raise HTTPException(status_code=404, detail="Audit trail not found")
    
    return FileResponse(
        audit_path,
        media_type="application/zip",
        filename=f"audit_{processing_id}.zip"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

