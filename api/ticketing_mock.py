"""
Mock DMS/Ticketing service for routing human-review tasks.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime

app = FastAPI(title="Mock Ticketing Service", version="1.0.0")

# In-memory ticket storage
tickets = {}


class CreateTicketRequest(BaseModel):
    document_id: str
    processing_id: str
    violation_summary: str
    severity: str
    department: Optional[str] = None
    assignee: Optional[str] = None


class TicketResponse(BaseModel):
    ticket_id: str
    document_id: str
    processing_id: str
    status: str
    created_at: str
    violation_summary: str
    severity: str


@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(request: CreateTicketRequest):
    """Create a new review ticket."""
    ticket_id = str(uuid.uuid4())
    
    ticket = {
        "ticket_id": ticket_id,
        "document_id": request.document_id,
        "processing_id": request.processing_id,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "violation_summary": request.violation_summary,
        "severity": request.severity,
        "department": request.department,
        "assignee": request.assignee
    }
    
    tickets[ticket_id] = ticket
    
    return TicketResponse(**ticket)


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get ticket by ID."""
    if ticket_id not in tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return TicketResponse(**tickets[ticket_id])


@app.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(status: Optional[str] = None):
    """List all tickets, optionally filtered by status."""
    ticket_list = list(tickets.values())
    
    if status:
        ticket_list = [t for t in ticket_list if t["status"] == status]
    
    return [TicketResponse(**t) for t in ticket_list]


@app.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, status: str):
    """Update ticket status."""
    if ticket_id not in tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    tickets[ticket_id]["status"] = status
    return {"message": "Ticket updated", "ticket_id": ticket_id}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ticketing-mock"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

