"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import health, auth, chat


router = APIRouter()

# Include all v1 sub-routers
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
