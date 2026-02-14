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
    memory,
    wellbeing,
    briefing,
    prediction,
    calendar,
    reminders,
    webhooks,
    n8n,
    agents,
    agent_stream,
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

# Phase 5: Memory/Knowledge Graph routers
router.include_router(memory.router, prefix="/memory", tags=["Memory"])

# Phase 7: Wellbeing/Guardian Angel routers
router.include_router(wellbeing.router, prefix="/wellbeing", tags=["Wellbeing"])

# Phase 8: Morning Briefing routers
router.include_router(briefing.router, prefix="/briefing", tags=["Briefing"])

# Phase 9: Prediction Pattern Engine routers
router.include_router(prediction.router, prefix="/predictions", tags=["Predictions"])

# Phase 10: Essential Integrations routers
router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(n8n.router, prefix="/n8n", tags=["n8n"])

# Phase 11: Multi-Agent System routers
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(agent_stream.router, prefix="/agents", tags=["Agent Stream"])
