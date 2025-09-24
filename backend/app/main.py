"""
RocketTrainer FastAPI application main module.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.api import auth, users, replays, training, health


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting RocketTrainer API", environment=settings.environment)
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down RocketTrainer API")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="RocketTrainer API",
    description="AI-powered Rocket League coaching platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.rockettrainer.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(replays.router, prefix="/replays", tags=["replays"])
app.include_router(training.router, prefix="/training", tags=["training"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RocketTrainer API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation not available in production"
    }
