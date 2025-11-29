#!/bin/bash
# Setup script for Compliance Sentinel

echo "Setting up Compliance Sentinel..."

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p data/originals data/labeled data/audit_trails data/memory_bank

# Generate sample data
echo "Generating sample data..."
python scripts/generate_sample_data.py

# Initialize memory bank with templates
echo "Initializing memory bank..."
python infra/init_db.py

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review .env file and configure as needed"
echo "2. Run: docker compose -f infra/docker-compose.yml up --build"
echo "3. Or run locally: uvicorn api.main:app --reload"

