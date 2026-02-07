---
title: Changelog
description: Aenderungsprotokoll fuer ALICE ADHS-Coach
---

# Changelog

Alle wesentlichen Aenderungen am ALICE-Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Unreleased]

### Hinzugefuegt

- **Zeitbewusstsein:** ALICE kennt jetzt Datum und Uhrzeit (Zeitzone: Europe/Berlin) im System-Prompt. Der ChatService injiziert die aktuelle Zeit, sodass ALICE zeitlich relevante Vorschlaege machen kann (z.B. "Es ist spaet, vielleicht morgen?").
- **Push Notifications Backend:** Expo Push API Integration im `NotificationService` mit Single- und Bulk-Push-Support, Retry-Logik und Token-Validierung.
- **Background Scheduler:** Automatischer Scheduler (asyncio Task im FastAPI-Prozess, 5-Minuten-Intervall) fuer proaktive Checks:
  - Deadline-Warnungen (Tasks faellig in den naechsten 24h)
  - Ueberfaellige Tasks (due_date < jetzt, status != completed)
  - Streak-Warnungen (Nutzer war heute noch nicht aktiv)
- **Push Token Endpoint:** `POST /api/v1/settings/push-token` zum Registrieren von Expo Push Tokens. Token wird im `user_settings` JSONB-Blob gespeichert (kein neues DB-Feld oder Migration noetig).
- **Mobile: expo-notifications Plugin:** Integration von `expo-notifications` im Mobile-Client mit Permission-Dialog und Android-Notification-Channel.
- **Mobile: notificationStore Rewrite:** Vollstaendiges State Management fuer Push Notifications mit Zustand Store.
- **Mobile: Notification Listener:** App hoert auf eingehende Notifications und navigiert zu relevantem Screen bei Tap.
- **ARCHITECTURE.md Erweiterung:** Neuer Abschnitt 4.5 "Background Scheduler und Push Notifications" mit Mermaid-Diagramm und detaillierter Beschreibung.

### Geaendert

- `DEFAULT_SETTINGS` in `backend/app/core/config.py` erweitert um `expo_push_token` (string | null) und `notifications_enabled` (bool).
- `ADHSSettingsResponse` und `ADHSSettingsUpdate` Schemas in `backend/app/schemas/settings.py` um Push-Felder erweitert.
- `SettingsService` in `backend/app/services/settings.py`: Neue Methode `register_push_token()` hinzugefuegt.
- `main.py` Lifespan-Funktion: Scheduler-Start beim App-Start (skip in Testumgebung via `TESTING=true` Env-Variable).
- `mobile/app/_layout.tsx`: Push Notification Init und Listener bei erfolgreicher Authentifizierung.
- `mobile/app/(tabs)/chat/index.tsx`: KeyboardAvoidingView Fix fuer bessere Tastatur-Behandlung.

### Behoben

- **Expo Go Kompatibilitaet:** Lazy Import fuer `expo-notifications` verhindert Crashes in Expo Go (Plugin wird erst bei tatsaechlicher Nutzung geladen).
- **Tastatur-Overlay im Chat:** KeyboardAvoidingView mit korrektem `behavior` Prop (`padding` auf iOS, `height` auf Android) behoben.

---

## [Phase 3] - ADHS-Modus - 2026-02-06

### Hinzugefuegt

- 194 Tests (alle bestanden, 0 Failures)
- **Gamification System:** XP, Levels, Streaks, Achievements
  - `GET /api/v1/gamification/stats` - XP, Level, Streak, Fortschritt
  - `GET /api/v1/gamification/history` - XP-Verlauf pro Tag
  - `GET /api/v1/gamification/achievements` - Achievement-Liste mit Unlock-Status
- **Focus-Timer:** Pomodoro-Timer mit Pause/Resume/Reset Funktionalitaet
- **Dashboard Screen:** Aggregierte Tagesuebersicht mit Tagesplan, Heutigen Tasks, XP-Fortschritt, Streak-Anzeige
  - `GET /api/v1/dashboard/summary` - Dashboard-Daten
- **ADHS Settings Screen:** Konfiguration fuer ADHS-Modus, Nudge-Intensitaet, Auto-Breakdown, Gamification, Fokus-Timer-Dauer, Ruhezeiten
  - `GET /api/v1/settings/adhs` - Einstellungen lesen
  - `PUT /api/v1/settings/adhs` - Einstellungen aendern
- **Task-Breakdown Service:** KI-gestuetzte Zerlegung grosser Tasks in Sub-Tasks
  - `POST /api/v1/tasks/{id}/breakdown` - Breakdown vorschlagen
  - `POST /api/v1/tasks/{id}/breakdown/confirm` - Sub-Tasks erstellen
- **Nudge System:** Proaktive Erinnerungen und Eskalationslogik (DB + API)
  - `GET /api/v1/nudges` - Aktive Nudges abrufen
  - `POST /api/v1/nudges/{id}/acknowledge` - Nudge bestaetigen
  - `GET /api/v1/nudges/history` - Nudge-Verlauf
- **Verhaltensbeobachtungen:** `save_observation()` und `search_observations()` im BrainService fuer ADHS-spezifisches User Behavior Tracking
- **Migration 003_phase3_tables:** 4 neue Tabellen (achievements, user_stats, user_settings, nudge_history) + 2 Enums (AchievementCategory, NudgePriority)

### Geaendert

- `task_service.py`: `complete_task()` vergibt jetzt XP basierend auf Prioritaet und aktualisiert Streak.
- `personality.py`: `activate_profile()` flush-Reihenfolge geaendert (UniqueViolation bei Unique Partial Index behoben).

### Behoben

- **Test-Infrastruktur:** `clean_tables` Fixture als `autouse=True` vor `client` Fixture. Teardown-Reihenfolge: client zuerst (schliesst Verbindungen) → dann DELETE (vermeidet Deadlocks).
- **Test Cleanup:** `session_replication_role = replica` fuer FK-freies DELETE, TRUNCATE entfernt (AccessExclusiveLock Deadlocks).
- **setup_db:** `pg_terminate_backend()` killt Orphan-Connections vor Test-DB-Drop.
- **NIEMALS `app_engine.dispose()` in Tests:** Engine ist Singleton und darf nicht zerstoert werden.

---

## [Phase 2] - Core Features - 2026-02-05

### Hinzugefuegt

- 124 Tests (alle bestanden, 0 Failures)
- **Migration 002_phase2_tables:** 6 neue Tabellen (tasks, brain_entries, brain_embeddings, mentioned_items, personality_profiles, personality_templates), 7 Enums, 22 Indexes, 4 Seed-Templates
- **Backend Services:**
  - `TaskService` - Task CRUD, Complete (+XP), Breakdown, Today
  - `BrainService` - Brain Entry CRUD, Search (RAG), Ingest
  - `PersonalityService` - Profile Management, System Prompt Composition
  - `ProactiveService` - Mentioned Items Extraction, Daily Planning
- **Backend Router:** 24 neue Endpoints
  - 8 Task-Endpoints (CRUD + complete + breakdown + today)
  - 6 Brain-Endpoints (CRUD + search)
  - 7 Personality-Endpoints (CRUD + activate + templates + preview)
  - 3 Proactive-Endpoints (mentioned-items + convert + dismiss + snooze)
- **Frontend:** 22 neue Dateien
  - Screens: Tasks, Brain, Settings (Personality, ADHS)
  - Components: TaskCard, TaskForm, EntryCard, EntryForm, SearchBar
  - Hooks: useTasks, useBrain, usePersonality, useDashboard
  - Services: taskApi, brainApi, personalityApi, proactiveApi
  - Types: task, brain, personality, proactive
- **Tests:** 77 neue Tests
  - 26 Task-Tests (CRUD + complete + breakdown + today)
  - 23 Brain-Tests (CRUD + search + embeddings)
  - 17 Personality-Tests (CRUD + activate + templates + preview)
  - 8 Proactive-Tests (mentioned-items + convert + dismiss + snooze)
  - 3 Misc-Tests (Health Check, CORS, Rate Limiting)

### Hinweis

- **CrewAI Orchestrator:** DB/API Infrastruktur vorhanden, aber echte AI-Integration und Background Jobs noch nicht implementiert.
- **pgvector:** Python Package muss in `.venv` installiert sein fuer Vektor-Operationen.
- **Brain Search:** Aktuell nur ILIKE-Textsuche, semantische Vektorsuche noch nicht aktiv.

---

## [Phase 1] - Foundation - 2026-02-04

### Hinzugefuegt

- 47 Tests (alle bestanden)
- **Auth System:** User Registration, Login, Logout, Token Refresh (JWT-basiert)
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
- **Chat System:** Nachrichten mit Claude API, SSE Streaming, Tool Use
  - `POST /api/v1/chat/message` (SSE Streaming)
  - `GET /api/v1/chat/conversations`
  - `GET /api/v1/chat/conversations/{id}/messages`
  - `WS /api/v1/chat/ws`
- **Mobile App Skeleton:** Expo SDK 54, Expo Router, NativeWind v4, Zustand, TanStack Query v5
  - Tab Navigation (Chat, Tasks, Brain, Dashboard, Settings)
  - Auth Screens (Login, Register)
  - Chat Screen mit SSE Streaming
- **Docker Setup:** `docker-compose.yml` mit PostgreSQL 16, Redis 7, FastAPI, Celery (Placeholder)
- **Migration 001_foundation:** User, Conversation, Message Tabellen

### Technologie-Stack

- **Backend:** Python 3.12+, FastAPI 0.115, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **AI:** CrewAI, Claude API (Anthropic)
- **Datenbank:** PostgreSQL 16 + pgvector Extension
- **Cache:** Redis 7
- **Frontend:** React Native, Expo SDK 54, Expo Router, NativeWind v4, Zustand, TanStack Query v5
- **CI/CD:** GitHub Actions
- **Deployment:** Docker Compose, Coolify (Self-Hosted PaaS)
