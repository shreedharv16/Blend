"""Main FastAPI application."""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from app.api.routes import upload, chat, dashboard
from app.api.websockets.chat_ws import handle_websocket
from app.services.data_service import data_service
from app.services.cache_service import cache_service
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)

# Initialize LangSmith tracing
def setup_langsmith():
    """Configure LangSmith tracing for LangChain/LangGraph."""
    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        logger.info(f"✓ LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")
    else:
        logger.warning("LangSmith API key not found - tracing disabled")

# Set up LangSmith before creating the app
setup_langsmith()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management."""
    logger.info("Starting Retail Insights Assistant API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("Shutting down Retail Insights Assistant API")
    # Cleanup
    data_service.close()
    cache_service.cleanup_expired()


# Create FastAPI app
app = FastAPI(
    title="Retail Insights Assistant API",
    description="GenAI-powered retail analytics with multi-agent workflow",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(dashboard.router)


# WebSocket endpoint
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await handle_websocket(websocket)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "model": settings.GEMINI_MODEL,
        "langsmith_enabled": bool(settings.LANGCHAIN_API_KEY),
        "langsmith_project": settings.LANGCHAIN_PROJECT if settings.LANGCHAIN_API_KEY else None
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Retail Insights Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

