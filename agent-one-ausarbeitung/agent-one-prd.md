# AGENT ONE — Complete Project Requirements Document (PRD)
## For Claude Code Implementation

**Version:** 1.0
**Date:** 12. Februar 2026
**Author:** HR Code Labs GbR (Oliver Hees & Alina Rosenbusch)
**Status:** Architecture Complete — Ready for Implementation

---

## INHALTSVERZEICHNIS

1. [Projekt-Übersicht & Vision](#1-projekt-übersicht--vision)
2. [Tech Stack](#2-tech-stack)
3. [Architektur-Übersicht (5 Level)](#3-architektur-übersicht)
4. [Monorepo-Struktur](#4-monorepo-struktur)
5. [Backend: FastAPI + LangGraph](#5-backend-fastapi--langgraph)
6. [Frontend: Next.js Dashboard](#6-frontend-nextjs-dashboard)
7. [Mobile App: Expo / React Native](#7-mobile-app-expo--react-native)
8. [Datenbank-Schemas](#8-datenbank-schemas)
9. [Knowledge Graph: Graphiti + FalkorDB](#9-knowledge-graph-graphiti--falkordb)
10. [Agent-System: LangGraph Multi-Agent](#10-agent-system-langgraph-multi-agent)
11. [Security & Auth](#11-security--auth)
12. [Caching & Kostenoptimierung](#12-caching--kostenoptimierung)
13. [MCP Gateway & Connectors](#13-mcp-gateway--connectors)
14. [n8n Orchestration Bridge](#14-n8n-orchestration-bridge)
15. [Voice System](#15-voice-system)
16. [Push Notifications & Event System](#16-push-notifications--event-system)
17. [Self-Evolution Engine (Level 5)](#17-self-evolution-engine)
18. [World Model Engine (Level 5)](#18-world-model-engine)
19. [Guardian Angel (Level 5)](#19-guardian-angel)
20. [Deployment & Infrastructure](#20-deployment--infrastructure)
21. [Environment Variables](#21-environment-variables)
22. [API-Referenz](#22-api-referenz)
23. [Implementierungs-Phasen](#23-implementierungs-phasen)

---

# 1. PROJEKT-ÜBERSICHT & VISION

## 1.1 Was ist Agent One?

Agent One ist ein proaktiver KI-Mitarbeiter für deutsche KMUs — insbesondere für Freiberufler und Berufsgeheimnisträger nach §203 StGB (Steuerberater, Anwälte, Ärzte). Er arbeitet 24/7 im Hintergrund, überwacht E-Mails, Kalender, Fristen und Kommunikation, handelt proaktiv, verdient sich schrittweise mehr Autonomie durch nachweisbare Zuverlässigkeit, und wird mit jeder Interaktion besser.

## 1.2 Die Fünf Architektur-Level

| Level | Name | Kernfunktion |
|-------|------|-------------|
| **1** | Das Fundament | Tech Stack, Knowledge Graph, Multi-Agent-System |
| **2** | Die Festung | DSGVO, Multi-Tenant, Caching, RouteLLM, Dashboard |
| **3** | Der Ambient Agent | Proaktivität, Trust Scores, Expo App, Voice, On-Device AI |
| **4** | Zero-Data-Architektur | Deployment-Modelle, MCP Connectors, n8n Bridge |
| **5** | Der Lebendige Agent | Selbstevolution, Weltmodell, Guardian Angel |

## 1.3 Kern-Prinzipien

- **DSGVO-by-Design**: Jede Architekturentscheidung priorisiert Datenschutz
- **Zero-Data-Retention**: Agent speichert KEINE Kundendaten — nur abstrahierte Fakten im Knowledge Graph
- **Progressive Autonomie**: Agent verdient sich Freiheit durch nachweisbare Zuverlässigkeit
- **Sustainable Performance**: Agent optimiert nicht nur Business, sondern auch Nutzer-Wohlbefinden
- **German-First**: Alles auf deutschen Servern, deutsche Sprache, deutsche Compliance

## 1.4 Zielgruppen & Deployment-Modelle

| Modell | Zielgruppe | Preis | Setup |
|--------|-----------|-------|-------|
| **A: Full Cloud SaaS** | 80% der KMUs (Coaches, Berater, Freelancer) | €149-299/Mo | Minuten |
| **B: Hybrid** | §203-Berufe (Steuerberater, Anwälte, Ärzte) | €299-499/Mo | 2-4 Stunden |
| **C: Full On-Premise** | Kliniken, Behörden, Enterprise | €999+/Mo | Tage |
| **Level 5 Premium** | Alle Modelle mit Selbstevolution + Guardian Angel | €499-999/Mo | Wie Basismodell |

---

# 2. TECH STACK

## 2.1 Backend

| Komponente | Technologie | Version | Zweck |
|-----------|------------|---------|-------|
| **Runtime** | Python | 3.11+ | Backend-Sprache |
| **API Framework** | FastAPI | 0.110+ | REST + WebSocket API |
| **Agent Framework** | LangGraph | 1.0+ | Multi-Agent Orchestrierung, Cron Jobs, Checkpointing |
| **Knowledge Graph** | Graphiti | latest | Temporaler Knowledge Graph mit bi-temporalen Fakten |
| **Graph Database** | FalkorDB | latest | Sub-10ms Graph Queries, 10.000+ Tenants pro Instanz |
| **Relational DB** | PostgreSQL | 16+ | Nutzer, Tenants, Billing, Audit Logs |
| **Cache** | Redis | 7+ | Semantisches Caching, Pub/Sub, Session Store |
| **LLM Gateway** | LiteLLM | latest | Einheitliche API für 100+ Modelle, Failover, Rate Limits |
| **LLM Router** | RouteLLM | latest | 95% GPT-4-Qualität bei 14-26% der Kosten |
| **Observability** | Langfuse | latest (self-hosted) | Agent Tracing, Performance Monitoring, A/B Testing |
| **Secrets** | HashiCorp Vault | latest | OAuth Tokens, API Keys, Encryption Keys |
| **PII Filter** | Microsoft Presidio | latest | PII-Erkennung vor Knowledge Graph Speicherung |
| **Task Queue** | Celery + Redis | latest | Background Jobs, Nightly Reflection |

## 2.2 Frontend (Dashboard)

| Komponente | Technologie | Version | Zweck |
|-----------|------------|---------|-------|
| **Framework** | Next.js | 14+ (App Router) | Dashboard mit SSR |
| **Sprache** | TypeScript | 5+ | Type Safety |
| **UI Library** | shadcn/ui | latest | Konsistente UI-Komponenten |
| **Styling** | Tailwind CSS | 3+ | Utility-First CSS |
| **Charts** | Recharts | latest | Agent Performance Visualisierung |
| **Graph Viz** | Cytoscape.js | latest | Knowledge Graph Visualisierung |
| **Real-time** | Socket.IO | latest | Live Agent Updates |
| **Auth** | NextAuth.js | 5+ | OAuth 2.0 + JWT |
| **Forms** | React Hook Form + Zod | latest | Validierte Formulare |
| **State** | Zustand | latest | Client State Management |

## 2.3 Mobile App

| Komponente | Technologie | Version | Zweck |
|-----------|------------|---------|-------|
| **Framework** | Expo | SDK 52+ | Managed Workflow + Custom Dev Client |
| **Sprache** | TypeScript | 5+ | Type Safety |
| **Navigation** | Expo Router | latest | File-based Routing |
| **Push** | expo-notifications | latest | Push Notifications |
| **Biometrie** | expo-local-authentication | latest | Face ID / Fingerprint |
| **Kamera** | expo-camera + expo-image-picker | latest | Dokument-Scanner |
| **Storage** | expo-secure-store | latest | Sichere Token-Speicherung |
| **Voice STT** | Deepgram | latest | Speech-to-Text (exzellentes Deutsch) |
| **Voice TTS** | ElevenLabs | latest | Text-to-Speech (natürliches Deutsch) |
| **On-Device AI** | react-native-executorch | latest | Llama 3.2 1B offline |
| **Streaming** | Vercel AI SDK | latest | SSE Streaming (`expo/fetch`) |

## 2.4 Infrastructure

| Komponente | Technologie | Zweck |
|-----------|------------|-------|
| **Hosting** | Hetzner Cloud (Nürnberg/Falkenstein) | ISO 27001, kein US CLOUD Act |
| **Container** | Docker + Docker Compose | Container-Orchestrierung |
| **Orchestration (Scale)** | k3s (Kubernetes) | Ab 500+ Kunden |
| **Reverse Proxy** | Traefik / Caddy | Auto-TLS, Subdomain Routing |
| **Monitoring** | Grafana + Loki + OpenTelemetry | System + Agent Monitoring |
| **CI/CD** | GitHub Actions | Automated Deployment |
| **PaaS (optional)** | Coolify | Self-hosted PaaS auf Hetzner |

## 2.5 Externe APIs

| API | Zweck | Fallback |
|-----|-------|---------|
| **Anthropic Claude** | Primäres LLM (Reasoning) | OpenAI GPT-4o |
| **OpenAI GPT-4o-mini** | Schnelle/günstige Tasks | Anthropic Claude Haiku |
| **Deepgram** | STT (Speech-to-Text) | Whisper (self-hosted) |
| **ElevenLabs** | TTS (Text-to-Speech) | — |
| **Vapi** | Telefon-Agent Integration | Sipgate + Custom |
| **Expo Push Service** | Push Notifications | — |
| **Hetzner Object Storage** | S3-kompatibel für Audit Logs | — |

---

# 3. ARCHITEKTUR-ÜBERSICHT

## 3.1 Gesamtarchitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                                                                     │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐     │
│  │ Expo App    │  │ Next.js Dashboard│  │ Telefon (Vapi)     │     │
│  │ iOS/Android │  │ Web              │  │ Voice Agent        │     │
│  │ Voice, Push │  │ Admin + Kunden   │  │ STT→Agent→TTS      │     │
│  └──────┬──────┘  └────────┬─────────┘  └─────────┬──────────┘     │
│         │                  │                       │               │
└─────────┼──────────────────┼───────────────────────┼───────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                                   │
│  FastAPI (REST + WebSocket + SSE)                                   │
│  ├── Auth Middleware (JWT + API Key)                                │
│  ├── Tenant Resolution (Subdomain → tenant_id)                     │
│  ├── Rate Limiting (per Tenant)                                    │
│  └── Request Logging (OpenTelemetry → Langfuse)                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     AGENT ORCHESTRATION LAYER                       │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐              │
│  │              LangGraph Supervisor                 │              │
│  │  Plan-and-Execute Reasoning                       │              │
│  │  Thread Management + Checkpointing                │              │
│  │  Cron Jobs (Morgen-Briefing, E-Mail Monitor,      │              │
│  │            Fristen-Wächter, Nightly Reflection)    │              │
│  └──────────────────┬───────────────────────────────┘              │
│                     │                                               │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ E-Mail  │ │Kalender │ │ Telefon  │ │ Fristen  │ │ Research │  │
│  │ Agent   │ │ Agent   │ │ Agent    │ │ Agent    │ │ Agent    │  │
│  └────┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │           │           │            │            │          │
│  ┌────▼───────────▼───────────▼────────────▼────────────▼────┐    │
│  │              Level 5 Engines                               │    │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐   │    │
│  │  │Self-Evolution│ │ World Model  │ │ Guardian Angel   │   │    │
│  │  │Metacognition │ │ Counterfact. │ │ Wellbeing Score  │   │    │
│  │  │Skill Library │ │ Simulation   │ │ Load Balancer    │   │    │
│  │  │Prompt Evol.  │ │ Risk Scoring │ │ Kalender-Schutz  │   │    │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘   │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                        DATA & INTELLIGENCE LAYER                    │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │
│  │ Graphiti +   │  │ PostgreSQL   │  │ Redis                │      │
│  │ FalkorDB     │  │ (Multi-Tenant│  │ (Semantic Cache +    │      │
│  │ (Knowledge   │  │  RLS +       │  │  Pub/Sub +           │      │
│  │  Graph,      │  │  Audit Logs) │  │  Session Store)      │      │
│  │  Temporal)   │  │              │  │                      │      │
│  └──────────────┘  └──────────────┘  └──────────────────────┘      │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │
│  │ LiteLLM      │  │ RouteLLM     │  │ Langfuse             │      │
│  │ (LLM Gateway │  │ (Smart       │  │ (Tracing +           │      │
│  │  + Failover) │  │  Routing)    │  │  Monitoring)         │      │
│  └──────────────┘  └──────────────┘  └──────────────────────┘      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ HashiCorp Vault (Secrets, OAuth Tokens, Encryption Keys) │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     MCP CONNECTOR LAYER                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    MCP Gateway                            │      │
│  │  OAuth 2.1 Auth │ Rate Limiting │ PII Filter (Presidio)  │      │
│  │  Audit Logging  │ Permission Scopes │ Schema Validation   │      │
│  └──────────────────────┬───────────────────────────────────┘      │
│                         │                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │ Gmail  │ │Google  │ │HubSpot │ │ DATEV  │ │  n8n   │          │
│  │ MCP    │ │Calendar│ │ MCP    │ │ MCP    │ │ Bridge │          │
│  │ Server │ │ MCP    │ │ Server │ │ Server │ │ (1200+ │          │
│  │        │ │ Server │ │        │ │        │ │ Integr)│          │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ HTTP Universal Connector — Jede API in 5 Min via UI      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 3.2 Data Flow Prinzip: Zero-Data-Retention

```
Kundendaten (Gmail, Kalender, CRM, DMS)
    │
    ▼
Agent LIEST Daten über MCP Connectors
    │
    ▼
PII Filter (Presidio) entfernt personenbezogene Daten
    │
    ▼
LangGraph Reasoning Engine DENKT und ENTSCHEIDET
    │
    ├──► Graphiti speichert NUR abstrahierte Fakten:
    │    ✓ "Mandant Müller bevorzugt informellen Ton"
    │    ✓ "USt-VA Frist: 31.03.2026"
    │    ✗ NICHT: E-Mail-Texte, Dokumente, Kundendaten
    │
    ▼
Agent SCHREIBT zurück in Kundensysteme über MCP Connectors
    │
    ▼
Keine Kundendaten verbleiben im Agent-System
```

---

# 4. MONOREPO-STRUKTUR

```
agent-one/
├── README.md
├── docker-compose.yml                    # Lokale Entwicklung
├── docker-compose.prod.yml               # Produktion (Model A: SaaS)
├── docker-compose.hybrid.yml             # Model B: Hybrid (Kunden-Stack)
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml                        # Tests + Linting
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── packages/
│   ├── shared/                           # Geteilte Types + Utils
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── tenant.ts
│   │   │   │   ├── agent.ts
│   │   │   │   ├── approval.ts
│   │   │   │   ├── wellbeing.ts
│   │   │   │   └── mcp.ts
│   │   │   └── utils/
│   │   │       ├── validation.ts
│   │   │       └── formatting.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── mcp-sdk/                          # MCP Connector SDK
│       ├── src/
│       │   ├── server.py
│       │   ├── gateway.py
│       │   ├── pii_filter.py
│       │   └── types.py
│       ├── pyproject.toml
│       └── README.md
│
├── backend/                              # Python Backend
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic/                          # DB Migrations
│   │   ├── alembic.ini
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI App Entry
│   │   ├── config.py                     # Pydantic Settings
│   │   │
│   │   ├── api/                          # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py               # Login, Register, OAuth
│   │   │   │   ├── agents.py             # Agent CRUD + Control
│   │   │   │   ├── approvals.py          # Approval Queue
│   │   │   │   ├── briefings.py          # Morning Briefing
│   │   │   │   ├── chat.py               # Chat + Streaming
│   │   │   │   ├── connectors.py         # MCP Connector Management
│   │   │   │   ├── dashboard.py          # Dashboard Data
│   │   │   │   ├── knowledge.py          # Knowledge Graph Queries
│   │   │   │   ├── notifications.py      # Push Notification Management
│   │   │   │   ├── tenants.py            # Tenant Management (Admin)
│   │   │   │   ├── voice.py              # Voice STT/TTS Endpoints
│   │   │   │   ├── wellbeing.py          # Guardian Angel Data
│   │   │   │   ├── evolution.py          # Self-Evolution Dashboard
│   │   │   │   └── webhooks.py           # Incoming Webhooks
│   │   │   └── deps.py                   # Shared Dependencies
│   │   │
│   │   ├── core/                         # Core Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py               # JWT, Hashing, Encryption
│   │   │   ├── tenant.py                 # Tenant Resolution + Isolation
│   │   │   ├── permissions.py            # RBAC + Feature Flags
│   │   │   └── audit.py                  # Audit Trail Logger
│   │   │
│   │   ├── models/                       # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Base Model mit tenant_id
│   │   │   ├── user.py
│   │   │   ├── tenant.py
│   │   │   ├── agent_action.py           # Jede Agent-Aktion
│   │   │   ├── approval.py               # Approval Queue Items
│   │   │   ├── trust_score.py            # Trust Scores pro Aktion
│   │   │   ├── skill.py                  # Gelernte Skills (Level 5)
│   │   │   ├── prompt_version.py         # Prompt-Versionierung
│   │   │   ├── wellbeing_score.py        # Wellbeing Tracking
│   │   │   ├── connector.py              # MCP Connector Configs
│   │   │   ├── notification.py           # Push Notification Log
│   │   │   └── audit_log.py              # Immutable Audit Trail
│   │   │
│   │   ├── services/                     # Business Services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── tenant_service.py
│   │   │   ├── approval_service.py
│   │   │   ├── trust_service.py          # Trust Score Berechnung
│   │   │   ├── notification_service.py   # Push via Expo
│   │   │   ├── voice_service.py          # Deepgram + ElevenLabs
│   │   │   ├── wellbeing_service.py      # Wellbeing Score Berechnung
│   │   │   ├── evolution_service.py      # Self-Evolution Logic
│   │   │   ├── world_model_service.py    # Business World Model
│   │   │   ├── pii_service.py            # Presidio PII Filter
│   │   │   └── vault_service.py          # HashiCorp Vault Client
│   │   │
│   │   ├── agents/                       # LangGraph Agent Definitions
│   │   │   ├── __init__.py
│   │   │   ├── supervisor.py             # Haupt-Supervisor Agent
│   │   │   ├── email_agent.py            # E-Mail Sub-Agent
│   │   │   ├── calendar_agent.py         # Kalender Sub-Agent
│   │   │   ├── phone_agent.py            # Telefon Sub-Agent
│   │   │   ├── deadline_agent.py         # Fristen-Wächter
│   │   │   ├── research_agent.py         # Research Sub-Agent
│   │   │   ├── briefing_agent.py         # Morgen-Briefing Generator
│   │   │   ├── reflection_agent.py       # Nightly Reflection (Level 5)
│   │   │   ├── world_model_agent.py      # Counterfactual Reasoning
│   │   │   ├── guardian_angel_agent.py   # Wellbeing Monitor
│   │   │   ├── tools/                    # Shared Agent Tools
│   │   │   │   ├── __init__.py
│   │   │   │   ├── graphiti_tools.py     # Knowledge Graph Read/Write
│   │   │   │   ├── approval_tools.py     # Request Human Approval
│   │   │   │   ├── notification_tools.py # Send Push Notifications
│   │   │   │   ├── mcp_tools.py          # MCP Connector Access
│   │   │   │   └── calendar_tools.py     # Calendar Operations
│   │   │   ├── prompts/                  # System Prompts (versioniert)
│   │   │   │   ├── supervisor.md
│   │   │   │   ├── email.md
│   │   │   │   ├── calendar.md
│   │   │   │   ├── phone.md
│   │   │   │   ├── briefing.md
│   │   │   │   └── reflection.md
│   │   │   └── cron_jobs.py              # Cron Job Definitions
│   │   │
│   │   ├── mcp/                          # MCP Gateway + Connectors
│   │   │   ├── __init__.py
│   │   │   ├── gateway.py                # MCP Gateway (Auth, Rate Limit, PII)
│   │   │   ├── registry.py               # Connector Registry
│   │   │   ├── connectors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── gmail.py              # Gmail MCP Server
│   │   │   │   ├── google_calendar.py    # Google Calendar MCP Server
│   │   │   │   ├── hubspot.py            # HubSpot CRM MCP Server
│   │   │   │   ├── datev.py              # DATEV MCP Server
│   │   │   │   ├── n8n_bridge.py         # n8n Workflow → MCP Tool
│   │   │   │   └── http_universal.py     # HTTP Universal Connector
│   │   │   └── schemas/
│   │   │       └── connector_config.py   # Connector Config Schemas
│   │   │
│   │   └── cache/                        # Caching Layer
│   │       ├── __init__.py
│   │       ├── semantic_cache.py         # Redis + Embeddings
│   │       ├── response_cache.py         # LangGraph Node Cache
│   │       └── route_llm.py             # RouteLLM Integration
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_agents/
│       ├── test_api/
│       ├── test_services/
│       └── test_mcp/
│
├── dashboard/                            # Next.js Frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── Dockerfile
│   ├── tailwind.config.ts
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                # Root Layout
│   │   │   ├── page.tsx                  # Landing / Login
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx            # Dashboard Layout (Sidebar)
│   │   │   │   ├── page.tsx              # Overview / Home
│   │   │   │   ├── chat/page.tsx         # Agent Chat
│   │   │   │   ├── approvals/page.tsx    # Approval Queue
│   │   │   │   ├── briefing/page.tsx     # Morning Briefing
│   │   │   │   ├── knowledge/page.tsx    # Knowledge Graph Browser
│   │   │   │   ├── connectors/page.tsx   # MCP Connector Management
│   │   │   │   ├── connectors/new/page.tsx # HTTP Universal Connector Setup
│   │   │   │   ├── settings/page.tsx     # Tenant Settings
│   │   │   │   ├── evolution/page.tsx    # Self-Evolution Dashboard (L5)
│   │   │   │   ├── wellbeing/page.tsx    # Guardian Angel Dashboard (L5)
│   │   │   │   ├── audit/page.tsx        # Audit Trail Viewer
│   │   │   │   └── analytics/page.tsx    # Usage Analytics
│   │   │   └── admin/                    # Admin Dashboard (HR Code Labs)
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       ├── tenants/page.tsx
│   │   │       ├── system/page.tsx
│   │   │       └── monitoring/page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                       # shadcn/ui Komponenten
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── TenantSwitcher.tsx
│   │   │   ├── agents/
│   │   │   │   ├── AgentChat.tsx         # Streaming Chat
│   │   │   │   ├── ApprovalCard.tsx      # Einzelne Genehmigung
│   │   │   │   ├── ApprovalQueue.tsx     # Genehmigungs-Liste
│   │   │   │   ├── BriefingView.tsx      # Morgen-Briefing
│   │   │   │   └── TrustScoreDisplay.tsx # Trust Score Visualisierung
│   │   │   ├── knowledge/
│   │   │   │   ├── GraphViewer.tsx       # Cytoscape.js Graph
│   │   │   │   └── EntityDetail.tsx      # Entity-Detail-View
│   │   │   ├── connectors/
│   │   │   │   ├── ConnectorCard.tsx
│   │   │   │   ├── ConnectorSetup.tsx    # OAuth Flow
│   │   │   │   └── UniversalConnectorForm.tsx # HTTP Connector Builder
│   │   │   ├── wellbeing/
│   │   │   │   ├── WellbeingScore.tsx    # Score Widget
│   │   │   │   ├── WorkPatternChart.tsx  # Arbeitsmuster
│   │   │   │   └── WeeklyReport.tsx      # Wochen-Check-in
│   │   │   └── evolution/
│   │   │       ├── SkillLibrary.tsx      # Gelernte Skills
│   │   │       ├── PromptHistory.tsx     # Prompt Versionen
│   │   │       └── EvolutionTimeline.tsx # Fortschritt über Zeit
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                    # API Client (fetch wrapper)
│   │   │   ├── auth.ts                   # Auth Utilities
│   │   │   ├── socket.ts                 # WebSocket Client
│   │   │   └── tenant.ts                 # Tenant Resolution
│   │   │
│   │   └── middleware.ts                 # Tenant + Auth Middleware
│   │
│   └── public/
│       └── branding/                     # White-Label Assets
│
├── mobile/                               # Expo App
│   ├── package.json
│   ├── app.json
│   ├── tsconfig.json
│   ├── eas.json                          # EAS Build Config
│   │
│   ├── app/
│   │   ├── _layout.tsx                   # Root Layout
│   │   ├── (auth)/
│   │   │   ├── login.tsx
│   │   │   └── biometric.tsx
│   │   ├── (tabs)/
│   │   │   ├── _layout.tsx               # Tab Navigation
│   │   │   ├── index.tsx                 # Briefing Screen
│   │   │   ├── inbox.tsx                 # Agent Inbox (Approvals)
│   │   │   ├── chat.tsx                  # Chat + Voice
│   │   │   ├── activity.tsx              # Activity Feed
│   │   │   └── settings.tsx              # Settings + Wellbeing
│   │   └── approval/[id].tsx             # Approval Detail (Deep Link)
│   │
│   ├── components/
│   │   ├── BriefingCard.tsx
│   │   ├── ApprovalSwipe.tsx             # Swipe-to-Approve
│   │   ├── VoiceButton.tsx               # Push-to-Talk
│   │   ├── VoiceChat.tsx                 # Voice Conversation
│   │   ├── DocumentScanner.tsx           # OCR Camera
│   │   ├── WellbeingWidget.tsx           # Wellbeing Score Compact
│   │   └── NotificationHandler.tsx       # Push Handler
│   │
│   ├── services/
│   │   ├── api.ts                        # API Client
│   │   ├── auth.ts                       # Secure Store + Biometric
│   │   ├── notifications.ts              # Expo Push Setup
│   │   ├── voice.ts                      # Deepgram STT + ElevenLabs TTS
│   │   └── offline.ts                    # ExecuTorch On-Device AI
│   │
│   └── hooks/
│       ├── useAgent.ts
│       ├── useApprovals.ts
│       ├── useBriefing.ts
│       ├── useVoice.ts
│       └── useWellbeing.ts
│
├── mcp-connectors/                       # Standalone MCP Servers
│   ├── gmail/
│   │   ├── server.py
│   │   └── Dockerfile
│   ├── google-calendar/
│   │   ├── server.py
│   │   └── Dockerfile
│   ├── hubspot/
│   │   ├── server.py
│   │   └── Dockerfile
│   ├── datev/
│   │   ├── server.py
│   │   └── Dockerfile
│   └── n8n-bridge/
│       ├── server.py
│       └── Dockerfile
│
├── infrastructure/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── dashboard.Dockerfile
│   │   └── nginx.conf
│   ├── k8s/                              # Kubernetes Manifests (Phase 3)
│   │   ├── backend-deployment.yml
│   │   ├── dashboard-deployment.yml
│   │   └── ingress.yml
│   ├── vault/
│   │   └── config.hcl                    # Vault Configuration
│   └── monitoring/
│       ├── grafana/
│       │   └── dashboards/
│       ├── loki-config.yml
│       └── otel-collector-config.yml
│
└── docs/
    ├── architecture/
    │   ├── level1-foundation.md
    │   ├── level2-security.md
    │   ├── level3-ambient-agent.md
    │   ├── level4-data-architecture.md
    │   └── level5-living-agent.md
    ├── api/
    │   └── openapi.yml
    ├── deployment/
    │   ├── model-a-saas.md
    │   ├── model-b-hybrid.md
    │   └── model-c-onprem.md
    └── connectors/
        ├── creating-connectors.md
        └── connector-sdk.md
```

---

# 5. BACKEND: FastAPI + LangGraph

## 5.1 FastAPI App Entry Point

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import (
    auth, agents, approvals, briefings, chat, connectors,
    dashboard, knowledge, notifications, tenants, voice,
    wellbeing, evolution, webhooks
)
from app.core.tenant import TenantMiddleware
from app.core.audit import AuditMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_graphiti()
    await init_redis()
    await init_vault()
    await init_langfuse()
    await register_cron_jobs()
    yield
    # Shutdown
    await close_connections()

app = FastAPI(
    title="Agent One API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware (Reihenfolge wichtig!)
app.add_middleware(AuditMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion: spezifische Origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["Approvals"])
app.include_router(briefings.router, prefix="/api/v1/briefings", tags=["Briefings"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connectors"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["Knowledge"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(wellbeing.router, prefix="/api/v1/wellbeing", tags=["Wellbeing"])
app.include_router(evolution.router, prefix="/api/v1/evolution", tags=["Evolution"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
```

## 5.2 Tenant-Isolation Middleware

```python
# backend/app/core/tenant.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class TenantMiddleware(BaseHTTPMiddleware):
    """Löst Tenant aus Subdomain oder Header auf"""
    
    async def dispatch(self, request: Request, call_next):
        # 1. Subdomain-Routing: benjamin.agent-one.de → tenant "benjamin"
        host = request.headers.get("host", "")
        subdomain = host.split(".")[0] if "." in host else None
        
        # 2. Oder: X-Tenant-ID Header (API-Calls)
        tenant_id = request.headers.get("X-Tenant-ID") or subdomain
        
        if tenant_id:
            tenant = await get_tenant(tenant_id)
            request.state.tenant = tenant
            request.state.tenant_id = tenant.id
        
        response = await call_next(request)
        return response
```

## 5.3 Config (Pydantic Settings)

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Agent One"
    APP_ENV: str = "development"  # development | staging | production
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str  # postgresql://...
    REDIS_URL: str     # redis://...
    
    # FalkorDB / Graphiti
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    
    # LLM APIs
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    LITELLM_MASTER_KEY: str
    
    # Voice
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    
    # Vapi (Telefon-Agent)
    VAPI_API_KEY: str = ""
    
    # Push Notifications
    EXPO_ACCESS_TOKEN: str
    
    # HashiCorp Vault
    VAULT_ADDR: str = "http://vault:8200"
    VAULT_TOKEN: str
    
    # Langfuse
    LANGFUSE_HOST: str = "http://langfuse:3000"
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    
    # n8n
    N8N_BASE_URL: str = "http://n8n:5678"
    N8N_API_KEY: str = ""
    
    # LangGraph
    LANGGRAPH_API_URL: str = "http://localhost:8123"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

# 6. FRONTEND: Next.js Dashboard

## 6.1 Tenant-Aware Middleware

```typescript
// dashboard/src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || ''
  const subdomain = hostname.split('.')[0]
  
  // Subdomain → Tenant Resolution
  // benjamin.agent-one.de → tenant "benjamin"
  if (subdomain && subdomain !== 'www' && subdomain !== 'app') {
    const response = NextResponse.next()
    response.headers.set('x-tenant-id', subdomain)
    return response
  }
  
  return NextResponse.next()
}
```

## 6.2 Dashboard Screens

| Screen | Route | Funktion |
|--------|-------|----------|
| **Overview** | `/dashboard` | KPIs, letzte Aktionen, Quick Actions |
| **Chat** | `/dashboard/chat` | Streaming Chat mit Agent, Voice Input |
| **Approvals** | `/dashboard/approvals` | Genehmigungs-Queue mit Batch-Actions |
| **Briefing** | `/dashboard/briefing` | Morgen-Briefing Anzeige + Historie |
| **Knowledge** | `/dashboard/knowledge` | Cytoscape.js Graph Browser + Suche |
| **Connectors** | `/dashboard/connectors` | MCP Connector Install/Config/OAuth |
| **Connectors/New** | `/dashboard/connectors/new` | HTTP Universal Connector Builder |
| **Evolution** | `/dashboard/evolution` | Skill Library, Prompt-Versionen, A/B Tests |
| **Wellbeing** | `/dashboard/wellbeing` | Wellbeing Score, Arbeitsmuster, Empfehlungen |
| **Audit** | `/dashboard/audit` | Audit Trail durchsuchen + exportieren |
| **Analytics** | `/dashboard/analytics` | Nutzungsstatistiken, Kosten, Performance |
| **Settings** | `/dashboard/settings` | Profil, Team, Billing, Agent Config |

## 6.3 White-Labeling

```typescript
// Tenant Config (gespeichert in PostgreSQL)
interface TenantConfig {
  id: string
  name: string                    // "Kanzlei Schmidt"
  subdomain: string               // "schmidt"
  branding: {
    logo_url: string
    primary_color: string         // "#1e40af"
    secondary_color: string       // "#3b82f6"
    company_name: string          // "Kanzlei Schmidt"
    favicon_url: string
  }
  features: {
    voice_enabled: boolean
    phone_agent_enabled: boolean
    wellbeing_enabled: boolean
    evolution_dashboard: boolean
  }
  agent_config: {
    morning_briefing_time: string // "07:00"
    evening_cutoff_time: string   // "21:00"
    auto_approve_threshold: number // 0.85
    language: string              // "de"
  }
}
```

---

# 7. MOBILE APP: Expo / React Native

## 7.1 Die Fünf App Screens

### Screen 1: Briefing (Home Tab)
Morgen-Briefing mit Zusammenfassung: neue E-Mails, Termine, Fristen, vorbereitete Aktionen. One-Tap-Genehmigungen direkt aus dem Briefing.

### Screen 2: Inbox (Approvals Tab)
Agent-Inbox mit allen anstehenden Genehmigungen. Swipe-Right = Genehmigen. Swipe-Left = Ablehnen. Tap = Detail + Bearbeiten. Batch-Aktionen für Routine-Items.

### Screen 3: Chat (Chat Tab)
Vollwertiger Chat mit dem Agent. Voice-Button für Spracheingabe (Deepgram STT). Agent antwortet per Text UND optional per Sprache (ElevenLabs TTS). Streaming-Antworten via Vercel AI SDK. Kontext aus Graphiti wird automatisch geladen.

### Screen 4: Activity (Feed Tab)
Chronologischer Feed aller Agent-Aktionen. Filtert nach: Automatisch erledigt, Genehmigt, Abgelehnt, Bearbeitet.

### Screen 5: Settings & Wellbeing
Profil, Push-Einstellungen, Agent-Konfiguration. **Wellbeing-Widget** mit aktuellem Score und Trend. Wochen-Check-in mit Empfehlungen.

## 7.2 Voice-First Interaktion (Detail)

```typescript
// mobile/services/voice.ts

import { Audio } from 'expo-av'

interface VoiceService {
  // STT: Deepgram (exzellentes Deutsch)
  startListening(): Promise<void>
  stopListening(): Promise<string>     // Gibt transkribierten Text zurück
  
  // TTS: ElevenLabs (natürliches Deutsch)
  speak(text: string): Promise<void>
  stopSpeaking(): void
}

// Ablauf:
// 1. Nutzer drückt Voice-Button (Push-to-Talk)
// 2. Audio wird aufgenommen (expo-av)
// 3. Audio → Deepgram WebSocket STT → Text
// 4. Text → Agent API (Streaming)
// 5. Agent-Antwort → ElevenLabs TTS → Audio
// 6. Audio wird abgespielt
// Gesamtlatenz: ~600ms (Deepgram ~200ms + Agent ~200ms + ElevenLabs ~200ms)
```

## 7.3 Push Notification Architektur

```typescript
// mobile/services/notifications.ts

// Push-Kategorien mit unterschiedlicher Dringlichkeit:

type NotificationCategory =
  | 'URGENT_APPROVAL'     // Sofortige Push + Sound + Vibration
  | 'ROUTINE_APPROVAL'    // Stille Push mit Badge-Update
  | 'BRIEFING_READY'      // Morgen-Briefing fertig
  | 'AGENT_UPDATE'        // Agent hat etwas erledigt
  | 'WELLBEING_REMINDER'  // Guardian Angel Hinweis
  | 'DEADLINE_WARNING'    // Frist nähert sich

// Interactive Notification Actions (direkt aus Notification):
// URGENT_APPROVAL → [Genehmigen] [Ablehnen] [In App öffnen]
// BRIEFING_READY → [Briefing anzeigen]
// WELLBEING_REMINDER → [Akzeptieren] [Später]
```

## 7.4 On-Device AI (Offline-Fallback)

```typescript
// mobile/services/offline.ts
import { useLLM, LLAMA3_2_1B } from 'react-native-executorch'

// Llama 3.2 1B auf dem Gerät für:
// - E-Mail-Klassifikation (dringend/routine/spam)
// - Einfache Text-Zusammenfassungen
// - OCR-Nachbearbeitung
// - Grundlegende Fragen wenn offline
// NICHT für: Komplexes Reasoning, Multi-Step-Aufgaben
```

---

# 8. DATENBANK-SCHEMAS

## 8.1 PostgreSQL (Multi-Tenant mit RLS)

```sql
-- Row Level Security aktivieren
ALTER TABLE ALL TABLES ENABLE ROW LEVEL SECURITY;

-- Tenant
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(63) UNIQUE NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'starter',  -- starter|professional|enterprise
    deployment_model VARCHAR(20) NOT NULL DEFAULT 'saas',  -- saas|hybrid|onprem
    branding JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    agent_config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner|admin|member
    expo_push_token VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    UNIQUE(tenant_id, email)
);

-- RLS Policy
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Agent-Aktionen (Jede einzelne Aktion wird geloggt)
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    agent_type VARCHAR(50) NOT NULL,        -- email|calendar|phone|deadline|research
    action_type VARCHAR(100) NOT NULL,       -- send_email|create_event|make_call|...
    action_category VARCHAR(50) NOT NULL,    -- routine|important|critical
    input_summary TEXT,                      -- Zusammenfassung der Eingabe
    output_summary TEXT,                     -- Zusammenfassung der Ausgabe
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending|approved|rejected|edited|auto_approved
    trust_score_at_time FLOAT,              -- Trust Score zum Zeitpunkt
    was_auto_approved BOOLEAN DEFAULT FALSE,
    human_edit_diff TEXT,                    -- Diff wenn bearbeitet
    langfuse_trace_id VARCHAR(255),         -- Link zu Langfuse Trace
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id)
);
CREATE INDEX idx_actions_tenant ON agent_actions(tenant_id, created_at DESC);
CREATE INDEX idx_actions_status ON agent_actions(tenant_id, status);

-- Trust Scores (Pro Aktions-Typ pro Tenant)
CREATE TABLE trust_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    action_type VARCHAR(100) NOT NULL,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    edited_count INTEGER DEFAULT 0,
    current_score FLOAT DEFAULT 0.0,         -- 0.0 - 1.0
    auto_approve_threshold FLOAT DEFAULT 0.85,
    is_never_auto BOOLEAN DEFAULT FALSE,     -- Manuell gesperrt
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, action_type)
);

-- Skill Library (Level 5: Gelernte Fähigkeiten)
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    skill_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),                   -- communication|scheduling|legal|...
    lessons JSONB DEFAULT '[]',              -- Array von gelernten Lektionen
    confidence FLOAT DEFAULT 0.5,
    source VARCHAR(50),                      -- nightly_reflection|edit_diff|manual
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, skill_name)
);

-- Prompt-Versionen (Level 5: Prompt Evolution)
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    agent_type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    parent_version INTEGER,
    change_description TEXT,
    performance_score FLOAT,                 -- Aus A/B-Test
    is_active BOOLEAN DEFAULT FALSE,
    is_rollback_safe BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, agent_type, version)
);

-- Wellbeing Scores (Level 5: Guardian Angel)
CREATE TABLE wellbeing_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    score FLOAT NOT NULL,                    -- 0.0 - 1.0
    signals JSONB NOT NULL,                  -- Alle 5 Signale im Detail
    recommendations JSONB DEFAULT '[]',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_wellbeing_user ON wellbeing_scores(user_id, period_end DESC);

-- MCP Connector Configs
CREATE TABLE connector_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    connector_type VARCHAR(100) NOT NULL,    -- gmail|google_calendar|hubspot|datev|http_universal
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',               -- Connector-spezifische Config
    oauth_token_vault_path VARCHAR(255),     -- Pfad in HashiCorp Vault
    permissions JSONB DEFAULT '{}',          -- Erlaubte Operationen
    last_synced TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Trail (Immutable, Write-Once)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID,
    agent_type VARCHAR(50),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, created_at DESC);
-- KEIN UPDATE/DELETE auf audit_logs erlaubt (Write-Once)
REVOKE UPDATE, DELETE ON audit_logs FROM app_user;
```

---

# 9. KNOWLEDGE GRAPH: Graphiti + FalkorDB

## 9.1 Graphiti-Integration

```python
# backend/app/agents/tools/graphiti_tools.py
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# Graphiti Initialisierung (einmal beim Start)
graphiti = Graphiti(
    neo4j_uri=settings.FALKORDB_HOST,
    neo4j_password=settings.FALKORDB_PASSWORD,
)

async def save_to_memory(
    tenant_id: str,
    content: str,
    source: str = "agent_action",
    episode_type: EpisodeType = EpisodeType.text
):
    """Speichert eine Episode im Knowledge Graph des Tenants"""
    await graphiti.add_episode(
        name=f"episode_{datetime.now().isoformat()}",
        episode_body=content,
        source=source,
        source_description=f"Agent One - {source}",
        group_id=tenant_id,  # CRITICAL: Tenant-Isolation!
        episode_type=episode_type,
    )

async def query_memory(
    tenant_id: str,
    query: str,
    num_results: int = 10
) -> list:
    """Sucht im Knowledge Graph des Tenants"""
    results = await graphiti.search(
        query=query,
        group_ids=[tenant_id],  # Nur im Tenant suchen!
        num_results=num_results,
    )
    return results
```

## 9.2 Graphiti Temporal Queries (für Weltmodell)

```python
async def get_temporal_patterns(
    tenant_id: str,
    entity: str,
    time_range: tuple[datetime, datetime]
) -> list:
    """Holt temporale Muster für das Business World Model"""
    # Graphiti speichert bi-temporal:
    # - valid_at: Wann der Fakt gültig wurde
    # - invalid_at: Wann der Fakt ungültig wurde
    # Das ermöglicht: "Was hat sich bei Mandant X über die Zeit geändert?"
    results = await graphiti.search(
        query=f"Temporal changes for {entity}",
        group_ids=[tenant_id],
        num_results=50,
    )
    return [r for r in results if r.valid_at >= time_range[0]]
```

## 9.3 PII-Filter vor Graphiti-Speicherung

```python
# backend/app/services/pii_service.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

ENTITIES_TO_FILTER = [
    "PHONE_NUMBER", "IBAN_CODE", "EMAIL_ADDRESS",
    "CREDIT_CARD", "IP_ADDRESS", "MEDICAL_LICENSE",
    "DE_DRIVER_LICENSE",  # Deutsche Führerscheinnummer
]

async def filter_pii(text: str, language: str = "de") -> str:
    """Filtert PII BEVOR Daten in Graphiti gespeichert werden"""
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=ENTITIES_TO_FILTER
    )
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )
    return anonymized.text
    # "Müller hat IBAN DE89..." → "Müller hat IBAN <IBAN>"
```

---

# 10. AGENT-SYSTEM: LangGraph Multi-Agent

## 10.1 Supervisor Agent (Haupt-Orchestrator)

```python
# backend/app/agents/supervisor.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver

class AgentState(TypedDict):
    messages: list
    tenant_id: str
    user_id: str
    current_plan: list[str]
    completed_tasks: list[str]
    pending_approvals: list[dict]
    trust_scores: dict
    skills: list[dict]           # Level 5: Loaded Skills
    wellbeing_score: float       # Level 5: Current Score

def create_supervisor(tenant_id: str):
    """Erstellt den Supervisor Agent für einen Tenant"""
    
    # Sub-Agents als Tools
    tools = [
        email_agent_tool,        # E-Mail lesen/schreiben
        calendar_agent_tool,     # Termine verwalten
        phone_agent_tool,        # Anrufe planen/durchführen
        deadline_agent_tool,     # Fristen überwachen
        research_agent_tool,     # Web-Recherche
        graphiti_search_tool,    # Knowledge Graph suchen
        graphiti_save_tool,      # Knowledge Graph speichern
        request_approval_tool,   # Mensch um Genehmigung bitten
        send_notification_tool,  # Push Notification senden
    ]
    
    # System Prompt (wird durch Level 5 Evolution verbessert)
    system_prompt = load_active_prompt(tenant_id, "supervisor")
    
    # Skills aus Skill Library laden
    skills = load_skills(tenant_id)
    if skills:
        system_prompt += f"\n\nGelernte Regeln:\n{format_skills(skills)}"
    
    graph = StateGraph(AgentState)
    
    # Nodes
    graph.add_node("plan", plan_node)         # Plan erstellen
    graph.add_node("execute", execute_node)   # Plan ausführen
    graph.add_node("reflect", reflect_node)   # Ergebnis bewerten
    graph.add_node("approve", approve_node)   # Genehmigung einholen
    
    # Edges
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges("execute", route_after_execute)
    graph.add_edge("approve", "execute")
    graph.add_edge("reflect", END)
    
    graph.set_entry_point("plan")
    
    # Checkpointing (State überlebt Crashes)
    checkpointer = PostgresSaver(conn_string=settings.DATABASE_URL)
    
    return graph.compile(checkpointer=checkpointer)
```

## 10.2 Cron Jobs

```python
# backend/app/agents/cron_jobs.py
from langgraph_sdk import get_client

async def register_cron_jobs():
    """Registriert alle Cron Jobs beim LangGraph Server"""
    client = get_client(url=settings.LANGGRAPH_API_URL)
    
    # 1. Morgen-Briefing: Jeden Tag um 07:00 (pro Tenant konfigurierbar)
    for tenant in await get_active_tenants():
        briefing_time = tenant.agent_config.get("morning_briefing_time", "07:00")
        hour, minute = briefing_time.split(":")
        
        await client.crons.create(
            assistant_id="briefing-agent",
            schedule=f"{minute} {hour} * * *",
            input={
                "messages": [{
                    "role": "user",
                    "content": "Erstelle das Morgen-Briefing."
                }],
                "tenant_id": tenant.id
            }
        )
    
    # 2. E-Mail-Monitor: Alle 5 Minuten
    await client.crons.create(
        assistant_id="email-monitor",
        schedule="*/5 * * * *",
        input={"messages": [{"role": "user", "content": "Prüfe Posteingang."}]}
    )
    
    # 3. Fristen-Wächter: Täglich um 08:00
    await client.crons.create(
        assistant_id="deadline-agent",
        schedule="0 8 * * *",
        input={"messages": [{"role": "user", "content": "Prüfe Fristen."}]}
    )
    
    # 4. Nightly Reflection (Level 5): Täglich um 02:00
    await client.crons.create(
        assistant_id="reflection-agent",
        schedule="0 2 * * *",
        input={"messages": [{"role": "user", "content": "Nightly Reflection."}]}
    )
    
    # 5. Guardian Angel Weekly (Level 5): Sonntags um 20:00
    await client.crons.create(
        assistant_id="guardian-angel",
        schedule="0 20 * * 0",
        input={"messages": [{"role": "user", "content": "Wochen-Wellbeing-Report."}]}
    )
```

## 10.3 Trust Score System

```python
# backend/app/services/trust_service.py

class TrustService:
    
    async def calculate_trust_score(
        self,
        tenant_id: str,
        action_type: str
    ) -> float:
        """Berechnet den Trust Score für einen Aktionstyp"""
        score = await db.get(TrustScore, tenant_id=tenant_id, action_type=action_type)
        
        if not score:
            return 0.0
        
        total = score.approved_count + score.rejected_count + score.edited_count
        if total == 0:
            return 0.0
        
        # Gewichtete Berechnung:
        # Approved = 1.0, Edited = 0.5, Rejected = 0.0
        weighted = (
            score.approved_count * 1.0 +
            score.edited_count * 0.5 +
            score.rejected_count * 0.0
        )
        
        raw_score = weighted / total
        
        # Minimum Sample Size: Braucht mindestens 10 Aktionen
        confidence = min(total / 10, 1.0)
        
        return raw_score * confidence
    
    async def should_auto_approve(
        self,
        tenant_id: str,
        action_type: str
    ) -> bool:
        """Entscheidet ob eine Aktion auto-genehmigt werden kann"""
        score = await self.calculate_trust_score(tenant_id, action_type)
        trust = await db.get(TrustScore, tenant_id=tenant_id, action_type=action_type)
        
        if trust and trust.is_never_auto:
            return False  # Manuell gesperrt
        
        threshold = trust.auto_approve_threshold if trust else 0.85
        return score >= threshold
    
    async def record_feedback(
        self,
        tenant_id: str,
        action_type: str,
        feedback: str  # "approved" | "rejected" | "edited"
    ):
        """Aktualisiert Trust Score nach Feedback"""
        score = await db.get_or_create(TrustScore, tenant_id=tenant_id, action_type=action_type)
        
        if feedback == "approved":
            score.approved_count += 1
        elif feedback == "rejected":
            score.rejected_count += 1
        elif feedback == "edited":
            score.edited_count += 1
        
        score.current_score = await self.calculate_trust_score(tenant_id, action_type)
        score.last_updated = datetime.utcnow()
        await db.save(score)
```

---

# 11. SECURITY & AUTH

## 11.1 Authentifizierung

```python
# JWT Token mit Tenant-Kontext
class TokenPayload(BaseModel):
    sub: str          # user_id
    tenant_id: str    # tenant_id
    role: str         # owner|admin|member
    exp: datetime
    
# OAuth 2.0 für externe Dienste
# Tokens werden in HashiCorp Vault gespeichert, NICHT in der Datenbank
```

## 11.2 Verschlüsselung

| Ebene | Methode |
|-------|---------|
| **Transport** | TLS 1.3 überall |
| **API Gateway** | mTLS für Hybrid-Kunden (Model B) |
| **Datenbank** | AES-256 Envelope Encryption pro Tenant |
| **Knowledge Graph** | Graphiti group_id + verschlüsselte Edges |
| **Vault** | HashiCorp Vault für alle Secrets |
| **Mobile** | Biometric Auth + expo-secure-store |

## 11.3 Audit Trail

```python
# Jede Aktion wird geloggt — unveränderlich
class AuditLogger:
    async def log(
        self,
        tenant_id: str,
        action: str,
        details: dict,
        user_id: str = None,
        agent_type: str = None,
    ):
        await db.insert(AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_type=agent_type,
            action=action,
            details=details,
            ip_address=get_client_ip(),
            created_at=datetime.utcnow()
        ))
        # Zusätzlich: Write-Once Copy auf Hetzner Object Storage
```

## 11.4 DSGVO-Compliance Checkliste

- [x] **Art. 25**: Data Protection by Design and by Default (Zero-Data-Retention)
- [x] **Art. 28**: Auftragsverarbeitung (AVV-Template für jeden Kunden)
- [x] **Art. 30**: Verarbeitungsverzeichnis (automatisch aus Audit Trail)
- [x] **Art. 32**: Technische & organisatorische Maßnahmen (Encryption, Isolation, Vault)
- [x] **Art. 35**: Datenschutz-Folgenabschätzung (DSFA-Template bereitstellen)
- [x] **§203 StGB**: Berufsgeheimnis (Hybrid-Modell: Daten bleiben beim Kunden)
- [x] **EU AI Act**: Transparenz-Anforderungen (Audit Trail zeigt jede Agent-Entscheidung)
- [x] **BSI Grundschutz++**: ISO 27001-konforme Infrastruktur (Hetzner)

---

# 12. CACHING & KOSTENOPTIMIERUNG

## 12.1 Drei-Schichten-Caching

```python
# Schicht 1: Semantisches Caching (Redis + Embeddings)
# 31% der Queries sind semantisch ähnlich → Cache Hit
class SemanticCache:
    async def get_or_compute(self, query: str, compute_fn):
        embedding = await get_embedding(query)
        cached = await redis.vector_search(embedding, threshold=0.92)
        if cached:
            return cached  # ~100ms statt ~6.5s
        result = await compute_fn(query)
        await redis.store(embedding, result, ttl=3600)
        return result

# Schicht 2: RouteLLM (Smart Model Routing)
# 95% GPT-4-Qualität bei 14-26% der Kosten
# Einfache Aufgaben → GPT-4o-mini (16x günstiger)
# Komplexe Aufgaben → Claude Opus / GPT-4o

# Schicht 3: LangGraph Node-Level Caching
# Individuelle Nodes cachen mit konfigurierbarem TTL
```

## 12.2 Kostenübersicht pro Kunde (Model A)

| Posten | Kosten/Monat |
|--------|-------------|
| LLM API (mit Caching + Routing) | €15-30 |
| Infrastruktur (proportional) | €1-3 |
| Expo Push Service | €0.50 |
| **Gesamt** | **€17-34** |
| **Preis** | **€249/Mo** |
| **Brutto-Marge** | **87-93%** |

---

# 13. MCP GATEWAY & CONNECTORS

## 13.1 MCP Gateway

```python
# backend/app/mcp/gateway.py

class MCPGateway:
    """Zentrale Sicherheitsschicht für alle MCP-Verbindungen"""
    
    async def handle_request(
        self,
        tenant_id: str,
        connector_id: str,
        tool_name: str,
        parameters: dict
    ) -> dict:
        # 1. Auth Check
        connector = await self.get_connector(tenant_id, connector_id)
        if not connector.is_active:
            raise ConnectorDisabledError()
        
        # 2. Permission Check
        if tool_name not in connector.permissions.get("allowed_tools", []):
            raise PermissionDeniedError(f"Tool {tool_name} nicht erlaubt")
        
        # 3. Rate Limiting
        await self.check_rate_limit(tenant_id, connector_id)
        
        # 4. PII Filter (für §203-Kunden)
        if connector.config.get("pii_filter_enabled"):
            parameters = await pii_service.filter_pii_in_params(parameters)
        
        # 5. Execute
        result = await self.execute_tool(connector, tool_name, parameters)
        
        # 6. Audit Log
        await audit.log(
            tenant_id=tenant_id,
            action=f"mcp.{connector.connector_type}.{tool_name}",
            details={"parameters": parameters, "result_summary": summarize(result)}
        )
        
        return result
```

## 13.2 Connector-Beispiel: Gmail

```python
# mcp-connectors/gmail/server.py
from mcp.server import Server

server = Server("gmail-connector")

@server.tool("read_emails")
async def read_emails(count: int = 10, label: str = "INBOX"):
    """Liest die neuesten E-Mails"""
    # OAuth Token aus Vault laden
    token = await vault.get_oauth_token(tenant_id, "gmail")
    # Gmail API aufrufen
    messages = await gmail_api.list_messages(token, label, count)
    return messages

@server.tool("send_email")
async def send_email(to: str, subject: str, body: str):
    """Sendet eine E-Mail"""
    token = await vault.get_oauth_token(tenant_id, "gmail")
    return await gmail_api.send(token, to, subject, body)

@server.tool("search_emails")
async def search_emails(query: str, max_results: int = 10):
    """Durchsucht E-Mails"""
    token = await vault.get_oauth_token(tenant_id, "gmail")
    return await gmail_api.search(token, query, max_results)
```

## 13.3 HTTP Universal Connector

```python
# Jede REST API in 5 Minuten via Dashboard-UI konfigurierbar:
# 1. Name, Base URL, Auth (OAuth 2.0 / API Key / Basic)
# 2. Tools definieren: HTTP Method, Path, Parameters, Description
# 3. Sofort aktiv — Agent erkennt neue Tools automatisch
# Kein Code, kein Deployment
```

---

# 14. N8N ORCHESTRATION BRIDGE

## 14.1 n8n als MCP Server

```python
# mcp-connectors/n8n-bridge/server.py

@server.tool("execute_workflow")
async def execute_n8n_workflow(
    workflow_id: str,
    input_data: dict
):
    """Führt einen n8n Workflow aus und gibt das Ergebnis zurück"""
    result = await n8n_api.execute_workflow(
        base_url=settings.N8N_BASE_URL,
        api_key=settings.N8N_API_KEY,
        workflow_id=workflow_id,
        data=input_data
    )
    return result

@server.tool("list_workflows")
async def list_n8n_workflows():
    """Listet alle verfügbaren n8n Workflows"""
    return await n8n_api.get_workflows(
        base_url=settings.N8N_BASE_URL,
        api_key=settings.N8N_API_KEY
    )
```

## 14.2 n8n Deployment pro Modell

| Modell | n8n Location | Verbindung |
|--------|-------------|------------|
| **A (SaaS)** | n8n Cloud (Frankfurt) ODER unsere Instanz | Agent → n8n Cloud → Kunden-Systeme via OAuth |
| **B (Hybrid)** | n8n self-hosted beim Kunden | Agent → API → Kunden-n8n → Kunden-Systeme (lokal) |
| **C (On-Prem)** | n8n self-hosted beim Kunden | Alles lokal, keine externe Verbindung |

---

# 15. VOICE SYSTEM

## 15.1 In-App Voice (Expo)

```
Ablauf:
1. Nutzer drückt Voice-Button in App
2. expo-av nimmt Audio auf
3. Audio-Stream → Deepgram WebSocket API (STT)
   - Modell: nova-2-general (Deutsch)
   - Latenz: ~200ms
   - Interim Results: Ja (Echtzeit-Transkription)
4. Transkribierter Text → Agent API (SSE Streaming)
5. Agent-Antwort (Text) → ElevenLabs API (TTS)
   - Modell: multilingual_v2
   - Stimme: Konfigurierbar pro Tenant
   - Latenz: ~200ms
6. Audio-Stream → expo-av Playback
   
Gesamt-Latenz: ~600ms (fühlt sich natürlich an)
```

## 15.2 Telefon-Agent (Vapi)

```python
# Integration: Vapi → LangGraph → Vapi
# Vapi nutzt Agent One als Custom LLM Endpoint

# Vapi Konfiguration:
# - STT: Deepgram (exzellentes Deutsch)
# - LLM: Agent One LangGraph Endpoint (Custom)
# - TTS: ElevenLabs (deutsches Voice Cloning)

# Ablauf:
# 1. Anruf kommt rein bei Vapi
# 2. Vapi → Deepgram STT → Text
# 3. Vapi → POST /api/v1/voice/vapi-webhook → Agent One
# 4. Agent One → LangGraph Reasoning (mit Graphiti Kontext)
# 5. Agent One → Response Text → Vapi
# 6. Vapi → ElevenLabs TTS → Sprache zum Anrufer
```

---

# 16. PUSH NOTIFICATIONS & EVENT SYSTEM

## 16.1 Event Router

```python
# backend/app/services/notification_service.py

class NotificationService:
    
    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        category: str,         # URGENT_APPROVAL | ROUTINE_APPROVAL | ...
        data: dict = {},       # Deep Link Data
    ):
        user = await db.get(User, id=user_id)
        if not user.expo_push_token:
            return
        
        # Dringlichkeit bestimmt Push-Verhalten
        priority = "high" if category.startswith("URGENT") else "normal"
        sound = "default" if category.startswith("URGENT") else None
        
        await expo_push.send(
            to=user.expo_push_token,
            title=title,
            body=body,
            sound=sound,
            priority=priority,
            data={"category": category, **data},
            category_id=category  # Für Interactive Actions
        )
```

## 16.2 Event-Driven Triggers

| Event Source | Trigger | Agent-Aktion |
|-------------|---------|-------------|
| Gmail Push API | Neue E-Mail | Kategorisieren, Frist extrahieren, Antwort entwerfen |
| Google Calendar Webhook | Terminerinnerung | Vorbereitung zusammenstellen |
| Vapi Call Event | Verpasster Anruf | Rückruf planen, Zusammenfassung |
| Graphiti Temporal Query | Frist nähert sich | Erinnerung an Mandant |
| CRM Webhook | Neuer Mandant | Willkommens-Workflow starten |

---

# 17. SELF-EVOLUTION ENGINE (Level 5)

## 17.1 Nightly Reflection Agent

```python
# backend/app/agents/reflection_agent.py

class ReflectionAgent:
    """Läuft jede Nacht um 02:00 — analysiert Tagesperformance"""
    
    async def nightly_reflection(self, tenant_id: str):
        # 1. Alle Aktionen des Tages aus Langfuse laden
        actions = await langfuse.get_traces(
            tenant_id=tenant_id,
            date=today(),
            include_feedback=True
        )
        
        # 2. Muster analysieren
        analysis = {
            "total_actions": len(actions),
            "approved": sum(1 for a in actions if a.status == "approved"),
            "rejected": sum(1 for a in actions if a.status == "rejected"),
            "edited": sum(1 for a in actions if a.status == "edited"),
            "auto_approved": sum(1 for a in actions if a.was_auto_approved),
        }
        
        # 3. Edit-Diffs analysieren → Lektionen extrahieren
        edited_actions = [a for a in actions if a.human_edit_diff]
        lessons = await self.extract_lessons_from_edits(edited_actions)
        
        # 4. Skills aktualisieren
        for lesson in lessons:
            await skill_service.add_or_update_skill(
                tenant_id=tenant_id,
                skill_name=lesson.category,
                lesson=lesson.text,
                confidence=lesson.confidence
            )
        
        # 5. Prompt-Verbesserungen generieren
        if lessons:
            await self.propose_prompt_improvements(
                tenant_id=tenant_id,
                lessons=lessons
            )
        
        # 6. A/B-Test vorbereiten wenn Verbesserungen vorliegen
        await self.prepare_ab_tests(tenant_id)
```

## 17.2 Prompt Evolution Engine

```python
# Inspiriert von OpenAIs GEPA (Genetic-Pareto Evolution):
# 1. Generiere Varianten des System-Prompts basierend auf gelernten Lektionen
# 2. 50% der Aktionen mit neuem Prompt, 50% mit altem
# 3. Nach 20+ Aktionen: Performance vergleichen
# 4. Bessere Version wird Standard
# 5. Jede Version wird gespeichert (Rollback möglich)
```

## 17.3 Safety Rails

```python
EVOLUTION_SAFETY_RULES = {
    "bounded_improvement": True,      # Nur Prompts ändern, nicht Code
    "human_review_gate": True,        # Alle Änderungen im Dashboard anzeigen
    "rollback_on_regression": True,   # Auto-Rollback bei >5% Performance-Drop
    "ab_test_minimum": 20,            # Mindestens 20 Aktionen pro Variante
    "immutable_rules": [
        "DSGVO-Compliance",
        "§203 StGB Geheimhaltung",
        "Keine finanziellen Transaktionen ohne Review",
        "Keine Löschungen",
        "Höflichkeit und Professionalität"
    ]
}
```

---

# 18. WORLD MODEL ENGINE (Level 5)

## 18.1 Business World Model

```python
# backend/app/services/world_model_service.py

class BusinessWorldModel:
    """Simuliert mögliche Zukünfte basierend auf Graphiti-Patterns"""
    
    async def simulate_futures(
        self,
        tenant_id: str,
        action: str,
        context: dict,
        num_futures: int = 3
    ) -> list[dict]:
        # 1. Historische Patterns aus Graphiti
        patterns = await graphiti.search(
            query=f"Similar situations to: {action}",
            group_ids=[tenant_id],
            num_results=20
        )
        
        # 2. Beziehungsdaten
        relationships = await graphiti.get_entity_relationships(
            entity=context.get("entity"),
            group_id=tenant_id
        )
        
        # 3. LLM simuliert Zukünfte
        futures = await llm.generate(
            prompt=f"""Basierend auf historischen Mustern, simuliere {num_futures} 
            mögliche Zukünfte für die Aktion: {action}
            Historische Muster: {patterns}
            Beziehungen: {relationships}
            
            Für jede Zukunft: Beschreibung, Wahrscheinlichkeit, Risiko-Score.""",
            model="claude-sonnet-4-5-20250929"
        )
        
        return futures
    
    async def counterfactual_reasoning(
        self,
        tenant_id: str,
        question: str  # "Was passiert wenn wir nicht antworten?"
    ) -> dict:
        """Kontrafaktisches Denken für Morgen-Briefing"""
        patterns = await graphiti.search(
            query=question,
            group_ids=[tenant_id]
        )
        return await llm.generate(
            prompt=f"Counterfactual: {question}\nPatterns: {patterns}"
        )
```

---

# 19. GUARDIAN ANGEL (Level 5)

## 19.1 Wellbeing Score Calculator

```python
# backend/app/services/wellbeing_service.py

class WellbeingService:
    
    SIGNAL_WEIGHTS = {
        "work_hours": 0.25,
        "decision_fatigue": 0.20,
        "recovery": 0.20,
        "pressure": 0.15,
        "recovery_days": 0.20,
    }
    
    async def calculate_score(
        self,
        tenant_id: str,
        user_id: str,
        period_days: int = 7
    ) -> WellbeingReport:
        signals = {}
        
        # Signal 1: Arbeitszeiten
        work_hours = await self.get_work_hours(user_id, period_days)
        signals["work_hours"] = self.score_range(work_hours.avg_daily, 6, 9)
        
        # Signal 2: Entscheidungslast (Approvals pro Tag)
        decisions = await self.get_approval_count(user_id, period_days)
        signals["decision_fatigue"] = self.score_range(decisions.avg_daily, 5, 25)
        
        # Signal 3: Pausen
        breaks = await self.get_break_patterns(user_id, period_days)
        signals["recovery"] = self.score_range(breaks.avg_minutes, 30, 120)
        
        # Signal 4: Kommunikations-Tempo
        response = await self.get_response_patterns(user_id)
        signals["pressure"] = 1.0 if response.trend == "stable" else 0.6
        
        # Signal 5: Freie Tage (letzte 30 Tage)
        days_off = await self.get_days_off(user_id, 30)
        signals["recovery_days"] = self.score_range(days_off, 4, 10)
        
        # Gesamtscore
        overall = sum(
            signals[k] * self.SIGNAL_WEIGHTS[k]
            for k in self.SIGNAL_WEIGHTS
        )
        
        # Empfehlungen generieren
        recommendations = await self.generate_recommendations(signals, overall)
        
        return WellbeingReport(
            score=overall,
            signals=signals,
            recommendations=recommendations,
            trend=await self.calculate_trend(user_id)
        )
```

## 19.2 Adaptive Load Balancer

```python
# Wenn Wellbeing Score niedrig:
# 1. Trust-Threshold temporär senken → Agent übernimmt mehr automatisch
# 2. Nur DRINGENDE Approvals als Push → Rest im Morgen-Briefing
# 3. Kalender-Schutz: Focus-Blocks einfügen
# 4. Abend-Modus früher aktivieren

async def adjust_for_wellbeing(tenant_id: str, user_id: str):
    score = await wellbeing_service.get_latest_score(user_id)
    
    if score < 0.5:  # Niedrig
        await tenant_service.update_config(tenant_id, {
            "auto_approve_threshold": 0.70,      # Statt 0.85
            "push_only_urgent": True,
            "evening_cutoff": "20:00",           # Statt 21:00
            "insert_focus_blocks": True
        })
    elif score < 0.3:  # Kritisch
        await send_wellbeing_alert(user_id, score)
```

---

# 20. DEPLOYMENT & INFRASTRUCTURE

## 20.1 Docker Compose (Model A: SaaS)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - VAULT_ADDR=http://vault:8200
    depends_on:
      - postgres
      - redis
      - falkordb
      - vault
    
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.agent-one.de
    
  langgraph:
    image: langchain/langgraph-api:latest
    ports:
      - "8123:8000"
    environment:
      - DATABASE_URL=postgresql://...
    
  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=agent_one
      - POSTGRES_USER=agent_one
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6380:6379"
    volumes:
      - falkordb_data:/data
    
  vault:
    image: hashicorp/vault:latest
    cap_add:
      - IPC_LOCK
    volumes:
      - vault_data:/vault/data
      - ./infrastructure/vault:/vault/config
    
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://...
    
  litellm:
    image: ghcr.io/berriai/litellm:latest
    ports:
      - "4000:4000"
    environment:
      - REDIS_HOST=redis
    
  traefik:
    image: traefik:v3.0
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - traefik_certs:/certs

volumes:
  postgres_data:
  redis_data:
  falkordb_data:
  vault_data:
  traefik_certs:
```

## 20.2 Skalierungsphasen

| Phase | Kunden | Server | Kosten/Mo |
|-------|--------|--------|-----------|
| **1** | 1-50 | 1x Hetzner CX41 (16GB, 4vCPU) | ~€30 |
| **2** | 50-500 | 3x Hetzner (App + Data + Services) | ~€150 |
| **3** | 500-5.000 | k3s Cluster (auto-scaling) | €500-2.000 |

## 20.3 Hosting-Empfehlung

Für die Produktionsinfrastruktur: **Hetzner Cloud** (Nürnberg/Falkenstein), ISO 27001-zertifiziert.
Für einfachere Setups und Kunden-VPS: **Hostinger** (https://hostinger.com/kiheroes, Code KIHEROES für 5% Rabatt, nur KVM 2 oder größer).

---

# 21. ENVIRONMENT VARIABLES

```bash
# .env.example

# === App ===
APP_NAME=AgentOne
APP_ENV=development
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,agent-one.de

# === Database ===
DATABASE_URL=postgresql://agent_one:password@postgres:5432/agent_one
REDIS_URL=redis://redis:6379/0

# === FalkorDB / Graphiti ===
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
FALKORDB_PASSWORD=

# === LLM APIs ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LITELLM_MASTER_KEY=sk-litellm-...

# === Voice ===
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# === Telefon ===
VAPI_API_KEY=...

# === Push Notifications ===
EXPO_ACCESS_TOKEN=...

# === HashiCorp Vault ===
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=...

# === Langfuse ===
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# === n8n ===
N8N_BASE_URL=http://n8n:5678
N8N_API_KEY=...

# === LangGraph ===
LANGGRAPH_API_URL=http://langgraph:8000

# === Email (für Transactional Mails) ===
SMTP_HOST=smtp.eu.mailgun.org
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# === Hetzner Object Storage (Audit Logs) ===
S3_ENDPOINT=https://fsn1.your-objectstorage.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=agent-one-audit
```

---

# 22. API-REFERENZ

## 22.1 Auth Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Neuen Nutzer + Tenant erstellen |
| POST | `/api/v1/auth/login` | Login → JWT Token |
| POST | `/api/v1/auth/refresh` | Token Refresh |
| GET | `/api/v1/auth/me` | Aktueller Nutzer |

## 22.2 Agent Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/chat/message` | Nachricht an Agent (SSE Streaming) |
| POST | `/api/v1/voice/stt` | Audio → Text (Deepgram) |
| POST | `/api/v1/voice/tts` | Text → Audio (ElevenLabs) |
| GET | `/api/v1/briefings/today` | Heutiges Morgen-Briefing |
| GET | `/api/v1/briefings/history` | Briefing-Historie |

## 22.3 Approval Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/approvals` | Alle offenen Genehmigungen |
| POST | `/api/v1/approvals/{id}/approve` | Genehmigen |
| POST | `/api/v1/approvals/{id}/reject` | Ablehnen |
| POST | `/api/v1/approvals/{id}/edit` | Bearbeiten + Genehmigen |
| POST | `/api/v1/approvals/batch` | Batch Approve/Reject |

## 22.4 Knowledge Graph Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/knowledge/search?q=...` | Knowledge Graph durchsuchen |
| GET | `/api/v1/knowledge/entity/{id}` | Entity-Details |
| GET | `/api/v1/knowledge/graph` | Graph-Daten für Visualisierung |

## 22.5 Connector Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/connectors` | Alle Connectors des Tenants |
| POST | `/api/v1/connectors` | Neuen Connector hinzufügen |
| POST | `/api/v1/connectors/{id}/oauth/start` | OAuth Flow starten |
| POST | `/api/v1/connectors/{id}/oauth/callback` | OAuth Callback |
| DELETE | `/api/v1/connectors/{id}` | Connector entfernen |
| POST | `/api/v1/connectors/universal` | HTTP Universal Connector |

## 22.6 Level 5 Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/evolution/skills` | Skill Library |
| GET | `/api/v1/evolution/prompts` | Prompt-Versionen |
| POST | `/api/v1/evolution/prompts/{id}/approve` | Prompt-Änderung genehmigen |
| POST | `/api/v1/evolution/prompts/{id}/rollback` | Rollback |
| GET | `/api/v1/wellbeing/score` | Aktueller Wellbeing Score |
| GET | `/api/v1/wellbeing/history` | Score-Verlauf |
| POST | `/api/v1/wellbeing/preferences` | Wellbeing-Einstellungen |

## 22.7 Dashboard & Admin Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/overview` | Dashboard KPIs |
| GET | `/api/v1/dashboard/actions` | Aktions-Feed |
| GET | `/api/v1/dashboard/trust-scores` | Trust Scores Übersicht |
| GET | `/api/v1/audit` | Audit Trail (paginiert) |
| GET | `/api/v1/audit/export` | Audit Trail Export (CSV/JSON) |

## 22.8 Webhook Endpoints (Incoming)

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/gmail` | Gmail Push Notification |
| POST | `/api/v1/webhooks/calendar` | Google Calendar Webhook |
| POST | `/api/v1/webhooks/vapi` | Vapi Call Events |
| POST | `/api/v1/webhooks/n8n` | n8n Workflow Completion |

---

# 23. IMPLEMENTIERUNGS-PHASEN

## Phase 1: Foundation (Wochen 1-8)

**Ziel:** Funktionierender Agent mit Chat, E-Mail und Kalender

- [ ] Monorepo Setup (Backend + Dashboard + Mobile)
- [ ] PostgreSQL Schema + Alembic Migrations
- [ ] FastAPI Basis (Auth, Tenants, CORS, Middleware)
- [ ] LangGraph Supervisor + E-Mail Agent + Kalender Agent
- [ ] Graphiti + FalkorDB Integration
- [ ] Next.js Dashboard (Login, Chat, Overview)
- [ ] Expo App (Login, Chat, Biometric Auth)
- [ ] Gmail MCP Connector
- [ ] Google Calendar MCP Connector
- [ ] Docker Compose für lokale Entwicklung
- [ ] Basis-Tests

## Phase 2: Security & Intelligence (Wochen 9-16)

**Ziel:** DSGVO-konform, multi-tenant, kostenoptimiert

- [ ] Multi-Tenant RLS + Subdomain Routing
- [ ] HashiCorp Vault Integration
- [ ] Audit Trail (Write-Once)
- [ ] Semantisches Caching (Redis + Embeddings)
- [ ] RouteLLM Integration
- [ ] LiteLLM Gateway + Failover
- [ ] Langfuse Observability
- [ ] Presidio PII Filter
- [ ] White-Label Branding
- [ ] Dashboard: Audit Trail, Analytics

## Phase 3: Ambient Agent + App (Wochen 17-24)

**Ziel:** Proaktiver Agent mit App und Voice

- [ ] LangGraph Cron Jobs (Morgen-Briefing, E-Mail Monitor, Fristen)
- [ ] Event-Driven Triggers (Gmail Push, Calendar Webhook)
- [ ] Trust Score System (Progressive Autonomie)
- [ ] Approval Queue + Batch Actions
- [ ] Push Notifications (Expo)
- [ ] Morgen-Briefing (Generator + App Screen)
- [ ] Voice: Deepgram STT + ElevenLabs TTS in App
- [ ] Document Scanner (OCR in App)
- [ ] Swipe-to-Approve in App
- [ ] Vapi Telefon-Agent Integration

## Phase 4: Data Architecture & Connectors (Wochen 25-32)

**Ziel:** Zero-Data-Retention, MCP Gateway, Hybrid-Modell

- [ ] MCP Gateway (Auth, Rate Limit, PII Filter, Audit)
- [ ] HubSpot MCP Connector
- [ ] DATEV MCP Connector
- [ ] n8n Bridge (Workflows als MCP Tools)
- [ ] HTTP Universal Connector (No-Code)
- [ ] Connector Marketplace UI
- [ ] Hybrid Deployment Docker Stack (Model B)
- [ ] Anonymization Pipeline (Cloud↔Kunden-Server)
- [ ] mTLS Gateway (Hybrid-Verbindung)
- [ ] OAuth Token Management in Vault
- [ ] Dashboard: Connector Management

## Phase 5: Der Lebendige Agent (Wochen 33-50)

**Ziel:** Selbstevolution, Weltmodell, Guardian Angel

- [ ] Nightly Reflection Agent
- [ ] Skill Library (Graphiti-basiert)
- [ ] Prompt Versioning + A/B Testing
- [ ] Prompt Evolution Engine (GEPA-inspiriert)
- [ ] Safety Rails für Selbstevolution
- [ ] Business World Model (Counterfactual Reasoning)
- [ ] Outcome Predictor (Monte Carlo auf Graphiti)
- [ ] Proaktive Empfehlungen im Briefing
- [ ] Wellbeing Score Calculator (5 Signale)
- [ ] Work Pattern Monitor
- [ ] Decision Fatigue Tracker
- [ ] Adaptive Load Balancer
- [ ] Kalender-Schutz (Focus Blocks, Abend-Modus)
- [ ] Weekly Wellbeing Report
- [ ] Evolution Dashboard
- [ ] Wellbeing Dashboard + App Widget
- [ ] Full Integration aller drei Level-5-Säulen

## Phase 6: Polish & Scale (Wochen 51+)

- [ ] On-Device AI (ExecuTorch Llama 3.2)
- [ ] Full On-Premise Docker Image (Model C)
- [ ] Connector SDK für Community
- [ ] A2A-Readiness
- [ ] k3s Kubernetes Migration
- [ ] Load Testing + Performance Optimization
- [ ] Security Audit
- [ ] App Store Submission (iOS + Android)

---

# ANHANG

## A. Quellen & Referenzen

Dieses PRD basiert auf umfangreicher Recherche:

- **ICML 2025**: "Truly Self-Improving Agents Require Intrinsic Metacognitive Learning"
- **NeurIPS 2025**: Self-Improving Agents Track (Self-Challenging, SEAL, SiriuS, Voyager)
- **OpenAI Cookbook**: Self-Evolving Agents (Jan 2026)
- **Google DeepMind**: World Model Proof (2025), Genie 3
- **Yann LeCun / AMI Labs**: €500M World Model Startup
- **Anthropic**: MCP Specification (Nov 2024), Registry (Sep 2025)
- **Google**: A2A Protocol (Apr 2025)
- **LangChain**: Ambient Agents Concept, LangGraph Documentation
- **Graphiti / Zep**: Temporal Knowledge Graph, Deep Memory Benchmark
- **SAGE Framework**: Reflective + Memory-Augmented Agents
- **DreamerV3**: Nature Paper (Apr 2025) — World Model Agent
- **Sifted**: Founder Mental Health Survey 2025
- **Gallup**: Burnout Cost Analysis ($322B global)
- **Cisco**: OpenClaw Security Audit (512 Schwachstellen)

## B. Kontakt

**HR Code Labs GbR**
Oliver Hees & Alina Rosenbusch
Hamburg, Deutschland
