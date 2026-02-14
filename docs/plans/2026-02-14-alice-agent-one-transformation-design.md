# ALICE — Agent One Transformation Design

> **A.L.I.C.E. = Adaptive Living Intelligence for Coaching & Evolution**

**Decision:** Agent One and ALICE ADHS-Coach werden zu EINER App zusammengefuehrt. ADHS ist ein togglebares Coaching-Modul. Alice ist der einheitliche Produktname, das Aktivierungswort ("Hey Alice") und das Akronym.

**Datum:** 2026-02-14
**Status:** Approved
**Autor:** Team Lead + User

---

## 1. Vision

Alice ist ein proaktiver, persoenlicher KI-Coach der sich an die Beduerfnisse des Users anpasst. ADHS-Coaching ist das erste und staerkste Modul, aber die Plattform waechst zu einem vollstaendigen KI-Assistenten mit Email-, Kalender-, CRM-Integration und autonomer Aufgabenausfuehrung.

**Kernprinzip:** Alice erinnert sich (Graphiti), lernt dazu (Self-Evolution), handelt proaktiv (Ambient Agent) und speichert keine Kundendaten (Zero-Data-Retention).

---

## 2. Modul-System

### 2.1 Architektur: Feature-Flag-basiert

Erweitert das bestehende `UserSettings.settings` JSONB:

```json
{
  "active_modules": ["core", "adhs", "wellness", "productivity"],
  "module_configs": {
    "adhs": {
      "nudge_intensity": "medium",
      "auto_breakdown": true,
      "pattern_tracking": true
    },
    "wellness": {
      "guardian_angel_enabled": true,
      "briefing_time": "07:00",
      "wellbeing_check_interval_hours": 4
    },
    "productivity": {
      "morning_briefing": true,
      "adaptive_planning": true,
      "max_daily_tasks": 3
    }
  }
}
```

### 2.2 Verfuegbare Module

| Modul | Beschreibung | Status |
|-------|-------------|--------|
| **core** | Chat, Brain, Tasks, Personality, Auth | Immer aktiv |
| **adhs** | Pattern-Erkennung, Nudges, Task-Breakdown, Gamification | Vorhanden (Phase 1-5) |
| **wellness** | Guardian Angel, Wellbeing Score, Schlaf/Energie-Tracking | Milestone 2 |
| **productivity** | Morning Briefing, Adaptive Tagesplanung, Focus Timer | Milestone 3 |
| **integrations** | Calendar, Email, Webhooks, n8n Bridge | Milestone 5 |
| **business** | MCP Connectors, Trust Scores, Approval Gates, Multi-Tenant | Milestone 6 |
| **evolution** | Self-Evolution, Prompt Versioning, World Model | Milestone 7 |

### 2.3 Onboarding Flow

1. Registration (wie bisher)
2. NEU: Modul-Auswahl Screen ("Was soll Alice fuer dich tun?")
3. Pro aktiviertem Modul: Spezifische Onboarding-Fragen
4. ADHS-Modul: Bisherige ADHS-Onboarding-Fragen
5. Wellness-Modul: Schlafzeiten, Energiemuster
6. Productivity: Arbeitszeiten, Prioritaeten

### 2.4 UI-Auswirkung

- Tab-Bar zeigt nur Tabs fuer aktive Module
- Settings Screen zeigt Modul-Management
- Inaktive Module sind komplett unsichtbar
- Module koennen jederzeit an/aus geschaltet werden

---

## 3. Guardian Angel (Wellness-Modul)

### 3.1 Wellbeing Score

Aggregiert alle verfuegbaren Signale zu einem Score 0-100:

```
wellbeing_score = weighted_average(
    mood_trend_7d      * 0.25,  // Stimmungsverlauf
    energy_trend_7d    * 0.20,  // Energieverlauf
    focus_trend_7d     * 0.15,  // Fokusverlauf
    task_completion_7d * 0.15,  // Aufgaben-Erledigungsrate
    sleep_pattern      * 0.10,  // Schlafmuster (Chat-Analyse)
    social_activity    * 0.10,  // Soziale Aktivitaet (Chat-Analyse)
    streak_health      * 0.05,  // Gamification-Streak
)
```

Zonen: 0-30 (rot/kritisch), 30-60 (gelb/Achtung), 60-100 (gruen/gut)

### 3.2 ADHS-spezifische Interventionen

| Pattern | Signal | Prediction | Intervention |
|---------|--------|------------|--------------|
| Hyperfocus | Focus > 0.9 fuer > 2h | Echtzeit | "Du bist deep drin - denk an Pause" |
| Procrastination Spiral | Task-Completion sinkt + Energy sinkt | 1-2 Tage vorher | "Lass uns die Aufgabe kleiner machen" |
| Decision Fatigue | Viele offene Tasks + Focus sinkt | Echtzeit | "Zu viele Optionen? Fokus auf DIESE eine" |
| Transition Difficulty | Kontextwechsel noetig | Echtzeit | "Gleich Wechsel - 2 Min Pause?" |
| Energy Crash | Energy sinkt 3 Tage hintereinander | 1-2 Tage vorher | Leichtere Tasks vorschlagen |
| Sleep Disruption | Spaete Nutzung + niedrige Morning-Energy | Muster erkannt | Quiet-Hours Vorschlag |
| Social Masking | Hohe Produktivitaet + sinkende Mood | Muster erkannt | Self-Care Vorschlag |

### 3.3 Backend

- `WellbeingService`: Score-Berechnung aus bestehenden Daten
- `WellbeingScore` Model: user_id, score, components (JSONB), calculated_at
- `Intervention` Model: user_id, type, trigger, message, status (pending/dismissed/acted)
- Cron Job: Alle 4 Stunden + nach jeder Chat-Session
- API: `GET /wellbeing/score`, `GET /wellbeing/history`, `GET /wellbeing/interventions`, `POST /wellbeing/intervention/{id}/dismiss`

### 3.4 Expo Screen

- Activity-Rings-Style Wellbeing Score Widget
- 7-Tage Trend Chart (Mood/Energy/Focus)
- Aktive Interventionen mit Dismiss/Snooze/Act
- Woechentlicher Check-in Report

---

## 4. Morning Briefing (Productivity-Modul)

### 4.1 Briefing-Generierung

Automatisch generiert via LLM mit Graphiti-Kontext:

```
Guten Morgen [Name]!

Wellbeing Score: 72/100 (Trend: +3)
Energie-Peak: voraussichtlich 10:00-12:00

Dein Tag:
  1. [Wichtigste Aufgabe] - mach das im Energie-Peak
  2. [Zweitwichtigste]
  3. [Rest kann warten]

Tipp: [Basierend auf Pattern-Analyse]

Alice erinnert sich: [Fakt aus Graphiti]
```

### 4.2 ADHS-Erweiterungen

- Max 3 Aufgaben anzeigen (Overwhelm vermeiden)
- Aufgaben nach Energie-Level priorisiert (nicht nach Deadline)
- "Brain Dump" Button fuer schnelles Gedanken-Capturen
- Swipeable Cards (links=skip, rechts=accept)

### 4.3 Backend

- `BriefingService`: LLM + Graphiti + Tasks + Wellbeing
- `Briefing` Model: user_id, date, content, tasks_suggested (JSONB), read_at
- Cron Job: Generierung um konfigurierbare `briefing_time`
- Push Notification: "Dein Morning Briefing ist fertig"
- API: `GET /briefings/today`, `GET /briefings/history`

### 4.4 Expo Screen

- Erster Screen bei App-Start (wenn aktiviert)
- Swipeable Task Cards
- Brain Dump Quick-Input
- "Jetzt nicht" Button (Briefing spaeter lesen)

---

## 5. Predictive Pattern Engine

### 5.1 Regelbasierte Prediction (MVP)

Nutzt Graphiti temporale Daten + PatternAnalyzer Sliding Windows:

- 7-Tage und 30-Tage Trends auf mood/energy/focus
- Regelbasierte Erkennung (kein ML fuer MVP)
- Predictions als `PredictedPattern` in DB gespeichert
- Push Notification bei High-Confidence Predictions

### 5.2 Spaetere Phase: ML-basiert

- Fine-tuned Model auf anonymisierten Pattern-Daten
- Personalisierte Schwellenwerte statt globale Regeln
- Confidence Scores fuer Predictions

---

## 6. Essential Integrations (Milestone 5)

### 6.1 Calendar Integration

- Google Calendar API (OAuth 2.0, Read/Write)
- Apple Calendar API (EventKit via Expo)
- Termine in Morning Briefing einbinden
- Termin-Erinnerungen via Push
- Kontextbasierte Erinnerungen ("Du hast in 30min einen Termin")

### 6.2 Smart Reminder System

- Zeitbasierte Erinnerungen (Cron)
- Kontextbasierte Erinnerungen (aus Chat extrahiert)
- Ortsbasierte Erinnerungen (optional, GPS)
- Push Notification Queue mit Priority-System
- Wiederkehrende Erinnerungen

### 6.3 Basic Webhook/Integration Layer

- Incoming Webhooks (externe Trigger -> Alice Aktionen)
- Outgoing Webhooks (Alice Events -> externe Services)
- n8n Bridge Foundation (n8n Workflows als Agent-Tools)

---

## 7. Vollstaendiger Milestone-Plan (Alle Agent One Features)

### Milestone 1: Foundation & Module System
**Scope: Rebranding + Modul-Architektur**

- [ ] Module System in UserSettings (active_modules, module_configs)
- [ ] Module Selection Onboarding Screen
- [ ] Dynamic Tab-Bar basierend auf aktiven Modulen
- [ ] Settings Screen fuer Module-Management (an/aus Toggle)
- [ ] API: `GET/PUT /settings/modules`
- [ ] ARCHITECTURE.md Update fuer Alice
- [ ] Linear Project + Milestones + Epics + Tasks komplett

### Milestone 2: Guardian Angel & Wellness Module
**Scope: Wellbeing Score + ADHS Interventionen**

- [ ] `WellbeingScore` DB Model + Migration
- [ ] `Intervention` DB Model + Migration
- [ ] `WellbeingService` mit Score-Berechnung
- [ ] Intervention Engine (7 ADHS-Pattern)
- [ ] Cron Job: Periodische Score-Berechnung
- [ ] API Endpoints: score, history, interventions
- [ ] Expo: Wellbeing Dashboard Screen
- [ ] Expo: Activity-Rings Score Widget
- [ ] Expo: 7d Trend Chart
- [ ] Expo: Intervention Cards (dismiss/snooze/act)
- [ ] Push Notifications fuer kritische Interventionen

### Milestone 3: Morning Briefing & Adaptive Planning
**Scope: Taegliches Briefing + Smart Task Management**

- [ ] `Briefing` DB Model + Migration
- [ ] `BriefingService` mit LLM-Generierung
- [ ] Graphiti-Context fuer Briefing-Personalisierung
- [ ] Cron Job: Briefing-Generierung um konfigurierbare Zeit
- [ ] Push Notification: "Briefing ist fertig"
- [ ] Energie-basierte Task-Priorisierung
- [ ] Max-3-Tasks Regel (ADHS-Modul)
- [ ] Brain Dump Quick-Capture Feature
- [ ] API: briefings/today, briefings/history
- [ ] Expo: Briefing Screen (erster Tab wenn aktiviert)
- [ ] Expo: Swipeable Task Cards
- [ ] Expo: Brain Dump Input

### Milestone 4: Predictive Pattern Engine
**Scope: Vorhersage statt nur Analyse**

- [ ] `PredictedPattern` DB Model
- [ ] Prediction Rules Engine (7 Pattern-Typen)
- [ ] Sliding Window Trend-Analyse (7d, 30d)
- [ ] Graphiti temporale Queries fuer Predictions
- [ ] Confidence Scoring fuer Predictions
- [ ] Push Notifications bei High-Confidence Predictions
- [ ] API: predictions/active, predictions/history
- [ ] Expo: Pattern Insights Screen
- [ ] Expo: Prediction Notification Cards

### Milestone 5: Essential Integrations
**Scope: Calendar + Reminders + Webhooks**

- [ ] Google Calendar OAuth 2.0 Integration (Read/Write)
- [ ] Apple Calendar Integration (EventKit via Expo)
- [ ] Calendar-Daten in Morning Briefing einbinden
- [ ] Termin-Erinnerungen via Push
- [ ] Smart Reminder System (zeit-/kontextbasiert)
- [ ] Wiederkehrende Erinnerungen
- [ ] Push Notification Queue mit Priority
- [ ] Incoming Webhooks Endpoint
- [ ] Outgoing Webhooks System
- [ ] n8n Bridge Foundation (Workflow -> MCP Tool)
- [ ] Expo: Calendar View Screen
- [ ] Expo: Reminder Management

### Milestone 6: Multi-Agent & Trust System (Agent One Level 1-3)
**Scope: LangGraph Supervisor + Progressive Autonomie**

- [ ] LangGraph Supervisor Agent
- [ ] Subagent-as-Tool Pattern Implementation
- [ ] Email Sub-Agent (Read/Summarize/Draft)
- [ ] Calendar Sub-Agent (Scheduling/Conflict Resolution)
- [ ] Research Sub-Agent (Web Search/Summarize)
- [ ] Briefing Sub-Agent (Morning Briefing Generation)
- [ ] `TrustScore` DB Model + Migration
- [ ] Trust Score Berechnung (per Action Type)
- [ ] Progressive Autonomy Engine
- [ ] Approval Gates (LangGraph `interrupt()`)
- [ ] Approval Queue API + UI
- [ ] Expo: Approval Swipe-to-Approve
- [ ] Agent Activity Feed (SSE)
- [ ] Reflexion Framework (lernen aus Fehlern)

### Milestone 7: DSGVO & Security Hardening (Agent One Level 2)
**Scope: Enterprise-taugliche Sicherheit**

- [ ] Multi-Tenant Data Isolation (4 Schichten)
- [ ] Graphiti group_id Namespace-Isolation
- [ ] PostgreSQL Row-Level Security
- [ ] Envelope Encryption (Tenant-spezifische Keys)
- [ ] HashiCorp Vault Integration (Secrets Management)
- [ ] OAuth Token Management via Vault
- [ ] Immutable Audit Trails (kryptographische Verkettung)
- [ ] OpenTelemetry Instrumentation
- [ ] Langfuse Self-hosted (Agent Observability)
- [ ] DSGVO Art. 30 Audit-Export API
- [ ] PII-Filter (Microsoft Presidio) vor Knowledge Graph
- [ ] BSI Grundschutz++ Stufe 2 Compliance
- [ ] AVV/DPA Templates fuer Kunden
- [ ] DSFA (Datenschutz-Folgenabschaetzung) Dokument

### Milestone 8: MCP Connector Gateway (Agent One Level 4)
**Scope: Universelle Tool-Anbindung**

- [ ] MCP Gateway (Auth, Rate Limiting, PII-Filter, Audit)
- [ ] MCP Server Registry
- [ ] Gmail MCP Connector
- [ ] Google Calendar MCP Connector
- [ ] HubSpot CRM MCP Connector
- [ ] DATEV MCP Connector
- [ ] n8n MCP Bridge (n8n Workflows als MCP Tools)
- [ ] HTTP Universal Connector (No-Code API-Anbindung)
- [ ] MCP Permission Model (Least Privilege)
- [ ] Connector Configuration UI (Dashboard)
- [ ] Connector SDK (Python + TypeScript)
- [ ] A2A Protocol Readiness

### Milestone 9: Data Sovereignty & Deployment (Agent One Level 4)
**Scope: 3 Deployment-Modelle**

- [ ] Zero-Data-Retention Policy (technisch + juristisch)
- [ ] Modell A: Full Cloud SaaS (Hetzner, Multi-Tenant)
- [ ] Modell B: Hybrid (Intelligence Cloud, Data beim Kunden)
- [ ] Modell B: Kunden-Docker-Stack (vorkonfiguriertes Image)
- [ ] Modell B: Anonymisierungs-Pipeline (Presidio)
- [ ] Modell B: mTLS Agent-Gateway
- [ ] Modell B: Auto-Update System
- [ ] Modell C: Full On-Premise Package
- [ ] Setup-Wizard UI fuer Deployment-Auswahl
- [ ] Dokumentation: Deployment-Guide pro Modell

### Milestone 10: Cost Optimization (Agent One Level 2)
**Scope: 75-95% Kostensenkung**

- [ ] Semantic Cache (Redis + Embeddings, Cosine Similarity)
- [ ] Provider-Level Prompt Caching (Anthropic + OpenAI)
- [ ] LangGraph Node-Level Caching
- [ ] RouteLLM Integration (Smart Model Routing)
- [ ] Batch API Processing fuer nicht-dringende Arbeit
- [ ] LiteLLM Gateway (LLM Failover, Load Balancing)
- [ ] Cost Dashboard (pro Tenant, pro Agent, pro Modell)
- [ ] Token Usage Analytics

### Milestone 11: Self-Evolution & World Model (Agent One Level 5)
**Scope: Der lebendige Agent**

- [ ] Nightly Reflection Agent (analysiert Tagesleistung)
- [ ] Prompt Versioning System
- [ ] A/B Testing fuer Prompts
- [ ] Skill Library (gelernte Faehigkeiten)
- [ ] `PromptVersion` DB Model
- [ ] `LearnedSkill` DB Model
- [ ] Business World Model (Counterfactual Reasoning)
- [ ] "Was waere wenn" Simulationen auf temporalen Daten
- [ ] Guardian Angel: Adaptive Load Balancing
- [ ] Self-Improvement Metrics Dashboard
- [ ] Evolution Timeline Visualization

### Milestone 12: Enterprise Dashboard (Agent One Level 2)
**Scope: Next.js Admin + Customer Dashboard**

- [ ] Next.js 15 Dashboard Application
- [ ] Admin Dashboard (HR Code Labs intern)
- [ ] Customer Dashboard (KMU-Mandant)
- [ ] Subdomain-basiertes Tenant Routing
- [ ] White-Label System (Logo, Farben, Branding)
- [ ] Knowledge Graph Browser (Cytoscape.js)
- [ ] Agent Activity Monitor
- [ ] Approval Queue UI
- [ ] Usage Analytics + Cost Dashboard
- [ ] Audit Trail Viewer
- [ ] Connector Management UI

### Milestone 13: Voice & Wake Word
**Scope: "Hey Alice" + erweiterte Voice**

- [ ] Picovoice Porcupine Wake Word ("Alice")
- [ ] Expo Custom Dev Client (fuer Native Module)
- [ ] Background Wake Word Detection (Android)
- [ ] Foreground Wake Word Detection (iOS)
- [ ] Continuous Voice Conversation Mode
- [ ] Voice-gesteuerte Task-Erstellung
- [ ] Voice-gesteuerte Briefing-Navigation
- [ ] Vapi Integration fuer Telefon-Agent (Enterprise)

### Milestone 14: Secure Marketplace
**Scope: Connector + Skill Marketplace**

- [ ] Connector Marketplace UI
- [ ] Mandatory Code Scanning bei Veroeffentlichung
- [ ] Kryptographische Signierung (Publisher-Verifikation)
- [ ] Sandboxed Execution (gVisor)
- [ ] Deklaratives Permission Model
- [ ] Review Pipeline (automatisch + manuell)
- [ ] Community Connector Submission
- [ ] Branchenspezifische Connectors (Praxis, Anwalt, Handwerk)

---

## 8. Tech Stack

### Bestehend (bleibt):
- **Backend:** Python + FastAPI
- **Mobile:** Expo SDK 52+ (React Native)
- **DB:** PostgreSQL + SQLAlchemy
- **Knowledge Graph:** Graphiti + FalkorDB
- **Voice:** Deepgram (STT) + ElevenLabs (TTS)
- **Auth:** JWT-basiert

### Neu (wird hinzugefuegt):
- **Multi-Agent:** LangGraph (ab Milestone 6)
- **LLM Gateway:** LiteLLM (ab Milestone 10)
- **Observability:** Langfuse self-hosted (ab Milestone 7)
- **Secrets:** HashiCorp Vault (ab Milestone 7)
- **PII Filter:** Microsoft Presidio (ab Milestone 7)
- **Caching:** Redis + RouteLLM (ab Milestone 10)
- **Dashboard:** Next.js 15 + shadcn/ui (ab Milestone 12)
- **Wake Word:** Picovoice Porcupine (ab Milestone 13)
- **Connectors:** MCP Protocol (ab Milestone 8)
- **Workflows:** n8n Bridge (ab Milestone 8)
- **Container Isolation:** gVisor (ab Milestone 14)

---

## 9. Datenfluss-Prinzip

```
User Input (Chat/Voice/Gesture)
       |
       v
Alice Core Engine (FastAPI + AI Service)
       |
       +---> Graphiti Knowledge Graph (temporale Fakten, KEINE Rohdaten)
       |
       +---> PatternAnalyzer (NLP Scores: mood/energy/focus)
       |
       +---> WellbeingService (aggregierter Score)
       |
       +---> BriefingService (taegliches Briefing)
       |
       +---> PredictionEngine (Muster-Vorhersage)
       |
       +---> (Future) LangGraph Supervisor -> Sub-Agents -> MCP Tools
       |
       v
Response (Chat/Voice/Push/Briefing/Intervention)
```

**Zero-Data-Retention:** Alice speichert abstrahierte Fakten im Knowledge Graph, KEINE Rohdaten (Emails, Dokumente, Kalender). PII wird vor Speicherung gefiltert (Presidio).

---

## 10. Alice Akronym-Bedeutung

**A** - Adaptive (Module System, passt sich an User-Beduerfnisse an)
**L** - Living (Lebendiger Agent, Self-Evolution, waechst mit dem User)
**I** - Intelligence (KI-Kern, temporaler Knowledge Graph)
**C** - Coaching (Persoenlicher Coach als Kernidentitaet)
**E** - Evolution (Self-Evolution, lernt und verbessert sich staendig)

**Aktivierungswort:** "Hey Alice" (Picovoice Porcupine, Milestone 13)

---

## 11. Referenz-Dokumente

Alle Agent One Architektur-Level sind vollstaendig abgedeckt:

| Agent One Level | Milestone(s) | Status |
|----------------|-------------|--------|
| Level 1: Foundation | Besteht bereits (FastAPI+Graphiti+FalkorDB) | Teilweise implementiert |
| Level 2: Security | M7 (DSGVO), M10 (Caching), M12 (Dashboard) | Geplant |
| Level 3: Ambient Agent | M2 (Guardian Angel), M3 (Briefing), M6 (Multi-Agent) | Naechste Phase |
| Level 4: Zero-Data | M5 (Integrations), M8 (MCP), M9 (Deployment) | Geplant |
| Level 5: Living Agent | M11 (Self-Evolution), M13 (Wake Word) | Spaetere Phase |

**Quelldokumente:**
- `agent-one-ausarbeitung/agent-one-projektbeschreibung.md`
- `agent-one-ausarbeitung/agent-one-prd.md`
- `agent-one-ausarbeitung/level2-architektur-agent-one.md`
- `agent-one-ausarbeitung/level3-architektur-agent-one.md`
- `agent-one-ausarbeitung/level4-architektur-agent-one.md`
- `agent-one-ausarbeitung/level5-architektur-agent-one.md`
