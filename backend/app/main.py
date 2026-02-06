"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    print(f"Starting {settings.app_name} API v{__version__}...")
    print(f"Environment: {settings.app_env}")
    print(f"Debug mode: {settings.debug}")

    # Initialize database connection
    await init_db()
    print("Database connection initialized")

    yield

    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=f"{settings.app_name} API",
    description="Proactive Personal Assistant with ADHD Focus",
    version=__version__,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(
    v1_router,
    prefix="/api/v1",
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "running",
        "docs": "/docs",
    }
