import os
import logging
from typing import List, Union
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from embedding_service import EmbeddingService
from utils import (
    OpenAIEmbeddingInput,
    OpenAIEmbeddingResult,
    OpenAIModelInfo,
    ModelInfo,
    create_error_response,
    list_embeddings_to_response,
    to_rerank_response,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Infinity Embedding & Rerank API",
    description="OpenAI-compatible embedding and rerank API powered by Infinity",
    version="1.0.0"
)

# Initialize embedding service
try:
    embedding_service = EmbeddingService()
    logger.info("Embedding service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize embedding service: {e}")
    raise


# Request/Response models for rerank
class RerankRequest(BaseModel):
    model: str = Field(..., description="Model name to use for reranking")
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., description="List of documents to rerank", alias="docs")
    return_documents: bool = Field(False, description="Whether to return the documents in the response", alias="return_docs")

    class Config:
        populate_by_name = True


class RerankResultItem(BaseModel):
    index: int
    relevance_score: float
    document: Union[str, None] = None


class RerankResponse(BaseModel):
    model: str
    results: List[RerankResultItem]
    usage: dict


# Health check endpoint - required for RunPod load balancing
@app.get("/ping")
async def health_check():
    """Health check endpoint required by RunPod load balancing."""
    return {"status": "healthy"}


# OpenAI-compatible endpoints
@app.get("/v1/models")
async def list_models():
    """List all available models (OpenAI-compatible)."""
    try:
        result = await embedding_service.route_openai_models()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        error_response = create_error_response(str(e))
        raise HTTPException(status_code=error_response.code, detail=error_response.model_dump())


@app.post("/v1/embeddings", response_model=OpenAIEmbeddingResult)
async def create_embeddings(request: OpenAIEmbeddingInput):
    """Create embeddings for the input text (OpenAI-compatible)."""
    try:
        if not request.model:
            raise HTTPException(status_code=400, detail="Model name is required")

        result = await embedding_service.route_openai_get_embeddings(
            embedding_input=request.input,
            model_name=request.model,
            return_as_list=False,
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        error_response = create_error_response(str(e))
        raise HTTPException(status_code=error_response.code, detail=error_response.model_dump())


@app.post("/v1/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """Rerank documents based on query relevance."""
    try:
        result = await embedding_service.infinity_rerank(
            query=request.query,
            docs=request.documents,
            return_docs=request.return_documents,
            model_name=request.model,
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error reranking documents: {e}")
        error_response = create_error_response(str(e))
        raise HTTPException(status_code=error_response.code, detail=error_response.model_dump())


# Alternative endpoint name for rerank (score)
@app.post("/v1/score", response_model=RerankResponse)
async def score_documents(request: RerankRequest):
    """Score documents based on query relevance (alias for rerank)."""
    return await rerank_documents(request)


# Stats endpoint for monitoring
@app.get("/stats")
async def get_stats():
    """Get service statistics."""
    return {
        "models": embedding_service.list_models(),
        "is_running": embedding_service.is_running,
        "status": "ready" if embedding_service.is_running else "initializing"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Start the embedding service on application startup."""
    logger.info("Starting embedding service...")
    try:
        await embedding_service.start()
        logger.info(f"Embedding service started successfully. Available models: {embedding_service.list_models()}")
    except Exception as e:
        logger.error(f"Failed to start embedding service: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the embedding service on application shutdown."""
    logger.info("Stopping embedding service...")
    try:
        await embedding_service.stop()
        logger.info("Embedding service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping embedding service: {e}")


# Run the application
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 80))
    logger.info(f"Starting FastAPI server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
