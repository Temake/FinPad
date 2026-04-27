from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.redis import init_redis, close_redis
from app.api.router import api_router
from app.services.expense_service import ensure_default_categories

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    await init_redis(settings.REDIS_URL)
    async with async_session_factory() as session:
        await ensure_default_categories(session)
        await session.commit()
    yield
    # Shutdown
    await close_redis()
    print(f"👋 Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal Finance Tracker with WhatsApp Integration",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
