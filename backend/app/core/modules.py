"""Module definitions for the ALICE modular coaching platform.

All module metadata lives here. The 'core' module is always active and cannot
be deactivated. Each module has a name, display label (German), icon name,
description, and default config dict.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

ALL_MODULES: dict[str, dict[str, Any]] = {
    "core": {
        "label": "Kern-Funktionen",
        "icon": "chatbubble-outline",
        "description": "Chat mit Alice, Aufgaben, Brain, Persoenlichkeit",
        "default_config": {},
    },
    "adhs": {
        "label": "ADHS-Coaching",
        "icon": "bulb-outline",
        "description": (
            "Pattern-Erkennung, Nudges, Task-Breakdown, Gamification und Focus-Timer"
        ),
        "default_config": {
            "nudge_intensity": "medium",
            "auto_breakdown": True,
            "pattern_tracking": True,
        },
    },
    "wellness": {
        "label": "Wellness & Guardian Angel",
        "icon": "heart-outline",
        "description": (
            "Wellbeing-Score, Energie-Tracking, Schlafmuster-Analyse "
            "und proaktive Interventionen"
        ),
        "default_config": {
            "guardian_angel_enabled": True,
            "wellbeing_check_interval_hours": 4,
        },
    },
    "productivity": {
        "label": "Produktivitaet & Planung",
        "icon": "calendar-outline",
        "description": (
            "Morning Briefing, adaptive Tagesplanung, Energie-basierte Priorisierung"
        ),
        "default_config": {
            "morning_briefing": True,
            "briefing_time": "07:00",
            "max_daily_tasks": 3,
        },
    },
}

# ---------------------------------------------------------------------------
# Derived constants
# ---------------------------------------------------------------------------

ALWAYS_ACTIVE_MODULES: frozenset[str] = frozenset({"core"})
"""Modules that cannot be deactivated."""

DEFAULT_ACTIVE_MODULES: list[str] = ["core", "adhs"]
"""Modules enabled by default for new users."""

VALID_MODULE_NAMES: frozenset[str] = frozenset(ALL_MODULES.keys())
"""Set of all recognised module names."""
