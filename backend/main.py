import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from backend.api.websocket import router as websocket_router
from backend.config import settings
from backend.core.session_manager import session_manager
from backend.services.knowledge import get_knowledge_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup and graceful shutdown."""
    logger.info("Starting Gemini Real-Time Voice Agent Backend...")
    logger.info("Model: %s | Voice: %s | API Key Configured: %s",
                settings.gemini_model, settings.voice_name, settings.has_api_key)
    logger.info("Allowed CORS Origins: %s", settings.cors_origins)
    yield
    logger.info("Shutting down backend and terminating all active sessions...")
    await session_manager.cleanup_all()
    logger.info("All sessions terminated cleanly.")


app = FastAPI(
    title="Gemini Real-Time Voice Agent API",
    version="1.0.0",
    description="Real-time voice and text conversational agent powered by Gemini Live API",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach WebSocket router
app.include_router(websocket_router)


# --- REST Endpoints ---

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model: str
    voice: str
    has_api_key: bool
    active_sessions: int
    audio_input_rate: int
    audio_output_rate: int


class AddDocumentRequest(BaseModel):
    title: str
    content: str
    source: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint exposing runtime diagnostics and model readiness."""
    active_count = len(session_manager._sessions)
    return HealthResponse(
        status="healthy",
        uptime_seconds=round(time.time() - start_time, 2),
        model=settings.gemini_model,
        voice=settings.voice_name,
        has_api_key=settings.has_api_key,
        active_sessions=active_count,
        audio_input_rate=settings.input_sample_rate,
        audio_output_rate=settings.output_sample_rate
    )


@app.post("/api/knowledge")
async def add_knowledge_doc(doc: AddDocumentRequest):
    """
    Extension point: dynamically inject website FAQs or documents
    into the knowledge store without restarting the application.
    """
    knowledge = get_knowledge_provider()
    await knowledge.add_document(title=doc.title, content=doc.content, source=doc.source)
    return {"status": "success", "message": f"Document '{doc.title}' added to knowledge store"}


@app.get("/api/knowledge")
async def get_knowledge_overview():
    """Return overview of currently registered knowledge documents."""
    knowledge = get_knowledge_provider()
    docs = getattr(knowledge, "_documents", [])
    return {
        "count": len(docs),
        "documents": [{"title": d.title, "source": d.source, "excerpt": d.content[:100]} for d in docs]
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
