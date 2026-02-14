"""Main FastAPI application entry point."""

import asyncio
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

    # Initialize Graphiti knowledge graph
    if settings.graphiti_enabled:
        from app.services.graphiti_client import GraphitiClient
        import app.services.graphiti_client as gc_module

        client = GraphitiClient(
            uri=settings.falkordb_uri,
            enabled=True,
        )
        await client.initialize()
        gc_module.graphiti_client = client
        print("Graphiti knowledge graph initialized")
    else:
        import app.services.graphiti_client as gc_module
        gc_module.graphiti_client = GraphitiClient(enabled=False)
        print("Graphiti knowledge graph disabled")

    # Start background scheduler (skip in test environment)
    scheduler_task = None
    if settings.app_env != "test":
        from app.services.scheduler import run_scheduler
        scheduler_task = asyncio.create_task(run_scheduler())
        print("Background scheduler started")

    yield

    # Shutdown
    print("Shutting down...")

    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        print("Background scheduler stopped")

    # Close Graphiti
    import app.services.graphiti_client as gc_module
    if gc_module.graphiti_client:
        await gc_module.graphiti_client.close()
        print("Graphiti connection closed")

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
