#!/bin/bash
# Demo script for Compliance Sentinel

echo "Starting Compliance Sentinel Demo..."

# Start services
echo "Starting Docker Compose services..."
docker-compose -f infra/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Generate sample data
echo "Generating sample data..."
python scripts/generate_sample_data.py

# Upload a test document
echo "Uploading test document..."
curl -X POST "http://localhost:8000/upload" \
  -F "file=@data/labeled/contract_01.txt" \
  -F "uploader_id=demo_user" \
  -F "department=legal"

echo ""
echo "Demo complete! Check http://localhost:8000/docs for API documentation."

