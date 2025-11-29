# Compliance Sentinel

**A multi-agent document compliance auditing system that automatically detects violations, proposes fixes, and makes approval decisions.**

## Elevator Pitch

Compliance Sentinel uses specialized AI agents to audit enterprise documents for policy violations, exposed PII, template drift, and missing approvals—delivering consistent, scalable compliance evaluation that adapts over time.

## Features

- **Multi-Agent Pipeline**: Specialized agents for classification, PII detection, policy checking, template comparison, and rewrite suggestions
- **Parallel Processing**: Scanners run in parallel for fast document processing
- **Memory Bank**: Stores templates and violation history for context-aware auditing
- **Auto-Fix Capability**: Automatically applies fixes for low-severity violations
- **Audit Trails**: Complete processing history with diffs and agent outputs
- **Observability**: Prometheus metrics and structured logging
- **Security**: PII redaction, uploader ID hashing, configurable encryption

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/AdiEnigma/Compliance-Sentinel.git
cd Compliance-Sentinel

# Start services
docker compose -f infra/docker-compose.yml up --build

# Services will be available at:
# - API: http://localhost:8000
# - Ticketing Mock: http://localhost:8001
# - API Docs: http://localhost:8000/docs
```

### Generate Sample Data

```bash
# Generate 30 labeled test documents
python scripts/generate_sample_data.py
```

### Run Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/ -v

# Run evaluation harness
bash scripts/run_evaluation.sh
```

### Demo Script

```bash
# Run end-to-end demo
bash scripts/demo.sh
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

### Agent Pipeline

1. **Triage Agent**: Classifies document type
2. **Parallel Scanners**: 
   - PII Scanner (regex + LLM confirmation)
   - Policy Rule Engine (deterministic rules)
   - Template Detector (embedding similarity)
   - Signature Checker (heuristic detection)
3. **Enrichment**: Fetches policy snippets and similar violations
4. **Rewrite Agent**: Generates suggested fixes
5. **Approval Agent**: Makes final decision (Auto-Approve, Auto-Fix, Require Review, Reject)

## API Usage

### Upload Document

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf" \
  -F "uploader_id=user123" \
  -F "department=legal"
```

Response:
```json
{
  "processing_id": "uuid-here",
  "message": "Document uploaded and processing started"
}
```

### Check Status

```bash
curl "http://localhost:8000/status/{processing_id}"
```

Response:
```json
{
  "processing_id": "uuid-here",
  "status": "completed",
  "document_type": "contract",
  "violations": [...],
  "suggestions": [...],
  "approval_decision": "Auto-Fix",
  "violation_score": 2
}
```

### Download Audit Trail

```bash
curl "http://localhost:8000/audit/{processing_id}/download" -o audit.zip
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LLM Configuration
USE_DEV_STUB_LLM=true  # Use stub LLM (no external calls)
OPENAI_API_KEY=        # Optional: for real LLM

# Feature Flags
USE_FAISS=true         # Use FAISS for vector store
USE_OCR=true           # Enable OCR for images

# Security
HASH_UPLOADER_IDS=true # Hash uploader IDs before storage
```

## Development Mode

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export USE_DEV_STUB_LLM=true
export USE_FAISS=true

# Run API
uvicorn api.main:app --reload

# Run ticketing mock (separate terminal)
uvicorn api.ticketing_mock:app --port 8001
```

### Dev Stub LLM Mode

By default, the system uses stub LLM mode (no external API calls). To enable real LLM:

1. Set `USE_DEV_STUB_LLM=false` in `.env`
2. Provide API keys: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. The system will redact PII before any external LLM calls

## Evaluation

The evaluation harness tests the system on a labeled dataset:

```bash
# Generate test data
python scripts/generate_sample_data.py

# Run evaluation
pytest tests/test_end_to_end.py::test_evaluation_harness -v
```

Metrics computed:
- **PII Detection**: Precision, Recall, F1
- **Template Drift**: Detection accuracy
- **Edit Acceptance**: Rate of accepted suggestions

Expected thresholds:
- PII Precision ≥ 0.85
- PII Recall ≥ 0.80

## Project Structure

```
compliance-sentinel/
├── api/                 # FastAPI application
│   ├── main.py         # Main API endpoints
│   ├── ticketing_mock.py  # Mock DMS service
│   └── audit_trail.py  # Audit trail management
├── agents/             # Multi-agent system
│   ├── orchestrator.py
│   ├── triage_agent.py
│   ├── scanners/      # Parallel scanning agents
│   ├── rewrite_agent.py
│   └── approval_agent.py
├── tools/              # Utilities
│   ├── parsers.py     # PDF/DOCX/OCR
│   ├── embeddings.py  # Sentence transformers
│   ├── vector_store.py # FAISS/SQLite
│   └── rule_definitions.py
├── memory/             # Memory Bank
│   └── memory_bank.py
├── tests/              # Test suite
├── scripts/            # Utility scripts
├── docs/               # Documentation
├── data/               # Data storage
│   ├── originals/     # Uploaded files
│   ├── labeled/       # Test dataset
│   └── audit_trails/  # Audit history
└── infra/             # Docker setup
```

## Security & Privacy

- **PII Redaction**: All PII automatically redacted before external LLM calls
- **Uploader ID Hashing**: Uploader IDs hashed before storage (configurable)
- **File Encryption**: Configurable encryption at rest (prototype stores plain files)
- **Dev Stub Mode**: Default mode avoids external API calls

## Observability

### Prometheus Metrics

Access metrics at `http://localhost:8000/metrics`:

- `documents_processed_total`: Total documents processed
- `violations_total{severity}`: Violations by severity
- `autopasses_total`: Auto-approved documents
- `auto_fix_applied_total`: Auto-fixes applied
- `processing_time_seconds`: Processing time histogram

### Structured Logging

All agent steps emit structured logs with:
- Document ID
- Agent name
- Processing step
- Violations found
- Decision made

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

[Specify license here]

## Author

**AdiEnigma**

- GitHub: [@AdiEnigma](https://github.com/AdiEnigma)

## Acknowledgments

Built with:
- FastAPI for the API layer
- Python ADK wrapper for agent orchestration
- Sentence Transformers for embeddings
- FAISS for vector similarity search
- Prometheus for metrics

## Additional Documentation

- [Architecture](docs/architecture.md): Detailed system architecture
- [Prompts](docs/prompts.md): LLM prompt templates
