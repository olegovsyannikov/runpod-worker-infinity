#!/usr/bin/env bash

# Local testing script for the load balancing endpoint
# Usage: ./test_local.sh [type]
# Example: ./test_local.sh loadbalancer
#          ./test_local.sh serverless

set -e

TYPE="${1:-loadbalancer}"

if [[ "$TYPE" == "loadbalancer" ]]; then
  BASE_URL="${BASE_URL:-http://localhost:8080}"
  echo "Testing Infinity Load Balancing Endpoint at $BASE_URL"
elif [[ "$TYPE" == "serverless" ]]; then
  BASE_URL="${BASE_URL:-http://localhost:8000}"
  echo "Testing Infinity Serverless Endpoint at $BASE_URL"
  echo "Note: For serverless, use RunPod SDK or test_input.json for full testing"
else
  echo "Error: TYPE must be 'loadbalancer' or 'serverless'"
  exit 1
fi

echo "=========================================="
echo ""

if [[ "$TYPE" == "loadbalancer" ]]; then
  # Test 1: Health check
  echo "1. Testing health check (/ping)..."
  curl -s "$BASE_URL/ping" | jq .
  echo -e "\n"

  # Test 2: List models
  echo "2. Testing list models (/v1/models)..."
  curl -s "$BASE_URL/v1/models" | jq .
  echo -e "\n"

  # Test 3: Create embeddings (single input)
  echo "3. Testing embeddings - single input (/v1/embeddings)..."
  curl -s -X POST "$BASE_URL/v1/embeddings" \
    -H "Content-Type: application/json" \
    -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world"}' | jq .
  echo -e "\n"

  # Test 4: Create embeddings (multiple inputs)
  echo "4. Testing embeddings - multiple inputs (/v1/embeddings)..."
  curl -s -X POST "$BASE_URL/v1/embeddings" \
    -H "Content-Type: application/json" \
    -d '{"model":"BAAI/bge-small-en-v1.5","input":["Hello world","Another sentence","Third text"]}' | jq .
  echo -e "\n"

  # Test 5: Stats endpoint
  echo "5. Testing stats endpoint (/stats)..."
  curl -s "$BASE_URL/stats" | jq .
  echo -e "\n"
else
  # Serverless tests
  echo "1. Testing health check..."
  curl -s "$BASE_URL/health" | jq . 2>/dev/null || echo "Health endpoint may not be available in serverless mode"
  echo -e "\n"

  echo "For full serverless testing, use:"
  echo "  python test_input.json"
  echo "Or use the RunPod SDK"
fi

echo "=========================================="
echo "All tests completed!"
