# Phase 6: Module System & Rebranding — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Alice from a hardcoded ADHS-only app into a modular coaching platform where users choose which modules (adhs, wellness, productivity) are active, and the UI dynamically adapts.

**Architecture:** Feature-flag-based module system stored in existing `UserSettings.settings` JSONB. New keys `active_modules` (list of strings) and `module_configs` (dict of per-module config). Backend exposes `GET/PUT /settings/modules` endpoints. Expo tab-bar renders dynamically based on active modules. Onboarding adds a module-selection step.

**Tech Stack:** Python/FastAPI (backend), Pydantic v2 (schemas), SQLAlchemy async (ORM), Expo Router (mobile), TypeScript/React Native (mobile UI)

**Linear Epics:**
- HR-455: Module System Backend
- HR-456: Module Selection Onboarding
- HR-457: Dynamic Tab-Bar & Module-aware UI
- HR-458: Documentation Update

---

### Task 1: Module Constants & Pydantic Schemas (Backend)

**Files:**
- Create: `backend/app/core/modules.py`
- Create: `backend/app/schemas/modules.py`
- Test: `backend/tests/test_modules.py`

**Context:** All module definitions live in one place. The `core` module is always active and cannot be deactivated. Each module has a name, display label (German), icon name, description, and default config dict.

**Step 1: Write the failing test**

```python
# backend/tests/test_modules.py
"""Module system unit tests."""

import pytest
from pydantic import ValidationError


class TestModuleDefinitions:
    """Tests for module constants and registry."""

    def test_all_modules_defined(self):
        from app.core.modules import ALL_MODULES
        assert "core" in ALL_MODULES
        assert "adhs" in ALL_MODULES
        assert "wellness" in ALL_MODULES
        assert "productivity" in ALL_MODULES

    def test_core_module_is_always_active(self):
        from app.core.modules import ALWAYS_ACTIVE_MODULES
        assert "core" in ALWAYS_ACTIVE_MODULES

    def test_module_has_required_fields(self):
        from app.core.modules import ALL_MODULES
        for name, module in ALL_MODULES.items():
            assert "label" in module, f"Module '{name}' missing 'label'"
            assert "icon" in module, f"Module '{name}' missing 'icon'"
            assert "description" in module, f"Module '{name}' missing 'description'"
            assert "default_config" in module, f"Module '{name}' missing 'default_config'"

    def test_default_active_modules(self):
        from app.core.modules import DEFAULT_ACTIVE_MODULES
        assert "core" in DEFAULT_ACTIVE_MODULES
        assert "adhs" in DEFAULT_ACTIVE_MODULES


class TestModuleSchemas:
    """Tests for module Pydantic schemas."""

    def test_module_info_response(self):
        from app.schemas.modules import ModuleInfoResponse
        info = ModuleInfoResponse(
            name="adhs",
            label="ADHS-Coaching",
            icon="bulb-outline",
            description="Pattern-Erkennung und Nudges",
            active=True,
            config={"nudge_intensity": "medium"},
        )
        assert info.name == "adhs"
        assert info.active is True

    def test_modules_response(self):
        from app.schemas.modules import ModulesResponse
        resp = ModulesResponse(
            active_modules=["core", "adhs"],
            available_modules=[],
        )
        assert "core" in resp.active_modules

    def test_modules_update_validates_module_names(self):
        from app.schemas.modules import ModulesUpdate
        # Valid
        update = ModulesUpdate(active_modules=["core", "adhs"])
        assert "core" in update.active_modules

    def test_modules_update_rejects_unknown_module(self):
        from app.schemas.modules import ModulesUpdate
        with pytest.raises(ValidationError):
            ModulesUpdate(active_modules=["core", "nonexistent_module"])

    def test_modules_update_core_always_included(self):
        """If user omits 'core', it should be auto-added by the validator."""
        from app.schemas.modules import ModulesUpdate
        update = ModulesUpdate(active_modules=["adhs"])
        assert "core" in update.active_modules

    def test_module_config_update(self):
        from app.schemas.modules import ModuleConfigUpdate
        update = ModuleConfigUpdate(config={"nudge_intensity": "high"})
        assert update.config["nudge_intensity"] == "high"
```

**Step 2: Run test to verify it fails**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/test_modules.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.modules'`

**Step 3: Write module constants**

```python
# backend/app/core/modules.py
"""ALICE module system definitions.

Each module is a feature group that users can activate/deactivate.
The 'core' module (Chat, Tasks, Brain, Auth) is always active.
"""

from typing import Any

# Module registry: name -> metadata
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
            "Pattern-Erkennung, Nudges, Task-Breakdown, "
            "Gamification und Focus-Timer"
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
            "Wellbeing-Score, Energie-Tracking, "
            "Schlafmuster-Analyse und proaktive Interventionen"
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
            "Morning Briefing, adaptive Tagesplanung, "
            "Energie-basierte Priorisierung"
        ),
        "default_config": {
            "morning_briefing": True,
            "briefing_time": "07:00",
            "max_daily_tasks": 3,
        },
    },
}

# Modules that cannot be deactivated
ALWAYS_ACTIVE_MODULES: frozenset[str] = frozenset({"core"})

# Modules active by default for new users
DEFAULT_ACTIVE_MODULES: list[str] = ["core", "adhs"]

# Valid module names (for schema validation)
VALID_MODULE_NAMES: frozenset[str] = frozenset(ALL_MODULES.keys())
```

```python
# backend/app/schemas/modules.py
"""Pydantic schemas for the module system."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.modules import VALID_MODULE_NAMES, ALWAYS_ACTIVE_MODULES


class ModuleInfoResponse(BaseModel):
    """Single module info for the available-modules list."""

    name: str = Field(..., description="Module identifier")
    label: str = Field(..., description="Display label (German)")
    icon: str = Field(..., description="Ionicons icon name")
    description: str = Field(..., description="Short description (German)")
    active: bool = Field(..., description="Whether this module is currently active")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Current config for this module"
    )


class ModulesResponse(BaseModel):
    """Response for GET /settings/modules."""

    active_modules: list[str] = Field(..., description="Currently active module names")
    available_modules: list[ModuleInfoResponse] = Field(
        ..., description="All available modules with status"
    )


class ModulesUpdate(BaseModel):
    """Request body for PUT /settings/modules."""

    active_modules: list[str] = Field(
        ..., description="Module names to activate"
    )

    @field_validator("active_modules")
    @classmethod
    def validate_module_names(cls, v: list[str]) -> list[str]:
        for name in v:
            if name not in VALID_MODULE_NAMES:
                raise ValueError(
                    f"Unknown module '{name}'. "
                    f"Valid modules: {sorted(VALID_MODULE_NAMES)}"
                )
        # Always include required modules
        for required in ALWAYS_ACTIVE_MODULES:
            if required not in v:
                v.append(required)
        return v


class ModuleConfigUpdate(BaseModel):
    """Request body for PUT /settings/modules/{module_name}/config."""

    config: dict[str, Any] = Field(
        ..., description="Key-value pairs to merge into module config"
    )
```

**Step 4: Run test to verify it passes**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/test_modules.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add backend/app/core/modules.py backend/app/schemas/modules.py backend/tests/test_modules.py
git commit -m "[HR-455] feat(modules): add module constants, registry and Pydantic schemas

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Module Service Methods (Backend)

**Files:**
- Modify: `backend/app/services/settings.py` (add module methods)
- Modify: `backend/app/models/user_settings.py` (extend DEFAULT_SETTINGS)
- Test: `backend/tests/test_modules.py` (add service tests)

**Context:** Extend the existing `SettingsService` with `get_modules()`, `update_modules()`, and `update_module_config()`. The module state lives in the same JSONB `settings` column alongside existing ADHS settings. No DB migration needed — JSONB is schema-flexible.

**Step 1: Write the failing tests**

Append to `backend/tests/test_modules.py`:

```python
# --- Service-level tests (require DB) ---

class TestModuleService:
    """Tests for module-related SettingsService methods."""

    async def test_get_modules_returns_defaults_for_new_user(
        self, authenticated_client, test_user
    ):
        """New user should have core + adhs active by default."""
        response = await authenticated_client.get("/api/v1/settings/modules")
        assert response.status_code == 200
        data = response.json()
        assert "core" in data["active_modules"]
        assert "adhs" in data["active_modules"]
        assert len(data["available_modules"]) == 4  # core, adhs, wellness, productivity

    async def test_get_modules_shows_active_status(
        self, authenticated_client, test_user
    ):
        """available_modules should show correct active flag."""
        response = await authenticated_client.get("/api/v1/settings/modules")
        data = response.json()
        for mod in data["available_modules"]:
            if mod["name"] in ("core", "adhs"):
                assert mod["active"] is True, f"{mod['name']} should be active"
            else:
                assert mod["active"] is False, f"{mod['name']} should be inactive"

    async def test_activate_wellness_module(self, authenticated_client, test_user):
        """Activating wellness should add it to active_modules."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "adhs", "wellness"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "wellness" in data["active_modules"]

    async def test_deactivate_adhs_module(self, authenticated_client, test_user):
        """Deactivating adhs should remove it but keep core."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "core" in data["active_modules"]
        assert "adhs" not in data["active_modules"]

    async def test_cannot_deactivate_core(self, authenticated_client, test_user):
        """Core is auto-added even if omitted."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["adhs"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "core" in data["active_modules"]
        assert "adhs" in data["active_modules"]

    async def test_invalid_module_name_rejected(self, authenticated_client, test_user):
        """Unknown module name should return 422."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "nonexistent"]},
        )
        assert response.status_code == 422

    async def test_update_module_config(self, authenticated_client, test_user):
        """PUT /settings/modules/adhs/config should merge config."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"nudge_intensity": "high", "auto_breakdown": False}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["nudge_intensity"] == "high"
        assert data["config"]["auto_breakdown"] is False

    async def test_update_config_preserves_existing_keys(
        self, authenticated_client, test_user
    ):
        """Updating one key should not remove other keys."""
        # Set initial config
        await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"nudge_intensity": "low"}},
        )
        # Update different key
        response = await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"auto_breakdown": False}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["nudge_intensity"] == "low"
        assert data["config"]["auto_breakdown"] is False

    async def test_update_config_unknown_module_404(
        self, authenticated_client, test_user
    ):
        """Config update for unknown module should 404."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules/nonexistent/config",
            json={"config": {"key": "value"}},
        )
        assert response.status_code == 404

    async def test_modules_unauthorized(self, client):
        """403 without auth."""
        response = await client.get("/api/v1/settings/modules")
        assert response.status_code == 403

    async def test_existing_adhs_settings_preserved(
        self, authenticated_client, test_user
    ):
        """Activating modules should NOT break existing ADHS settings."""
        # Update ADHS settings first
        await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"nudge_intensity": "high", "focus_timer_minutes": 45},
        )
        # Now activate a new module
        await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "adhs", "wellness"]},
        )
        # Check ADHS settings still intact
        response = await authenticated_client.get("/api/v1/settings/adhs")
        assert response.status_code == 200
        data = response.json()
        assert data["nudge_intensity"] == "high"
        assert data["focus_timer_minutes"] == 45
```

**Step 2: Run tests to verify they fail**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/test_modules.py::TestModuleService -v`
Expected: FAIL — endpoints don't exist yet

**Step 3: Implement service methods and API endpoints**

**3a. Extend DEFAULT_SETTINGS** in `backend/app/models/user_settings.py`:

Add these keys to `DEFAULT_SETTINGS` dict:

```python
    "active_modules": ["core", "adhs"],
    "module_configs": {},
```

**3b. Add service methods** to `backend/app/services/settings.py`:

Add these imports at the top:
```python
from app.core.modules import ALL_MODULES, DEFAULT_ACTIVE_MODULES, ALWAYS_ACTIVE_MODULES, VALID_MODULE_NAMES
from app.schemas.modules import ModuleInfoResponse, ModulesResponse, ModulesUpdate, ModuleConfigUpdate
```

Add these methods to the `SettingsService` class:

```python
    async def get_modules(self, user_id: UUID) -> ModulesResponse:
        """Get active modules and available modules list."""
        user_settings = await self._get_or_create_settings(user_id)
        settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        active = settings.get("active_modules", DEFAULT_ACTIVE_MODULES)
        module_configs = settings.get("module_configs", {})

        available = []
        for name, meta in ALL_MODULES.items():
            config = {**meta["default_config"], **module_configs.get(name, {})}
            available.append(ModuleInfoResponse(
                name=name,
                label=meta["label"],
                icon=meta["icon"],
                description=meta["description"],
                active=name in active,
                config=config,
            ))

        return ModulesResponse(active_modules=active, available_modules=available)

    async def update_modules(self, user_id: UUID, data: ModulesUpdate) -> ModulesResponse:
        """Update which modules are active."""
        user_settings = await self._get_or_create_settings(user_id)
        current = {**DEFAULT_SETTINGS, **user_settings.settings}

        current["active_modules"] = data.active_modules
        user_settings.settings = current
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

        return await self.get_modules(user_id)

    async def update_module_config(
        self, user_id: UUID, module_name: str, data: ModuleConfigUpdate
    ) -> ModuleInfoResponse:
        """Merge config updates for a specific module."""
        if module_name not in VALID_MODULE_NAMES:
            return None  # Caller handles 404

        user_settings = await self._get_or_create_settings(user_id)
        current = {**DEFAULT_SETTINGS, **user_settings.settings}

        module_configs = current.get("module_configs", {})
        existing_config = module_configs.get(module_name, {})
        merged_config = {**ALL_MODULES[module_name]["default_config"], **existing_config, **data.config}

        module_configs[module_name] = merged_config
        current["module_configs"] = module_configs
        user_settings.settings = current
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

        active_modules = current.get("active_modules", DEFAULT_ACTIVE_MODULES)
        meta = ALL_MODULES[module_name]
        return ModuleInfoResponse(
            name=module_name,
            label=meta["label"],
            icon=meta["icon"],
            description=meta["description"],
            active=module_name in active_modules,
            config=merged_config,
        )
```

**3c. Add API endpoints** to `backend/app/api/v1/settings.py`:

Add imports:
```python
from app.schemas.modules import ModulesResponse, ModulesUpdate, ModuleConfigUpdate, ModuleInfoResponse
```

Add endpoints at end of file:
```python
@router.get(
    "/modules",
    response_model=ModulesResponse,
    summary="Get active modules",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active modules and all available modules with their config."""
    service = SettingsService(db)
    return await service.get_modules(current_user.id)


@router.put(
    "/modules",
    response_model=ModulesResponse,
    summary="Update active modules",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_modules(
    data: ModulesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate modules. 'core' is always active."""
    service = SettingsService(db)
    return await service.update_modules(current_user.id, data)


@router.put(
    "/modules/{module_name}/config",
    response_model=ModuleInfoResponse,
    summary="Update module config",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_module_config(
    module_name: str,
    data: ModuleConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update configuration for a specific module (merge)."""
    service = SettingsService(db)
    result = await service.update_module_config(current_user.id, module_name, data)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    return result
```

**Step 4: Run tests to verify they pass**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/test_modules.py -v`
Expected: All tests PASS (unit + integration)

**Step 5: Run existing settings tests to verify no regression**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/test_settings.py -v`
Expected: All existing tests still PASS

**Step 6: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add backend/app/models/user_settings.py backend/app/services/settings.py backend/app/api/v1/settings.py backend/tests/test_modules.py
git commit -m "[HR-455] feat(modules): add module service methods and API endpoints

GET/PUT /settings/modules for module activation
PUT /settings/modules/{name}/config for per-module config
Extends existing JSONB settings — no migration needed

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Mobile Module Settings Store (Expo)

**Files:**
- Create: `mobile/stores/moduleStore.ts`
- Create: `mobile/services/modules.ts`
- Modify: `mobile/services/api.ts` (if needed for type exports)

**Context:** Create a Zustand store that fetches and caches the user's active modules. The store exposes `activeModules`, `availableModules`, `isModuleActive(name)`, `fetchModules()`, `updateModules()`, and `updateModuleConfig()`. Other screens will read from this store to determine what to show.

**Step 1: Create the modules API service**

```typescript
// mobile/services/modules.ts
import api from "./api";

export interface ModuleInfo {
  name: string;
  label: string;
  icon: string;
  description: string;
  active: boolean;
  config: Record<string, unknown>;
}

export interface ModulesResponse {
  active_modules: string[];
  available_modules: ModuleInfo[];
}

export const modulesApi = {
  getModules: async (): Promise<ModulesResponse> => {
    const response = await api.get("/settings/modules");
    return response.data;
  },

  updateModules: async (activeModules: string[]): Promise<ModulesResponse> => {
    const response = await api.put("/settings/modules", {
      active_modules: activeModules,
    });
    return response.data;
  },

  updateModuleConfig: async (
    moduleName: string,
    config: Record<string, unknown>
  ): Promise<ModuleInfo> => {
    const response = await api.put(
      `/settings/modules/${moduleName}/config`,
      { config }
    );
    return response.data;
  },
};
```

**Step 2: Create the Zustand store**

```typescript
// mobile/stores/moduleStore.ts
import { create } from "zustand";
import { modulesApi, ModuleInfo, ModulesResponse } from "../services/modules";

interface ModuleStore {
  activeModules: string[];
  availableModules: ModuleInfo[];
  isLoading: boolean;
  error: string | null;

  isModuleActive: (name: string) => boolean;
  fetchModules: () => Promise<void>;
  updateModules: (activeModules: string[]) => Promise<void>;
  updateModuleConfig: (
    moduleName: string,
    config: Record<string, unknown>
  ) => Promise<void>;
}

export const useModuleStore = create<ModuleStore>((set, get) => ({
  activeModules: ["core", "adhs"],
  availableModules: [],
  isLoading: false,
  error: null,

  isModuleActive: (name: string) => get().activeModules.includes(name),

  fetchModules: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await modulesApi.getModules();
      set({
        activeModules: data.active_modules,
        availableModules: data.available_modules,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateModules: async (activeModules: string[]) => {
    set({ isLoading: true, error: null });
    try {
      const data = await modulesApi.updateModules(activeModules);
      set({
        activeModules: data.active_modules,
        availableModules: data.available_modules,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateModuleConfig: async (
    moduleName: string,
    config: Record<string, unknown>
  ) => {
    try {
      const updated = await modulesApi.updateModuleConfig(moduleName, config);
      set((state) => ({
        availableModules: state.availableModules.map((m) =>
          m.name === moduleName ? updated : m
        ),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },
}));
```

**Step 3: Verify no build errors**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/mobile" && npx tsc --noEmit 2>&1 | head -20`
Expected: No new TypeScript errors related to module files

**Step 4: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add mobile/stores/moduleStore.ts mobile/services/modules.ts
git commit -m "[HR-457] feat(mobile): add module Zustand store and API service

useModuleStore for fetching, caching and updating active modules
modulesApi service wrapping GET/PUT /settings/modules endpoints

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Dynamic Tab-Bar (Expo)

**Files:**
- Modify: `mobile/app/(tabs)/_layout.tsx`

**Context:** Currently has 5 hardcoded `<Tabs.Screen>`. Transform to render tabs dynamically based on `useModuleStore().activeModules`. Core tabs (Chat, Tasks, Brain, Settings) are always visible. Dashboard is shown when any analytics module is active (adhs, wellness). Future modules will add their own tabs.

**Step 1: Define the tab-to-module mapping**

The mapping logic:
- `chat` → always visible (core)
- `tasks` → always visible (core)
- `brain` → always visible (core)
- `dashboard` → visible when `adhs` OR `wellness` OR `productivity` is active
- `settings` → always visible (core)

**Step 2: Implement dynamic tab rendering**

Replace the entire `_layout.tsx` content. Key changes:
- Import `useModuleStore`
- Define `TAB_CONFIG` array with `{ name, title, icon, requiredModules? }`
- Filter tabs: show if `requiredModules` is undefined OR at least one required module is active
- Keep all existing styling and header customization for the chat tab

```typescript
// mobile/app/(tabs)/_layout.tsx
import { Tabs, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { TouchableOpacity, View, Text, Image, useColorScheme } from "react-native";
import { useChatStore } from "../../stores/chatStore";
import { useModuleStore } from "../../stores/moduleStore";
import { useEffect } from "react";

type TabConfig = {
  name: string;
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  /** If set, tab is shown only when at least one of these modules is active */
  requiredModules?: string[];
};

const TAB_CONFIG: TabConfig[] = [
  { name: "chat", title: "Chat mit Alice", icon: "chatbubble-outline" },
  { name: "tasks", title: "Aufgaben", icon: "checkbox-outline" },
  { name: "brain", title: "Brain", icon: "bulb-outline" },
  {
    name: "dashboard",
    title: "Dashboard",
    icon: "analytics-outline",
    requiredModules: ["adhs", "wellness", "productivity"],
  },
  { name: "settings", title: "Einstellungen", icon: "settings-outline" },
];

export default function TabsLayout() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const router = useRouter();
  const { startNewConversation } = useChatStore();
  const { activeModules, fetchModules } = useModuleStore();

  useEffect(() => {
    fetchModules();
  }, []);

  const isTabVisible = (tab: TabConfig): boolean => {
    if (!tab.requiredModules) return true;
    return tab.requiredModules.some((m) => activeModules.includes(m));
  };

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: "#0284c7",
        tabBarInactiveTintColor: "#9ca3af",
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          backgroundColor: isDark ? "#111827" : "#ffffff",
          borderTopColor: isDark ? "#374151" : "#e5e7eb",
        },
        headerStyle: {
          backgroundColor: isDark ? "#111827" : "#ffffff",
        },
        headerTintColor: isDark ? "#ffffff" : "#111827",
      }}
    >
      {TAB_CONFIG.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            href: isTabVisible(tab) ? undefined : null,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name={tab.icon} size={size} color={color} />
            ),
            ...(tab.name === "chat"
              ? {
                  headerLeft: () => (
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        marginLeft: 16,
                        gap: 16,
                      }}
                    >
                      <TouchableOpacity
                        onPress={() => router.push("/(tabs)/chat/history")}
                        accessibilityLabel="Chat-Verlauf"
                      >
                        <Ionicons
                          name="time-outline"
                          size={24}
                          color={isDark ? "#ffffff" : "#111827"}
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={startNewConversation}
                        accessibilityLabel="Neuer Chat"
                      >
                        <Ionicons
                          name="add-circle-outline"
                          size={24}
                          color={isDark ? "#ffffff" : "#111827"}
                        />
                      </TouchableOpacity>
                    </View>
                  ),
                  headerRight: () => (
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        marginRight: 12,
                        gap: 10,
                      }}
                    >
                      <TouchableOpacity
                        onPress={() => router.push("/(tabs)/chat/live")}
                        accessibilityLabel="Live-Gespraech starten"
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: 18,
                          alignItems: "center",
                          justifyContent: "center",
                          backgroundColor: isDark ? "#1e293b" : "#f1f5f9",
                        }}
                      >
                        <Ionicons name="radio" size={20} color="#0284c7" />
                      </TouchableOpacity>
                      <Image
                        source={require("../../assets/alice-avatar.png")}
                        style={{
                          width: 52,
                          height: 52,
                          borderRadius: 26,
                          borderWidth: 2.5,
                          borderColor: "#0284c7",
                          marginTop: 4,
                        }}
                      />
                    </View>
                  ),
                }
              : {}),
          }}
        />
      ))}
    </Tabs>
  );
}
```

**Step 3: Verify the app builds**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/mobile" && npx tsc --noEmit 2>&1 | head -20`
Expected: No new TypeScript errors

**Step 4: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add mobile/app/\(tabs\)/_layout.tsx
git commit -m "[HR-457] feat(mobile): dynamic tab-bar based on active modules

Tabs are now driven by TAB_CONFIG with optional requiredModules.
Dashboard tab hidden when no analytics module is active.
Fetches module state from API on mount.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Module Selection in Onboarding (Expo)

**Files:**
- Modify: `mobile/app/onboarding.tsx`

**Context:** Add a new "modules" step between "welcome" and "name". Shows toggleable cards for each non-core module (adhs, wellness, productivity). ADHS is pre-selected. User can activate/deactivate before proceeding. On completion, the selected modules are sent alongside existing onboarding data.

**Step 1: Implement the modules step**

Key changes to `mobile/app/onboarding.tsx`:

1. Change `OnboardingStep` type: `"welcome" | "modules" | "name" | "settings" | "complete"`
2. Add state: `const [selectedModules, setSelectedModules] = useState<string[]>(["adhs"])`
3. Update `handleCompleteOnboarding` to also call `modulesApi.updateModules(["core", ...selectedModules])`
4. Add `renderModules()` function that shows toggle cards
5. Update progress bar to include the new step
6. Update flow: welcome -> modules -> name -> settings -> complete

The modules step renders each available module (except "core") as a card with:
- Module icon, label, description
- Toggle switch (on/off)
- Visual highlight when active

```typescript
// Add to imports:
import { Switch } from "react-native";
import { modulesApi } from "../services/modules";

// Add MODULE_OPTIONS constant:
const MODULE_OPTIONS = [
  {
    name: "adhs",
    label: "ADHS-Coaching",
    icon: "bulb-outline" as const,
    description: "Pattern-Erkennung, Nudges, Task-Breakdown und Gamification",
    defaultActive: true,
  },
  {
    name: "wellness",
    label: "Wellness & Guardian Angel",
    icon: "heart-outline" as const,
    description: "Wellbeing-Score, Energie-Tracking und proaktive Interventionen",
    defaultActive: false,
  },
  {
    name: "productivity",
    label: "Produktivitaet & Planung",
    icon: "calendar-outline" as const,
    description: "Morning Briefing, adaptive Tagesplanung",
    defaultActive: false,
  },
];
```

The `renderModules()` function:
```typescript
const renderModules = () => (
  <ScrollView
    className="flex-1 px-8 pt-12"
    contentContainerStyle={{ paddingBottom: 40 }}
    showsVerticalScrollIndicator={false}
  >
    <Text
      className={`text-3xl font-bold mb-4 text-center ${
        isDark ? "text-white" : "text-gray-900"
      }`}
    >
      Was soll Alice fuer dich tun?
    </Text>
    <Text
      className={`text-base text-center mb-8 ${
        isDark ? "text-gray-400" : "text-gray-500"
      }`}
    >
      Du kannst Module jederzeit in den Einstellungen aendern.
    </Text>

    {MODULE_OPTIONS.map((mod) => {
      const isActive = selectedModules.includes(mod.name);
      return (
        <TouchableOpacity
          key={mod.name}
          onPress={() => {
            setSelectedModules((prev) =>
              prev.includes(mod.name)
                ? prev.filter((m) => m !== mod.name)
                : [...prev, mod.name]
            );
          }}
          className={`flex-row items-center px-4 py-4 rounded-lg mb-3 border-2 ${
            isActive
              ? "border-primary-600 bg-primary-600/10"
              : isDark
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-300"
          }`}
        >
          <Ionicons
            name={mod.icon}
            size={28}
            color={isActive ? "#0284c7" : isDark ? "#9ca3af" : "#6b7280"}
          />
          <View className="flex-1 ml-4">
            <Text
              className={`text-lg font-semibold ${
                isActive
                  ? "text-primary-600"
                  : isDark
                  ? "text-white"
                  : "text-gray-900"
              }`}
            >
              {mod.label}
            </Text>
            <Text
              className={`text-sm mt-1 ${
                isDark ? "text-gray-400" : "text-gray-500"
              }`}
            >
              {mod.description}
            </Text>
          </View>
          <Switch
            value={isActive}
            onValueChange={() => {
              setSelectedModules((prev) =>
                prev.includes(mod.name)
                  ? prev.filter((m) => m !== mod.name)
                  : [...prev, mod.name]
              );
            }}
            trackColor={{ false: "#767577", true: "#0284c7" }}
            thumbColor="#ffffff"
          />
        </TouchableOpacity>
      );
    })}

    <TouchableOpacity
      onPress={() => setStep("name")}
      className="bg-primary-600 px-8 py-4 rounded-lg mt-4"
    >
      <Text className="text-white text-center text-lg font-semibold">
        Weiter
      </Text>
    </TouchableOpacity>
  </ScrollView>
);
```

Update `handleCompleteOnboarding`:
```typescript
const handleCompleteOnboarding = async () => {
  setIsLoading(true);
  try {
    // Save module selection
    await modulesApi.updateModules(["core", ...selectedModules]);
    // Save other settings
    await api.post("/settings/onboarding", {
      display_name: displayName.trim() || null,
      focus_timer_minutes: focusTimerMinutes,
      nudge_intensity: nudgeIntensity,
    });
  } catch (error) {
    console.error("Onboarding failed:", error);
  } finally {
    setIsLoading(false);
  }
  markOnboardingComplete();
  router.replace("/(tabs)/chat");
};
```

Update progress bar steps: `["modules", "name", "settings", "complete"]` and flow routing.

**Step 2: Verify the app builds**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/mobile" && npx tsc --noEmit 2>&1 | head -20`
Expected: No TypeScript errors

**Step 3: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add mobile/app/onboarding.tsx
git commit -m "[HR-456] feat(mobile): add module selection step to onboarding

New 'modules' step between welcome and name entry.
Users select which coaching modules to activate.
ADHS pre-selected, all modules toggleable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Module Management in Settings Screen (Expo)

**Files:**
- Modify: `mobile/app/(tabs)/settings/index.tsx` (or wherever the settings screen lives)

**Context:** Add a "Module" section to the existing Settings screen. Shows each module with a toggle switch. When toggled, calls `useModuleStore().updateModules()`. Shows a brief explanation that "core" cannot be deactivated.

**Step 1: Locate the settings screen**

Run: `find mobile/app -name "*.tsx" -path "*/settings*"` to locate exact file.

**Step 2: Add Module Management section**

Add a "Meine Module" section at the top of the settings screen. For each module from `useModuleStore().availableModules`:
- Show module icon, label, description
- Toggle switch (disabled for "core" with a note "Immer aktiv")
- When toggled, compute new `active_modules` list and call `updateModules()`

Key code for the section:

```typescript
import { useModuleStore } from "../../../stores/moduleStore";

// Inside component:
const { availableModules, activeModules, updateModules, fetchModules } = useModuleStore();

useEffect(() => {
  fetchModules();
}, []);

const toggleModule = (moduleName: string) => {
  const newModules = activeModules.includes(moduleName)
    ? activeModules.filter((m) => m !== moduleName)
    : [...activeModules, moduleName];
  updateModules(newModules);
};

// Render section:
<View className="mb-6">
  <Text className={`text-lg font-bold mb-3 ${isDark ? "text-white" : "text-gray-900"}`}>
    Meine Module
  </Text>
  {availableModules.map((mod) => (
    <View
      key={mod.name}
      className={`flex-row items-center justify-between px-4 py-3 rounded-lg mb-2 ${
        isDark ? "bg-gray-800" : "bg-white"
      }`}
    >
      <View className="flex-row items-center flex-1">
        <Ionicons name={mod.icon} size={22} color={mod.active ? "#0284c7" : "#9ca3af"} />
        <View className="ml-3 flex-1">
          <Text className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
            {mod.label}
          </Text>
          {mod.name === "core" && (
            <Text className="text-xs text-gray-400">Immer aktiv</Text>
          )}
        </View>
      </View>
      <Switch
        value={mod.active}
        onValueChange={() => toggleModule(mod.name)}
        disabled={mod.name === "core"}
        trackColor={{ false: "#767577", true: "#0284c7" }}
        thumbColor="#ffffff"
      />
    </View>
  ))}
</View>
```

**Step 3: Verify the app builds**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/mobile" && npx tsc --noEmit 2>&1 | head -20`
Expected: No TypeScript errors

**Step 4: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add mobile/app/\(tabs\)/settings/
git commit -m "[HR-457] feat(mobile): add module management section to settings

Toggle modules on/off directly from Settings screen.
Core module shown as 'Immer aktiv' with disabled toggle.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Register Module Schemas in __init__.py

**Files:**
- Modify: `backend/app/schemas/__init__.py`

**Context:** Register the new module schemas in the central schemas package so they're importable from `app.schemas`.

**Step 1: Add imports and __all__ entries**

Add to imports section:
```python
from app.schemas.modules import (
    ModuleConfigUpdate,
    ModuleInfoResponse,
    ModulesResponse,
    ModulesUpdate,
)
```

Add to `__all__`:
```python
    # Phase 6: Modules
    "ModuleInfoResponse",
    "ModulesResponse",
    "ModulesUpdate",
    "ModuleConfigUpdate",
```

**Step 2: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add backend/app/schemas/__init__.py
git commit -m "[HR-455] chore(schemas): register module schemas in __init__.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Run Full Backend Test Suite

**Files:** None (verification only)

**Step 1: Run all backend tests**

Run: `cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach/backend" && python -m pytest tests/ -v --tb=short`
Expected: ALL tests pass, including new module tests and existing settings tests

**Step 2: If any test fails, fix and re-run**

Fix approach: Read the failing test output, identify the root cause, apply minimal fix, re-run.

**Step 3: Commit any fixes**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add -A
git commit -m "[HR-455] fix(modules): address test failures from integration

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Update Linear Task Status

**Files:** None (Linear only)

**Step 1: Update Linear epics**

- HR-455 (Module System Backend): Mark as "Done" with comment listing files changed
- HR-456 (Module Selection Onboarding): Mark as "Done"
- HR-457 (Dynamic Tab-Bar & Module-aware UI): Mark as "Done"

**Step 2: Update Phase 6 milestone progress**

Check that all epics in Phase 6 are complete. HR-458 (Documentation) will be done in Task 10.

---

### Task 10: Documentation Update

**Files:**
- Modify: `docs/plans/2026-02-14-alice-agent-one-transformation-design.md` (mark Phase 6 items as done)

**Context:** Mark completed checklist items in the design doc. Update the ALICE description in any README or docs that reference the old "ADHS-Coach" name.

**Step 1: Update design doc checklist**

Change Phase 6 / Milestone 1 items from `[ ]` to `[x]`:
- `[x]` Module System in UserSettings
- `[x]` Module Selection Onboarding Screen
- `[x]` Dynamic Tab-Bar
- `[x]` Settings Screen Module Management
- `[x]` API: GET/PUT /settings/modules

**Step 2: Mark HR-458 as Done in Linear**

**Step 3: Commit**

```bash
cd "/media/oliver/Platte 2 (Netac)1/alice-adhs-coach"
git add docs/
git commit -m "[HR-458] docs: update design doc with Phase 6 completion status

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```
