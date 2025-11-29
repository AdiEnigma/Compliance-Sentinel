# Compliance Sentinel Architecture

## Overview

Compliance Sentinel is a multi-agent document compliance auditing system that uses specialized agents to detect violations, propose fixes, and make approval decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI HTTP API                         │
│  /upload, /status/{id}, /metrics, /audit/{id}/download     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Compliance Orchestrator                     │
│  Coordinates agent execution in sequence and parallel        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Triage Agent │ │   Scanners   │ │ Rewrite Agent│
│ (Sequential) │ │  (Parallel)  │ │ (Sequential) │
└──────────────┘ └──────────────┘ └──────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PII Scanner │ │Policy Engine │ │Template Det.│
└──────────────┘ └──────────────┘ └──────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Memory Bank                               │
│  - Template embeddings (FAISS/SQLite)                       │
│  - Violation history                                         │
│  - Policy snippets                                           │
└─────────────────────────────────────────────────────────────┘
```

## Agent Pipeline

### 1. Triage Agent (Sequential)
- **Input**: Raw document text
- **Output**: Document type classification, metadata
- **Purpose**: Classify document to determine which rules apply

### 2. Parallel Scanners
All scanners run in parallel after triage:

#### PII Scanner
- Uses regex patterns for common PII (email, phone, SSN, etc.)
- Optional LLM confirmation for ambiguous patterns
- Redacts PII before external LLM calls

#### Policy Rule Engine
- Applies deterministic rules based on document type
- Checks for required clauses, fields, formats
- Returns violations with severity levels

#### Template Detector
- Computes embedding similarity to canonical templates
- Flags chunks with low similarity as template drift
- Uses Memory Bank for template storage

#### Signature Checker
- Detects signature fields and approval blocks
- Flags missing signatures based on document type

### 3. Enrichment Service
- Fetches policy snippets for each violation
- Retrieves similar past violations from Memory Bank
- Adds context to violations

### 4. Rewrite Agent (Sequential)
- Generates suggested fixes for violations
- Uses LLM (or stub) with redacted context
- Returns replacement text and explanations

### 5. Approval Agent (Sequential)
- Computes violation score based on severity
- Makes final decision:
  - **Auto-Approve**: No violations
  - **Auto-Fix**: Low severity with available fixes
  - **Require Review**: Medium/high severity
  - **Reject**: Critical violations

## Data Flow

1. **Upload**: Document uploaded via `/upload` endpoint
2. **Parse**: Document parsed (PDF/DOCX/OCR) into text blocks
3. **Process**: Orchestrator runs agents through pipeline
4. **Store**: Results stored in audit trail
5. **Return**: Status available via `/status/{id}`

## Memory Bank

The Memory Bank stores:
- **Templates**: Canonical document templates with embeddings
- **Violations**: Past violation examples for context
- **Policies**: Policy snippets referenced by rule IDs

Uses FAISS for vector similarity search with SQLite fallback.

## Security & Privacy

- **PII Redaction**: All PII redacted/hashed before external LLM calls
- **Uploader ID Hashing**: Uploader IDs hashed before storage
- **File Encryption**: Configurable encryption at rest (prototype stores plain)
- **Dev Stub Mode**: Default mode uses stub LLM to avoid external calls

## Observability

- **Prometheus Metrics**: `/metrics` endpoint with counters and histograms
- **Structured Logging**: JSON-formatted logs for each agent step
- **Audit Trails**: Complete processing history stored per document

## Scalability

- **Parallel Processing**: Scanners run in parallel for speed
- **Chunking**: Long documents processed in chunks
- **Session Management**: In-memory session service (can be extended to Redis)
- **Vector Store**: FAISS for fast similarity search

