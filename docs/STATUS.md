# ALICE - Projektstatus

**Letzte Aktualisierung:** 2026-02-14
**Version:** Phase 5 (in Arbeit)

---

## Ueberblick

**ALICE** (Adaptive Living Intelligence & Cognitive Enhancement) ist ein KI-gestuetzter Personal Assistant mit ADHS-Modus und Second Brain Funktionalitaet. Die App kombiniert proaktive Unterstuetzung, Verhaltensbeobachtung und Gamification, um Menschen mit ADHS im Alltag zu helfen.

- **Projekt-Typ:** Mobile App (React Native + Expo) mit Python FastAPI Backend
- **Repository:** GitHub (private)
- **Projektmanagement:** Linear
- **Status:** Phase 4 abgeschlossen, Phase 5 in Arbeit
- **Tests:** ~300 Tests (alle bestanden, 0 Failures)
- **Test-Coverage:** >= 80%

---

## Technologie-Stack

### Backend

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Programmiersprache | Python | 3.12+ |
| Web Framework | FastAPI | 0.115 |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrationen | Alembic | 1.13+ |
| Schema-Validierung | Pydantic | 2.0+ |
| Task Queue | Celery | 5.3+ |
| Datenbank | PostgreSQL + pgvector | 16.x |
| Cache & Broker | Redis | 7.x |
| KI Framework | CrewAI | 0.40+ |
| Primaeres LLM | Claude API (Anthropic) | -- |
| Fallback LLM | GPT-4 (OpenAI) | -- |
| Voice (STT) | Deepgram | -- |
| Voice (TTS) | ElevenLabs | -- |

### Frontend (Mobile)

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Framework | React Native | 0.73+ |
| Development Platform | Expo | SDK 54 |
| Routing | Expo Router | 3.x |
| Styling | NativeWind (Tailwind CSS) | 4.x |
| Client State | Zustand | 4.x |
| Server State | TanStack Query | 5.x |
| Formulare | React Hook Form + Zod | -- |
| Secure Storage | expo-secure-store | -- |
| Push Notifications | expo-notifications + Expo Push API | -- |
| Type Safety | TypeScript | 5.3+ |

### Infrastruktur

| Komponente | Technologie |
|------------|-------------|
| Containerisierung | Docker + Docker Compose |
| PaaS | Coolify (Self-Hosted) |
| Reverse Proxy | Traefik (via Coolify) |
| CI/CD | GitHub Actions |
| Deployment-Ziel | Hostinger VPS (4 vCPU, 8 GB RAM) |

---

## Features nach Phase

### Phase 1: Foundation ✅ (Abgeschlossen)

**Status:** 47 Tests, alle bestanden

**Backend:**
- User Auth (Register, Login, Logout, Token Refresh) mit JWT
- Chat mit Claude API (SSE Streaming + Tool Use)
- PostgreSQL Setup + pgvector Extension
- Redis Setup (Cache + Broker)
- Docker Compose Development Setup

**Frontend:**
- Expo App Skeleton mit Tab Navigation
- Auth Screens (Login, Register)
- Chat Screen mit SSE Streaming
- Zustand State Management (Auth)
- TanStack Query (Server State)

**API Endpoints:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/chat/message` (SSE)
- `GET /api/v1/chat/conversations`
- `GET /api/v1/chat/conversations/{id}/messages`
- `WS /api/v1/chat/ws`

**Migration:**
- `001_foundation` - Users, Conversations, Messages

---

### Phase 2: Core Features ✅ (Abgeschlossen)

**Status:** 124 Tests (77 neue), alle bestanden

**Backend Services:**
- **TaskService:** Task CRUD, Complete (+XP), Breakdown, Today
- **BrainService:** Entry CRUD, Search (RAG), Ingest
- **PersonalityService:** Profile Management, System Prompt Composition
- **ProactiveService:** Mentioned Items Extraction, Daily Planning

**Frontend:**
- 22 neue Dateien (Screens, Components, Hooks, Services, Types)
- Tasks Screen (Liste, Detail, Create)
- Brain Screen (Liste, Detail, Create, Search)
- Settings Screen (Personality Editor)

**API Endpoints (24 neue):**
- **Tasks:** 8 Endpoints (CRUD + complete + breakdown + today)
- **Brain:** 6 Endpoints (CRUD + search)
- **Personality:** 7 Endpoints (CRUD + activate + templates + preview)
- **Proactive:** 3 Endpoints (mentioned-items + convert + dismiss + snooze)

**Migration:**
- `002_phase2_tables` - Tasks, Brain Entries, Brain Embeddings, Mentioned Items, Personality Profiles, Personality Templates (6 Tabellen, 7 Enums, 22 Indexes, 4 Seed Templates)

**Hinweise:**
- CrewAI Orchestrator: DB/API Infrastruktur vorhanden, echte AI-Integration noch nicht implementiert
- Brain Search: Aktuell nur ILIKE-Textsuche, semantische Vektorsuche noch nicht aktiv

---

### Phase 3: ADHS-Modus ✅ (Abgeschlossen)

**Status:** 194 Tests (70 neue), alle bestanden

**Backend Services:**
- **GamificationService:** XP Berechnung, Level, Streak, Achievements
- **TaskBreakdownService:** KI-gestuetzte Task-Zerlegung
- **NudgeService:** Proaktive Erinnerungen, Eskalationslogik
- **SettingsService:** ADHS-Einstellungen (Nudge-Intensitaet, Auto-Breakdown, Ruhezeiten)
- **DashboardService:** Aggregierte Tagesuebersicht

**Frontend:**
- Focus-Timer Screen (Pomodoro mit Pause/Resume/Reset)
- Achievements Screen (Liste mit Unlock-Status)
- Dashboard Screen (Tagesplan, Heutige Tasks, XP, Streak)
- ADHS Settings Screen (Nudge-Intensitaet, Gamification-Toggle, Ruhezeiten)

**API Endpoints (11 neue):**
- **Gamification:** 3 Endpoints (stats, history, achievements)
- **Task Breakdown:** 2 Endpoints (breakdown, confirm)
- **Nudges:** 3 Endpoints (list, acknowledge, history)
- **Dashboard:** 1 Endpoint (summary)
- **Settings:** 2 Endpoints (get, update ADHS settings)

**Migration:**
- `003_phase3_tables` - Achievements, User Stats, User Settings, Nudge History (4 Tabellen, 2 Enums)

**Bug Fixes:**
- Test-Infrastruktur: `clean_tables` Fixture Teardown-Reihenfolge behoben (Deadlock-Problem geloest)
- `personality.py`: `activate_profile()` flush-Reihenfolge geaendert (UniqueViolation behoben)

---

### Phase 4: Polish & Extras 🔄 (In Arbeit)

**Status:** Teilweise implementiert

**Bereits implementiert:**
- ✅ Zeitbewusstsein im Chat (Datum/Uhrzeit Europe/Berlin im System-Prompt)
- ✅ Push Notifications Backend (Expo Push API Integration im NotificationService)
- ✅ Background Scheduler (asyncio Task im FastAPI-Prozess, 5-Min-Intervall)
  - Deadline-Warnungen (Tasks faellig in 24h)
  - Ueberfaellige Tasks (due_date < jetzt)
  - Streak-Warnungen (Nutzer war heute noch nicht aktiv)
- ✅ Push Token Endpoint (`POST /api/v1/settings/push-token`)
- ✅ Mobile: expo-notifications Plugin Integration
- ✅ Mobile: notificationStore Rewrite mit vollem State Management
- ✅ Mobile: Notification Listener + Navigation bei Tap

**API Endpoints (1 neu):**
- `POST /api/v1/settings/push-token` - Expo Push Token registrieren

**Noch ausstehend:**
- LiveKit Voice Chat Integration
- Google Calendar Sync (Plugin)
- n8n Bridge (Plugin)
- Voice Journal (Plugin)
- Weitere Features aus HR-19, HR-20 (Linear)

---

### Phase 5: Knowledge Graph & NLP 🔄 (In Arbeit)

**Status:** Grundsystem implementiert

**Backend Services:**
- **GraphitiClient:** FalkorDB-basierter temporaler Knowledge Graph (Graphiti Framework)
- **NLPAnalyzer:** Stimmungs-, Energie- und Fokus-Analyse pro Gespraech (Claude Haiku)
- **PatternAnalyzer:** Trend-Erkennung ueber Zeit aus pattern_logs
- **MemoryService:** Orchestrator fuer Graph + NLP
- **ContextBuilder:** System Prompt Enrichment mit Memory-Kontext

**API Endpoints (4 neue):**
- `GET /api/v1/memory/status` - Memory-System Status
- `GET /api/v1/memory/export` - DSGVO Art. 15 Datenexport
- `DELETE /api/v1/memory` - DSGVO Art. 17 Komplett-Loeschung
- `PUT /api/v1/settings/memory` - Memory ein/ausschalten

**Migration:**
- `004_phase5_memory` - pattern_logs (1 Tabelle)

**ADHS Patterns (13 Seed):**
Procrastination, Hyperfocus, Task-Switching, Paralysis by Analysis,
Time Blindness, Emotional Dysregulation, Rejection Sensitivity,
Dopamine Seeking, Working Memory Overload, Sleep Disruption,
Transition Difficulty, Perfectionism Paralysis, Social Masking

**Infrastruktur:**
- FalkorDB v4.4.1 ersetzt Redis (Redis-kompatibel, FalkorDB Modul fuer Graph)
- graphiti-core[falkordb,anthropic] >= 0.5, < 1.0

**Noch ausstehend:**
- FalkorDB + Graphiti Produktiv-Test (erfordert laufenden FalkorDB Container)
- Pattern Discovery Service (automatische Erkennung neuer Muster)
- Mobile UI fuer Memory-Status und Trends

---

## Datenbank

### Migrationen

| Migration | Datum | Tabellen | Enums | Status |
|-----------|-------|----------|-------|--------|
| `001_foundation` | 2026-02-04 | 3 (users, conversations, messages) | 1 (MessageRole) | ✅ |
| `002_phase2_tables` | 2026-02-05 | 6 (tasks, brain_entries, brain_embeddings, mentioned_items, personality_profiles, personality_templates) | 7 (TaskStatus, TaskPriority, BrainEntryType, MentionedItemType, MentionedItemStatus, PersonalityTrait, VoiceType) | ✅ |
| `003_phase3_tables` | 2026-02-06 | 4 (achievements, user_stats, user_settings, nudge_history) | 2 (AchievementCategory, NudgePriority) | ✅ |
| `004_phase5_memory` | 2026-02-14 | 1 (pattern_logs) | 0 | ✅ |
| **Gesamt** | -- | **14 Tabellen** | **10 Enums** | -- |

### Schema-Highlights

- **users:** Auth-Daten, is_active Flag
- **tasks:** CRUD, Prioritaet, Due Date, Sub-Tasks (self-referencing parent_id), Gamification-Integration
- **brain_entries:** Second Brain, Tags, Entry Types (note, idea, learning, reflection)
- **brain_embeddings:** pgvector Similarity Search (384 Dimensionen)
- **personality_profiles:** Template-basiert, Traits (creativity, structure, empathy, humor, directness), System Prompt Composition
- **user_settings:** JSONB Blob (ADHS-Einstellungen, expo_push_token, notifications_enabled)
- **user_stats:** XP, Level, Streak (current_streak, longest_streak, last_active_date)
- **achievements:** Gamification (unlock_conditions, rewards, category)
- **nudge_history:** Proaktive Erinnerungen (priority, acknowledged_at)

---

## Tests

### Test-Coverage

| Phase | Tests | Status | Coverage |
|-------|-------|--------|----------|
| Phase 1 | 47 | ✅ Alle bestanden | >= 80% |
| Phase 2 | +77 (Total: 124) | ✅ Alle bestanden | >= 80% |
| Phase 3 | +70 (Total: 194) | ✅ Alle bestanden | >= 80% |
| Phase 5 | +~106 (Total: ~300) | ✅ Alle bestanden | >= 80% |

### Test-Infrastruktur

- PostgreSQL Test-DB (`alice_test`)
- pytest + pytest-asyncio
- TestContainers (optional)
- Coverage Reports (HTML + XML)
- `clean_tables` Fixture: DELETE mit `session_replication_role = replica` (FK-frei)
- Teardown-Reihenfolge: client zuerst (schliesst Verbindungen) → dann DELETE (vermeidet Deadlocks)
- **NIEMALS `app_engine.dispose()` in Tests** (zerstoert Singleton Engine)

### Test-Kategorien

- **Unit Tests:** Services, Models, Schemas
- **Integration Tests:** API Endpoints (E2E mit TestClient)
- **DB Tests:** Migrationen, Constraints, Relationships

---

## API Endpoints - Gesamt-Uebersicht

### Phase 1: Foundation (10 Endpoints)

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/health` | Service Health Check |
| POST | `/api/v1/auth/register` | Benutzer-Registrierung |
| POST | `/api/v1/auth/login` | Benutzer-Login |
| POST | `/api/v1/auth/refresh` | Token erneuern |
| POST | `/api/v1/auth/logout` | Ausloggen |
| GET | `/api/v1/auth/me` | Eigenes Profil |
| POST | `/api/v1/chat/message` | Nachricht senden (SSE) |
| GET | `/api/v1/chat/conversations` | Konversationsliste |
| GET | `/api/v1/chat/conversations/{id}/messages` | Nachrichten |
| WS | `/api/v1/chat/ws` | WebSocket Chat |

### Phase 2: Core Features (14 Endpoints)

| Method | Path | Beschreibung |
|--------|------|-------------|
| POST | `/api/v1/tasks` | Task erstellen |
| GET | `/api/v1/tasks` | Tasks auflisten |
| GET | `/api/v1/tasks/today` | Heutige Tasks |
| GET | `/api/v1/tasks/{id}` | Task abrufen |
| PUT | `/api/v1/tasks/{id}` | Task aktualisieren |
| DELETE | `/api/v1/tasks/{id}` | Task loeschen |
| POST | `/api/v1/tasks/{id}/complete` | Task erledigen (+XP) |
| POST | `/api/v1/brain/entries` | Brain-Eintrag erstellen |
| GET | `/api/v1/brain/entries` | Eintraege auflisten |
| GET | `/api/v1/brain/entries/{id}` | Eintrag abrufen |
| PUT | `/api/v1/brain/entries/{id}` | Eintrag aktualisieren |
| DELETE | `/api/v1/brain/entries/{id}` | Eintrag loeschen |
| GET | `/api/v1/brain/search` | Semantische Suche |
| POST | `/api/v1/personality/profiles` | Profil erstellen |
| GET | `/api/v1/personality/profiles` | Profile auflisten |
| PUT | `/api/v1/personality/profiles/{id}` | Profil bearbeiten |
| DELETE | `/api/v1/personality/profiles/{id}` | Profil loeschen |
| POST | `/api/v1/personality/profiles/{id}/activate` | Profil aktivieren |
| GET | `/api/v1/personality/templates` | Templates auflisten |
| GET | `/api/v1/personality/preview` | Personality Preview (AI) |
| GET | `/api/v1/proactive/mentioned-items` | Mentioned Items auflisten |
| POST | `/api/v1/proactive/mentioned-items/{id}/convert` | Item konvertieren |
| POST | `/api/v1/proactive/mentioned-items/{id}/dismiss` | Item verwerfen |
| POST | `/api/v1/proactive/mentioned-items/{id}/snooze` | Item snoozen |

### Phase 3: ADHS-Modus (12 Endpoints)

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/v1/gamification/stats` | XP, Level, Streak |
| GET | `/api/v1/gamification/history` | XP-Verlauf |
| GET | `/api/v1/gamification/achievements` | Achievements |
| POST | `/api/v1/tasks/{id}/breakdown` | Task-Breakdown |
| POST | `/api/v1/tasks/{id}/breakdown/confirm` | Sub-Tasks erstellen |
| GET | `/api/v1/nudges` | Aktive Nudges |
| POST | `/api/v1/nudges/{id}/acknowledge` | Nudge bestaetigen |
| GET | `/api/v1/nudges/history` | Nudge-Verlauf |
| GET | `/api/v1/dashboard/summary` | Dashboard-Daten |
| GET | `/api/v1/settings/adhs` | ADHS-Einstellungen lesen |
| PUT | `/api/v1/settings/adhs` | ADHS-Einstellungen aendern |
| POST | `/api/v1/settings/push-token` | Push Token registrieren |

### Phase 5: Memory (4 Endpoints)

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/v1/memory/status` | Memory-System Status |
| GET | `/api/v1/memory/export` | DSGVO Art. 15 Datenexport |
| DELETE | `/api/v1/memory` | DSGVO Art. 17 Komplett-Loeschung |
| PUT | `/api/v1/settings/memory` | Memory ein/ausschalten |

**Gesamt: 40 Endpoints**

---

## Deployment

### Entwicklungsumgebung

```bash
# Backend starten (lokal)
cd backend
poetry shell
uvicorn app.main:app --reload

# Mobile App starten (lokal)
cd mobile
npm start
```

### Docker Compose (Development)

```bash
docker-compose up -d
```

Services:
- **api:** FastAPI (Port 8000)
- **db:** PostgreSQL 16 + pgvector (Port 5432)
- **falkordb:** FalkorDB 4.4.1 (Port 6379, Redis-kompatibel + Graph)
- **celery:** Celery Worker (Placeholder)

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Services:
- **api:** FastAPI (2 Uvicorn Workers)
- **celery:** Celery Worker (1 Worker, 4 Threads)
- **scheduler:** APScheduler (in-process, 1 Instanz)
- **db:** PostgreSQL 16 + pgvector
- **falkordb:** FalkorDB 4.4.1 (Redis-kompatibel + Graph)

### Coolify Deployment

- **Ziel:** Hostinger VPS (4 vCPU, 8 GB RAM)
- **Reverse Proxy:** Traefik (SSL Termination)
- **Health Check:** `GET /health`
- **CI/CD:** GitHub Actions Webhook

---

## Dokumentation

### Nextra Docs (geplant)

- `/docs/user/` - Benutzerhandbuch
- `/docs/developer/` - Entwickler-Dokumentation
- `/docs/api/` - API-Referenz

### Aktuelle Dokumentation

| Datei | Beschreibung |
|-------|-------------|
| `/docs/ARCHITECTURE.md` | Systemarchitektur (5-Schicht-Modell, Diagramme, Datenfluss) |
| `/docs/api/ENDPOINTS.md` | API Endpoints Phase 1+2 |
| `/docs/api/ENDPOINTS-PHASE3.md` | API Endpoints Phase 3 |
| `/docs/database/SCHEMA.md` | Datenbankschema |
| `/docs/DEPLOYMENT.md` | Deployment-Anleitung |
| `/docs/DECISIONS.md` | Architektur-Entscheidungen (ADRs) |
| `/docs/changelog.md` | Aenderungsprotokoll |
| `/docs/STATUS.md` | Dieser Dokument (Projektstatus) |

---

## Known Issues & Limitations

### Phase 2 Limitations

- **CrewAI Orchestrator:** DB/API Infrastruktur vorhanden, echte AI-Integration noch nicht implementiert
- **Brain Search:** Aktuell nur ILIKE-Textsuche, semantische Vektorsuche noch nicht aktiv
- **Background Jobs:** Celery Worker ist Placeholder, keine echten Background Jobs

### Phase 3 Limitations

- **Nudge Engine:** Eskalationslogik implementiert, aber nicht zeitgesteuert ausgefuehrt (wartet auf Background Scheduler)
- **Daily Planning:** Infrastruktur vorhanden, aber noch nicht zeitgesteuert

### Phase 4 Limitations (aktuell)

- **Push Notifications:** Backend implementiert, Mobile-Client empfaengt Notifications aber Navigation-Logik ist simpel (kein Deep Link State Management)
- **Background Scheduler:** Laeuft im FastAPI-Prozess (nicht skalierbar fuer viele Nutzer, sollte spaeter auf Celery migriert werden)
- **Expo Go:** expo-notifications Lazy Import verhindert Crashes, aber einige Features nicht in Expo Go verfuegbar

---

## Next Steps (Phase 5+)

### Prioritaet 1 (Kritisch)

- [ ] **FalkorDB Produktiv-Test:** FalkorDB Container + Graphiti Integration im laufenden System testen
- [ ] **Pattern Discovery Service:** Automatische Erkennung neuer ADHS-Muster aus Gespraechen
- [ ] **Memory E2E Integration Tests:** Vollstaendige Integrationstests mit FalkorDB Container

### Prioritaet 2 (Wichtig)

- [ ] **Mobile Memory UI:** Memory-Status, Trend-Anzeige und Einstellungen in der App
- [ ] **Push Notification Deep Linking:** Robustes Deep Link State Management
- [ ] **Background Scheduler Migration:** Von asyncio Task zu Celery Worker (Skalierbarkeit)
- [ ] **Semantische Brain-Suche:** pgvector Cosine Similarity aktivieren (aktuell nur ILIKE)

### Prioritaet 3 (Nice-to-Have)

- [ ] **LiveKit Voice Chat:** Echtzeit-Voice-Chat-Integration
- [ ] **Google Calendar Sync:** Plugin-basierte Kalender-Synchronisation
- [ ] **Nextra Docs:** User + Developer Dokumentation (aktuell nur Markdown)
- [ ] **CI/CD:** GitHub Actions (Lint, Test, Build, Deploy)
- [ ] **Monitoring:** Sentry (Error Tracking), Prometheus (Metrics)

---

## Team

| Rolle | Agent | Modell |
|-------|-------|--------|
| Team Lead & PM | Orchestrator | Opus |
| Product Owner | product-owner | Opus |
| Architect | architect | Opus |
| Security Auditor | security-auditor | Opus |
| UX Designer | ux-designer | Sonnet |
| Frontend Dev | frontend-dev | Sonnet |
| Backend Dev | backend-dev | Sonnet |
| Database Manager | database-mgr | Sonnet |
| Test Engineer | test-engineer | Sonnet |
| Docs Writer | docs-writer | Sonnet |
| DevOps Engineer | devops-engineer | Sonnet |

---

## Kontakt & Ressourcen

- **Repository:** GitHub (private)
- **Projektmanagement:** Linear (Team: Hr-codelabs)
- **Kommunikation:** Deutsch
- **Working Dir:** `/media/oliver/Platte 2 (Netac)/alice-adhs-coach`
