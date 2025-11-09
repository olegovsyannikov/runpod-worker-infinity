![Infinity Embedding Worker Banner](https://cpjrphpz3t5wbwfe.public.blob.vercel-storage.com/worker-infinity-embedding_banner-9n86vTARpwknMZYnXHAUr7xJisiWXs.jpeg)

---

High-throughput, OpenAI-compatible text embedding & reranker powered by [Infinity](https://github.com/michaelfeil/infinity)

**Two Deployment Options**: Serverless Worker or Load Balancing Endpoint

---

[![RunPod](https://api.runpod.io/badge/runpod-workers/worker-infinity-embedding)](https://www.runpod.io/console/hub/runpod-workers/worker-infinity-embedding)

---

## Table of Contents

1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [Quickstart](#quickstart)
4. [Configuration](#configuration)
5. [API Documentation](#api-documentation)
6. [Local Development](#local-development)
7. [Further Documentation](#further-documentation)
8. [Acknowledgements](#acknowledgements)

---

## Overview

This project provides high-performance text embeddings and document reranking using the Infinity engine. It can be deployed in two ways:

### 🔹 Serverless Worker (Traditional)

- **Use case**: Batch processing, job queues, asynchronous workflows
- **API style**: RunPod job-based (`/run`, `/runsync`)
- **Best for**: High-throughput batch embeddings, cost optimization with auto-scaling

### 🔹 Load Balancing Endpoint (Modern)

- **Use case**: Real-time API, direct integration, OpenAI drop-in replacement
- **API style**: Direct REST API (`/v1/embeddings`, `/v1/rerank`)
- **Best for**: Real-time applications, low-latency requirements, OpenAI SDK compatibility

---

## Deployment Options

### Option 1: Serverless Worker

Traditional RunPod serverless endpoint with job-based processing.

**Features:**

- ✅ Job queue with `/run` and `/runsync` endpoints
- ✅ OpenAI-compatible via `/openai/v1/*` wrapper
- ✅ Auto-scaling based on queue depth
- ✅ Cost-effective for batch processing

**When to use:**

- Processing large batches of documents
- Async workflows with job tracking
- Cost optimization with auto-scaling
- Existing RunPod serverless integrations

**API Endpoints:**

```bash
POST https://api.runpod.ai/v2/<ENDPOINT_ID>/run
POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
POST https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings
GET  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/models
```

### Option 2: Load Balancing Endpoint

Modern REST API with direct endpoints and health checks.

**Features:**

- ✅ Direct REST API endpoints (no job wrapper)
- ✅ Native OpenAI compatibility
- ✅ `/ping` health check for automatic worker management
- ✅ Lower latency (no job queue overhead)
- ✅ Works with OpenAI Python SDK

**When to use:**

- Real-time applications requiring low latency
- Drop-in replacement for OpenAI embeddings API
- Direct API integration without job polling
- Applications using OpenAI SDK

**API Endpoints:**

```bash
GET  https://<ENDPOINT_ID>.api.runpod.ai/ping
GET  https://<ENDPOINT_ID>.api.runpod.ai/v1/models
POST https://<ENDPOINT_ID>.api.runpod.ai/v1/embeddings
POST https://<ENDPOINT_ID>.api.runpod.ai/v1/rerank
POST https://<ENDPOINT_ID>.api.runpod.ai/v1/score
GET  https://<ENDPOINT_ID>.api.runpod.ai/stats
```

---

## Quickstart

### 1. Choose Your Deployment Type

```bash
# For Serverless Worker
export DEPLOYMENT_TYPE=serverless

# For Load Balancing Endpoint
export DEPLOYMENT_TYPE=loadbalancer
```

### 2. Build Docker Image

```bash
export DOCKER_USERNAME=your-docker-username
./scripts/build.sh $DEPLOYMENT_TYPE v1.0.0 push
```

### 3. Deploy to RunPod

#### Serverless Worker

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint** → **Import from Docker Registry**
3. Enter image: `your-docker-username/infinity-serverless:v1.0.0`
4. Select **Endpoint Type**: **Serverless**
5. Set environment variable: `MODEL_NAMES=BAAI/bge-small-en-v1.5`
6. Deploy and use via `/run` or `/runsync`

#### Load Balancing Endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint** → **Import from Docker Registry**
3. Enter image: `your-docker-username/infinity-loadbalancer:v1.0.0`
4. Select **Endpoint Type**: **Load Balancer** ⚠️ Important!
5. Set environment variable: `MODEL_NAMES=BAAI/bge-small-en-v1.5`
6. Deploy and use direct API endpoints

---

## Configuration

All configuration is via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODEL_NAMES` | **Yes** | — | Semicolon-separated HuggingFace model IDs<br>Example: `BAAI/bge-small-en-v1.5;BAAI/bge-reranker-large` |
| `BATCH_SIZES` | No | `32` | Per-model batch sizes (semicolon-separated) |
| `BACKEND` | No | `torch` | Inference engine: `torch`, `optimum`, `ctranslate2` |
| `DTYPES` | No | `auto` | Data types per model: `auto`, `fp16`, `fp8` |
| `INFINITY_QUEUE_SIZE` | No | `48000` | Max items in Infinity queue |
| `RUNPOD_MAX_CONCURRENCY` | No | `300` | Max concurrent requests |
| `PORT` | No | `80` | Port for load balancer (load balancing only) |

**Example configurations:**

```bash
# Single embedding model
MODEL_NAMES=BAAI/bge-small-en-v1.5

# Embedding + reranker
MODEL_NAMES=BAAI/bge-small-en-v1.5;BAAI/bge-reranker-large
BATCH_SIZES=32;16

# Multiple embeddings with different dtypes
MODEL_NAMES=BAAI/bge-small-en-v1.5;BAAI/bge-large-en-v1.5
DTYPES=fp16;fp8
```

---

## API Documentation

### Serverless Worker API

#### Embeddings via `/runsync`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "model": "BAAI/bge-small-en-v1.5",
      "input": "Hello world"
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

#### OpenAI-compatible (via wrapper)

```bash
curl -X POST \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world"}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings
```

#### Reranking

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "model": "BAAI/bge-reranker-large",
      "query": "Which product has warranty?",
      "docs": ["Product A has 2-year warranty", "Product B is red"],
      "return_docs": true
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

### Load Balancing API

#### Health Check

```bash
curl https://<ENDPOINT_ID>.api.runpod.ai/ping
```

Response:

```json
{"status": "healthy"}
```

#### List Models

```bash
curl -H "Authorization: Bearer <RUNPOD_API_KEY>" \
     https://<ENDPOINT_ID>.api.runpod.ai/v1/models
```

#### Create Embeddings

```bash
curl -X POST \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world"}' \
  https://<ENDPOINT_ID>.api.runpod.ai/v1/embeddings
```

With multiple inputs:

```bash
curl -X POST \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":["Text 1","Text 2"]}' \
  https://<ENDPOINT_ID>.api.runpod.ai/v1/embeddings
```

#### Rerank Documents

```bash
curl -X POST \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "BAAI/bge-reranker-large",
    "query": "Which product has warranty?",
    "docs": ["Product A has 2-year warranty", "Product B is red"],
    "return_docs": true
  }' \
  https://<ENDPOINT_ID>.api.runpod.ai/v1/rerank
```

#### Using OpenAI SDK (Load Balancing Only)

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-runpod-api-key",
    base_url="https://your-endpoint-id.api.runpod.ai/v1"
)

response = client.embeddings.create(
    model="BAAI/bge-small-en-v1.5",
    input="Hello world"
)
```

---

## Local Development

### Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### Run Serverless Worker

```bash
docker-compose up infinity-serverless
```

Test at `http://localhost:8000`

### Run Load Balancing Endpoint

```bash
docker-compose up infinity-loadbalancer
```

Test at `http://localhost:8080`:

```bash
./scripts/test_local.sh loadbalancer
```

### Run Both

```bash
docker-compose up
```

- Serverless: `http://localhost:8000`
- Load Balancing: `http://localhost:8080`

---

## Comparison Table

| Feature | Serverless Worker | Load Balancing Endpoint |
|---------|------------------|------------------------|
| **API Style** | Job-based (`/run`, `/runsync`) | REST API (`/v1/*`) |
| **Latency** | Higher (job queue overhead) | Lower (direct) |
| **OpenAI Compatible** | Via `/openai/v1/*` wrapper | Native `/v1/*` |
| **Health Checks** | Optional | Required (`/ping`) |
| **Use OpenAI SDK** | No | Yes |
| **Job Tracking** | Yes (job IDs) | No |
| **Best For** | Batch processing | Real-time API |
| **Auto-scaling** | Queue-based | Load-based |
| **Cost** | Pay per second of execution | Pay per second workers run |

---

## Model Recommendations

### Embedding Models

| Model | Size | Dimensions | Use Case |
|-------|------|------------|----------|
| `BAAI/bge-small-en-v1.5` | 130MB | 384 | Fast, general-purpose |
| `BAAI/bge-base-en-v1.5` | 440MB | 768 | Balanced quality/speed |
| `BAAI/bge-large-en-v1.5` | 1.3GB | 1024 | Highest quality |
| `sentence-transformers/all-MiniLM-L6-v2` | 90MB | 384 | Very fast |

### Reranker Models

| Model | Size | Use Case |
|-------|------|----------|
| `BAAI/bge-reranker-base` | 440MB | General reranking |
| `BAAI/bge-reranker-large` | 1.3GB | High-quality reranking |

---

## Further Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide for both options
- **[Infinity Engine](https://github.com/michaelfeil/infinity)** - High-performance backend
- **[RunPod Docs](https://docs.runpod.io/)** - Platform documentation
- **[RunPod Load Balancing Guide](https://docs.runpod.io/serverless/load-balancing/build-a-worker)** - Load balancing details

---

## Troubleshooting

### Serverless Worker

- **Jobs timeout**: Increase timeout in endpoint settings
- **Queue depth high**: Scale up max workers
- **Cold starts**: Use min workers > 0

### Load Balancing

- **Workers not starting**: Check endpoint type is "Load Balancer"
- **Health check failing**: Verify `/ping` returns `{"status": "healthy"}`
- **404 errors**: Ensure endpoint type is Load Balancer, not Serverless

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting.

---

## Acknowledgements

Special thanks to [Michael Feil](https://github.com/michaelfeil) for creating the Infinity engine and for his ongoing support of this project.

---

## License

See [LICENSE](LICENSE) file for details.
