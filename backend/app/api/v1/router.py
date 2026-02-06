"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import health, auth, chat, tasks, brain, personality, proactive


router = APIRouter()

# Include all v1 sub-routers
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
router.include_router(brain.router, prefix="/brain", tags=["Brain"])
router.include_router(personality.router, prefix="/personality", tags=["Personality"])
router.include_router(proactive.router, prefix="/proactive", tags=["Proactive"])
