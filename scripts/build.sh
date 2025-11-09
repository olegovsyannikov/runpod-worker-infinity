#!/usr/bin/env bash

# Build script for Docker images
# Usage: ./build.sh [type] [tag] [push]
# Example: ./build.sh loadbalancer v1.0.0 push
#          ./build.sh serverless latest push

set -e

# Configuration
TYPE="${1:-loadbalancer}"  # serverless or loadbalancer
TAG="${2:-latest}"
PUSH="${3}"
IMAGE_NAME="${DOCKER_USERNAME:-your-docker-username}/infinity-${TYPE}"

if [[ "$TYPE" != "serverless" && "$TYPE" != "loadbalancer" ]]; then
  echo "Error: TYPE must be 'serverless' or 'loadbalancer'"
  echo "Usage: ./build.sh [serverless|loadbalancer] [tag] [push]"
  exit 1
fi

# Select Dockerfile
if [ "$TYPE" == "loadbalancer" ]; then
  DOCKERFILE="Dockerfile.loadbalancer"
else
  DOCKERFILE="Dockerfile"
fi

echo "Building Docker image: ${IMAGE_NAME}:${TAG}"
echo "Using Dockerfile: ${DOCKERFILE}"
echo "=========================================="

# Build for linux/amd64 (required for RunPod)
docker build \
  --platform linux/amd64 \
  -f "${DOCKERFILE}" \
  -t "${IMAGE_NAME}:${TAG}" \
  .

echo ""
echo "Build completed: ${IMAGE_NAME}:${TAG}"

# Push if requested
if [ "$PUSH" == "push" ]; then
  echo ""
  echo "Pushing to Docker Hub..."
  docker push "${IMAGE_NAME}:${TAG}"
  echo "Push completed!"
fi

echo ""
echo "=========================================="
echo "To run locally:"
if [ "$TYPE" == "loadbalancer" ]; then
  echo "  docker-compose up infinity-loadbalancer"
else
  echo "  docker-compose up infinity-serverless"
fi
echo ""
echo "To deploy to RunPod:"
echo "  1. Push the image: ./scripts/build.sh ${TYPE} ${TAG} push"
echo "  2. Create endpoint with image: ${IMAGE_NAME}:${TAG}"
if [ "$TYPE" == "loadbalancer" ]; then
  echo "  3. Select 'Load Balancer' as endpoint type"
else
  echo "  3. Select 'Serverless' as endpoint type"
fi
echo "=========================================="
