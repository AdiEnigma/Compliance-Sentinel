#!/bin/bash
# Evaluation harness script

echo "Running Compliance Sentinel Evaluation..."

# Generate sample data if not exists
if [ ! -d "data/labeled" ] || [ -z "$(ls -A data/labeled)" ]; then
    echo "Generating sample data..."
    python scripts/generate_sample_data.py
fi

# Run evaluation tests
echo "Running evaluation tests..."
pytest tests/test_end_to_end.py::test_evaluation_harness -v

# Extract and print metrics (simplified - in real implementation, parse pytest output)
echo "Evaluation complete. Check test output for metrics."

