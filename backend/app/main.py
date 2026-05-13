"""FastAPI entrypoint for the AI Conversational Commerce backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.chroma import init_chroma
from app.db.mongodb import close_mongo, connect_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    init_chroma()
    yield
    await close_mongo()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Conversational Commerce API",
        version="1.0.0",
        description=(
            "Backend for an AI-first shopping experience: semantic search, "
            "conversational assistant, recommendations, cart, and conversation memory."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok", "env": settings.APP_ENV}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
