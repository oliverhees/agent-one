"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    health,
    auth,
    chat,
    tasks,
    brain,
    personality,
    proactive,
    gamification,
    task_breakdown,
    nudges,
    dashboard,
    settings,
    voice,
    voice_live,
)


router = APIRouter()

# Include all v1 sub-routers
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
router.include_router(brain.router, prefix="/brain", tags=["Brain"])
router.include_router(personality.router, prefix="/personality", tags=["Personality"])
router.include_router(proactive.router, prefix="/proactive", tags=["Proactive"])

# Phase 3: ADHS-Modus routers
router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
router.include_router(task_breakdown.router, prefix="/tasks", tags=["Task Breakdown"])
router.include_router(nudges.router, prefix="/nudges", tags=["Nudges"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# Phase 4: Voice routers
router.include_router(voice.router, prefix="/voice", tags=["Voice"])
router.include_router(voice_live.router, prefix="/voice", tags=["Voice Live"])
