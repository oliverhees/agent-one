# ALICE -- Proactive Personal Assistant mit ADHS-Modus & Second Brain

## Projekt-Briefing

**Projektname:** ALICE (Adaptive Living Intelligence & Cognitive Enhancement)
**Projekttyp:** Premium Personal Assistant App (Mobile)
**Startdatum:** 2026-02-06
**Status:** Planung

---

## 1. Vision

ALICE ist eine KI-gestuetzte Personal Assistant App, die speziell fuer Menschen mit ADHS optimiert ist. Sie kombiniert:

- **Voice-First Interaktion** -- natuerliche Sprachkommunikation als primaerer Eingabekanal
- **Proaktives Task-Management** -- ALICE wartet nicht auf Befehle, sie erinnert, motiviert und eskaliert
- **Second Brain** -- semantische Wissensdatenbank mit RAG-basierter Suche
- **ADHS-Modus** -- Gamification, Nudge-Strategien, Task-Breakdown und anpassbare Persoenlichkeit
- **Plugin-System** -- erweiterbar durch Google Calendar, n8n, Voice Journal und mehr

Das Alleinstellungsmerkmal ist der **proaktive Agent**: ALICE analysiert Gespraeche, extrahiert Aufgaben, plant den Tag, erinnert an Deadlines und eskaliert bei Nicht-Erledigung -- alles angepasst an ADHS-typische Herausforderungen.

---

## 2. Zielgruppe

### Primaere Zielgruppe
- **Menschen mit ADHS** (diagnostiziert oder Verdacht), 18-45 Jahre
- Tech-affin, Smartphone als Hauptgeraet
- Kaempfen mit: Vergesslichkeit, Prokrastination, Zeitmangement, Ueberwaeltigung bei grossen Aufgaben

### Sekundaere Zielgruppe
- **Knowledge Worker** die einen intelligenten Assistenten suchen
- Personen die ihr Wissen strukturiert ablegen wollen (Second Brain)
- Menschen die Voice-First Interaktion bevorzugen

### Personas

**Max, 28, Softwareentwickler mit ADHS**
- Vergisst staendig Aufgaben die im Gespraech erwaehnt werden
- Braucht externe Struktur fuer seinen Tag
- Wird von grossen Aufgaben ueberwaeltigt
- Reagiert gut auf Gamification

**Lisa, 34, Projektmanagerin**
- Sammelt Wissen aus vielen Quellen
- Will schnellen Zugriff auf fruehere Notizen und Ideen
- Nutzt Voice Memos staendig
- Braucht proaktive Erinnerungen an Follow-Ups

---

## 3. Tech-Stack

### Frontend
| Technologie | Zweck |
|---|---|
| React Native + Expo | Cross-Platform Mobile App |
| Expo Router | Navigation |
| NativeWind / Tailwind | Styling |
| Zustand | Client State Management |
| TanStack Query | Server State / Caching |
| React Hook Form + Zod | Formulare + Validierung |

### Backend
| Technologie | Zweck |
|---|---|
| Python 3.12+ | Backend-Sprache |
| FastAPI | Web Framework + WebSocket |
| SQLAlchemy 2.0 | ORM |
| Alembic | Datenbank-Migrationen |
| Pydantic v2 | Schema-Validierung |
| Celery + Redis | Task Queue + Cache |
| APScheduler | Proaktive Jobs |

### KI / AI Engine
| Technologie | Zweck |
|---|---|
| CrewAI | Multi-Agent Orchestrierung |
| Claude API (Anthropic) | Primaeres LLM |
| GPT-4 (OpenAI) | Fallback LLM |
| pgvector | Vektor-Embeddings |
| Sentence Transformers | Embedding-Generierung |

### Voice
| Technologie | Zweck |
|---|---|
| LiveKit (Self-Hosted) | Voice-Streaming Infrastruktur |
| Deepgram | Speech-to-Text |
| ElevenLabs | Text-to-Speech |

### Infrastruktur
| Technologie | Zweck |
|---|---|
| Docker + Docker Compose | Containerisierung |
| Coolify | Self-Hosted PaaS |
| Hostinger VPS | Server |
| GitHub Actions | CI/CD |
| PostgreSQL 16 | Datenbank |
| Redis 7 | Cache + Message Broker |

---

## 4. Projekt-Phasen (Milestones)

### Phase 1: Foundation (MVP Core)
**Ziel:** Funktionierender Chat mit Auth und Basisinfrastruktur
**Erfolgskriterium:** Nutzer kann sich registrieren, einloggen und mit ALICE chatten (Streaming)

Umfang:
- Docker Compose Setup (FastAPI + PostgreSQL + Redis)
- User-Authentifizierung (JWT)
- Chat mit Claude API (Streaming)
- React Native App mit Login + Chat Screen
- WebSocket fuer Echtzeit-Kommunikation

### Phase 2: Core Features
**Ziel:** Task-Management, Second Brain und proaktiver Agent
**Erfolgskriterium:** ALICE extrahiert Tasks aus Gespraechen, speichert Wissen und plant den Tag

Umfang:
- Task CRUD + Task Screen
- Second Brain mit Embedding-Pipeline + RAG-Suche
- CrewAI Multi-Agent Integration
- Mentioned-Items-Extraktion aus Chat
- Proaktive Jobs (Daily Planning, Follow-Up, Deadline Monitor)
- Push Notifications
- Personality Engine (anpassbare KI-Persoenlichkeit)

### Phase 3: ADHS-Modus
**Ziel:** Spezialisierte ADHS-Features
**Erfolgskriterium:** Gamification aktiv, Nudge-System eskaliert korrekt, Tasks werden automatisch aufgeteilt

Umfang:
- Erweiterte proaktive Jobs mit Nudge-Eskalation
- Task-Breakdown (KI zerlegt grosse Tasks)
- Gamification (XP, Level, Streaks, Achievements)
- ADHS-Dashboard mit Tagesuebersicht
- Plugin-System (Base-Klasse, Registry, Store)
- Erweiterter Personality Editor

### Phase 4: Polish & Extras
**Ziel:** Voice-Integration, Plugins und Release-Qualitaet
**Erfolgskriterium:** App Store ready mit Voice, Plugins und Offline-Faehigkeit

Umfang:
- Voice-Integration (LiveKit + Deepgram + ElevenLabs)
- Google Calendar Plugin
- n8n Bridge Plugin
- Voice Journal Plugin
- Content Ingestion (URLs, Dateien)
- Dark/Light Mode
- Offline-Queue
- Performance-Optimierung
- App Store Vorbereitung

---

## 5. Kernprinzipien

1. **Proaktivitaet ist das Killerfeature** -- ALICE soll NICHT nur reagieren, sondern agieren
2. **Voice-First** -- Jede Funktion muss per Voice nutzbar sein
3. **ADHS-gerecht** -- Kurze Interaktionen, klare Struktur, positive Verstaerkung
4. **Privacy by Design** -- Lokale Verarbeitung wo moeglich, DSGVO-konform
5. **Erweiterbar** -- Plugin-System fuer Community-Erweiterungen

---

## 6. Nicht-funktionale Anforderungen (Uebersicht)

- **Performance:** Chat-Antwort < 2s (first token), App-Start < 3s
- **Sicherheit:** DSGVO-konform, Daten verschluesselt at rest + in transit
- **Verfuegbarkeit:** 99.5% Uptime
- **Skalierbarkeit:** Bis 10.000 User ohne Architektur-Aenderung
- **Barrierefreiheit:** WCAG 2.1 AA (soweit auf Mobile anwendbar)

---

## 7. Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|---|---|---|---|
| LLM-Kosten zu hoch | Mittel | Hoch | Caching, kleinere Modelle fuer einfache Tasks |
| Voice-Latenz zu hoch | Mittel | Hoch | LiveKit Self-Hosted, Edge-Optimierung |
| ADHS-User vergessen App zu nutzen | Hoch | Kritisch | Proaktive Push-Notifications, Habit-Building |
| Datenschutz-Bedenken | Mittel | Hoch | Transparente Datenverarbeitung, lokale Option |
| Expo-Limitierungen | Niedrig | Mittel | Eject-Option vorbereiten |

---

## 8. Abhaengigkeiten

- Anthropic Claude API Key
- OpenAI API Key (Fallback)
- Deepgram API Key (Voice STT)
- ElevenLabs API Key (Voice TTS)
- Hostinger VPS mit Docker + Coolify
- Google Cloud Console (Calendar API, FCM)
- Apple Developer Account (Push + App Store)
- Google Play Developer Account

---

## 9. API-Endpunkte (Uebersicht)

| Bereich | Endpoints |
|---|---|
| Auth | register, login, refresh, logout, me |
| Chat | message (streaming), history, WebSocket |
| Tasks | CRUD, complete (+XP), breakdown, today |
| Brain | entries CRUD, search (RAG), ingest |
| Calendar | events, sync |
| Proactive | mentioned-items, daily-plan, settings, snooze |
| Gamification | stats, history |
| Personality | profiles CRUD, traits, rules, voice, activate, templates, preview |
| Plugins | list, install, uninstall, settings, auth, webhook |

---

## 10. Datenbank-Tabellen (Uebersicht)

users, tasks, brain_entries, brain_embeddings, mentioned_items, conversations, messages, calendar_events, user_stats, notification_log, personality_profiles, personality_templates, user_plugins, plugin_data, achievements, user_achievements, xp_history
