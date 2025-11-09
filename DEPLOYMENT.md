# Deployment Guide: Load Balancing Endpoint

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your model configuration:

```bash
MODEL_NAMES=BAAI/bge-small-en-v1.5
BATCH_SIZES=32
BACKEND=torch
```

For multiple models (embedding + reranker):

```bash
MODEL_NAMES=BAAI/bge-small-en-v1.5;BAAI/bge-reranker-large
BATCH_SIZES=32;16
DTYPES=auto;auto
```

### 2. Local Testing

Start the service locally:

```bash
docker-compose up --build
```

Test the endpoints:

```bash
./test_local.sh
```

Or manually:

```bash
# Health check
curl http://localhost:8080/ping

# List models
curl http://localhost:8080/v1/models

# Create embeddings
curl -X POST http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world"}'
```

### 3. Build and Push to Docker Hub

Set your Docker Hub username:

```bash
export DOCKER_USERNAME=your-docker-username
```

Build and push:

```bash
./build.sh v1.0.0 push
```

Or manually:

```bash
docker build --platform linux/amd64 -t $DOCKER_USERNAME/infinity-loadbalancer:v1.0.0 .
docker push $DOCKER_USERNAME/infinity-loadbalancer:v1.0.0
```

### 4. Deploy to RunPod

#### Option A: Web Console

1. Go to <https://www.runpod.io/console/serverless>
2. Click **New Endpoint**
3. Click **Import from Docker Registry**
4. Enter image: `your-docker-username/infinity-loadbalancer:v1.0.0`
5. Click **Next**
6. Configure:
   - **Name**: `infinity-embeddings`
   - **Endpoint Type**: **Load Balancer** (Important!)
   - **GPU Type**: Select 16GB or 24GB GPU
   - **Max Workers**: Start with 1-3
7. Add environment variables:
   - `MODEL_NAMES`: `BAAI/bge-small-en-v1.5`
   - `BATCH_SIZES`: `32`
   - `BACKEND`: `torch`
8. Click **Create Endpoint**

#### Option B: RunPod CLI

```bash
# Install RunPod CLI
pip install runpod

# Create endpoint
runpod create endpoint \
  --name infinity-embeddings \
  --image your-docker-username/infinity-loadbalancer:v1.0.0 \
  --type load-balancer \
  --gpu-type "NVIDIA RTX A4000" \
  --env MODEL_NAMES=BAAI/bge-small-en-v1.5 \
  --env BATCH_SIZES=32 \
  --env BACKEND=torch
```

### 5. Wait for Workers to Initialize

Monitor the **Workers** tab in RunPod console. Workers will:

1. Pull the Docker image (2-3 minutes)
2. Start containers (30 seconds)
3. Download models from Hugging Face (1-5 minutes depending on model size)
4. Initialize Infinity engine (30 seconds)
5. Pass health check (immediately after initialization)

Total time: 5-10 minutes for first deployment.

### 6. Test Your Endpoint

Get your endpoint ID from the RunPod console, then test:

```bash
export ENDPOINT_ID=your-endpoint-id
export RUNPOD_API_KEY=your-api-key

# Health check
curl https://${ENDPOINT_ID}.api.runpod.ai/ping

# List models
curl -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
     https://${ENDPOINT_ID}.api.runpod.ai/v1/models

# Create embeddings
curl -X POST \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world"}' \
  https://${ENDPOINT_ID}.api.runpod.ai/v1/embeddings
```

---

## Model Selection

### Recommended Embedding Models

| Model | Size | Dimension | Use Case |
|-------|------|-----------|----------|
| `BAAI/bge-small-en-v1.5` | 130MB | 384 | Fast, general-purpose |
| `BAAI/bge-base-en-v1.5` | 440MB | 768 | Balanced performance |
| `BAAI/bge-large-en-v1.5` | 1.3GB | 1024 | High quality |
| `sentence-transformers/all-MiniLM-L6-v2` | 90MB | 384 | Very fast |

### Recommended Reranker Models

| Model | Size | Use Case |
|-------|------|----------|
| `BAAI/bge-reranker-base` | 440MB | General reranking |
| `BAAI/bge-reranker-large` | 1.3GB | High-quality reranking |

### Multi-Model Configuration

Deploy both embedding and reranking:

```bash
MODEL_NAMES=BAAI/bge-small-en-v1.5;BAAI/bge-reranker-base
BATCH_SIZES=32;16
DTYPES=auto;auto
```

---

## GPU Selection

### Minimum Requirements

| Model Size | Min VRAM | Recommended GPU |
|------------|----------|-----------------|
| Small (< 500MB) | 4GB | RTX 4000 (16GB) |
| Base (< 1GB) | 6GB | RTX 4000 (16GB) |
| Large (1-2GB) | 8GB | RTX A4000 (16GB) |
| Multi-model | 12GB | RTX A5000 (24GB) |

### RunPod GPU Options

- **RTX A4000** (16GB) - Good for single models
- **RTX A5000** (24GB) - Good for multiple models
- **RTX A6000** (48GB) - Overkill for most use cases
- **A40** (48GB) - Overkill for most use cases

---

## Scaling Configuration

### Auto-scaling Settings

Configure in RunPod console:

- **Min Workers**: 1 (always have one ready)
- **Max Workers**: 5-10 (depending on expected load)
- **Idle Timeout**: 30 seconds (how long to wait before scaling down)
- **Scale Up Threshold**: 80% (scale up when 80% of workers are busy)

### Batch Size Tuning

Larger batch sizes = higher throughput but more VRAM usage:

| GPU VRAM | Recommended Batch Size |
|----------|----------------------|
| 16GB | 32 |
| 24GB | 64 |
| 48GB | 128 |

---

## Monitoring

### Health Check

The `/ping` endpoint is used by RunPod to monitor worker health:

- Returns `{"status": "healthy"}` when ready
- Workers not passing health checks are automatically restarted
- Health checks run every 10 seconds

### Logs

View logs in RunPod console:

1. Go to your endpoint
2. Click **Workers** tab
3. Click on a worker
4. View **Logs**

Look for:

```
INFO - Starting embedding service...
INFO - Embedding service started successfully. Available models: ['BAAI/bge-small-en-v1.5']
INFO - Uvicorn running on http://0.0.0.0:80
```

### Stats Endpoint

Check service status:

```bash
curl https://${ENDPOINT_ID}.api.runpod.ai/stats
```

Returns:

```json
{
  "models": ["BAAI/bge-small-en-v1.5"],
  "is_running": true,
  "status": "ready"
}
```

---

## Troubleshooting

### Workers Not Starting

**Symptom**: Workers show as "Initializing" for a long time

**Solutions**:

1. Check logs for errors
2. Verify `MODEL_NAMES` is correct
3. Ensure GPU has enough VRAM
4. Try a smaller model

### Health Check Failing

**Symptom**: Workers restart repeatedly

**Solutions**:

1. Check logs for Python errors
2. Verify models downloaded successfully
3. Ensure port 80 is exposed
4. Check Infinity engine initialization

### API Returns 404

**Symptom**: Endpoints return "Not Found"

**Solutions**:

1. Verify endpoint URL format: `https://ENDPOINT_ID.api.runpod.ai/v1/embeddings`
2. Check endpoint type is "Load Balancer"
3. Ensure workers passed health checks

### Model Not Found

**Symptom**: API returns "Model 'X' not found"

**Solutions**:

1. Check `MODEL_NAMES` environment variable
2. Verify model name in request matches deployed model
3. Check logs to see which models loaded

### Slow Responses

**Symptom**: API takes a long time to respond

**Solutions**:

1. Check if workers are still initializing
2. Increase `BATCH_SIZES` for higher throughput
3. Add more workers for parallel processing
4. Use a smaller/faster model

### Out of Memory

**Symptom**: Workers crash with OOM errors

**Solutions**:

1. Reduce `BATCH_SIZES`
2. Use a smaller model
3. Switch to larger GPU
4. Reduce number of models

---

## Cost Optimization

### Tips

1. **Use Spot Instances**: 50-70% cheaper, may be interrupted
2. **Start Small**: Begin with 1-2 workers, scale up as needed
3. **Idle Timeout**: Set appropriate timeout to scale down unused workers
4. **Right-size GPU**: Don't use 48GB GPU for small models
5. **Batch Processing**: Send multiple inputs in one request

### Estimated Costs

RunPod pricing varies, but typical rates:

- **RTX A4000 (16GB)**: $0.20-0.30/hour
- **RTX A5000 (24GB)**: $0.30-0.40/hour
- **Spot instances**: 50-70% discount

Example monthly cost (1 worker, 24/7):

- On-demand: $150-250/month
- Spot: $75-125/month

---

## Updates and Maintenance

### Updating Models

1. Update `MODEL_NAMES` environment variable
2. Restart workers (or they'll restart automatically)
3. Wait for new models to download

### Updating Code

1. Make changes to `src/app.py`
2. Build new Docker image with new version tag
3. Update endpoint to use new image
4. Workers will restart with new code

### Rollback

1. Go to endpoint settings
2. Change Docker image to previous version
3. Workers will restart with old code

---

## Integration Examples

### Python

```python
import requests

ENDPOINT_ID = "your-endpoint-id"
API_KEY = "your-api-key"
BASE_URL = f"https://{ENDPOINT_ID}.api.runpod.ai"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Create embeddings
response = requests.post(
    f"{BASE_URL}/v1/embeddings",
    headers=headers,
    json={
        "model": "BAAI/bge-small-en-v1.5",
        "input": "Hello world"
    }
)
embeddings = response.json()
```

### JavaScript/TypeScript

```typescript
const ENDPOINT_ID = "your-endpoint-id";
const API_KEY = "your-api-key";
const BASE_URL = `https://${ENDPOINT_ID}.api.runpod.ai`;

const response = await fetch(`${BASE_URL}/v1/embeddings`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "BAAI/bge-small-en-v1.5",
    input: "Hello world"
  })
});

const embeddings = await response.json();
```

### OpenAI SDK

Since the API is OpenAI-compatible, you can use the OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-runpod-api-key",
    base_url=f"https://your-endpoint-id.api.runpod.ai/v1"
)

response = client.embeddings.create(
    model="BAAI/bge-small-en-v1.5",
    input="Hello world"
)
```

---

## Security

### API Key Management

- **Never commit API keys** to version control
- Use environment variables or secrets management
- Rotate keys periodically
- Use different keys for dev/staging/prod

### Network Security

- All traffic is over HTTPS
- RunPod handles TLS termination
- API keys required for all requests (except `/ping`)

### Model Security

- Models downloaded from Hugging Face
- Verify model sources before deployment
- Consider hosting your own model registry

---

## Support

- **RunPod Docs**: <https://docs.runpod.io/>
- **Infinity GitHub**: <https://github.com/michaelfeil/infinity>
- **Issues**: Open an issue in the repository

---

## License

See LICENSE file for details.
