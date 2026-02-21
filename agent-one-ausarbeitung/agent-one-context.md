# AGENT ONE — Vollständiges Projekt-Context-Dokument

**Für:** Claude Code / Claude Projekt Knowledge Base
**Version:** 3.0 — Konsolidiert aus allen Gesprächen (Jan–Feb 2026)
**Erstellt:** 15. Februar 2026
**Autoren:** Oliver Hees & Alina Rosenbusch (HR Code Labs GbR)
**Status:** 70% implementiert — Eigener Neubau (kein Fork)

---

## LESEHINWEIS FÜR CLAUDE

Dieses Dokument enthält ALLE strategischen und technischen Entscheidungen für Agent One. Es fasst zusammen:
- Das vollständige PRD (2.315 Zeilen / 90KB — separat verfügbar)
- Die Projektbeschreibung (Marktanalyse, Business Case, GTM)
- Die OpenClaw-Analyse und Fork-Entscheidung
- Alle Architektur-Entscheidungen der letzten Wochen

Wenn du Code schreibst oder Architektur-Fragen beantworten musst, findest du hier den vollständigen Kontext.

---

## 1. WAS IST AGENT ONE?

Agent One ist ein **proaktiver KI-Mitarbeiter für deutsche KMUs** — speziell für Berufsgeheimnisträger nach §203 StGB (Steuerberater, Anwälte, Ärzte). Kein Chatbot. Kein Tool. Ein digitaler Partner der mitdenkt, vorausplant und auf die Gesundheit des Nutzers achtet.

### Das Versprechen
> "Wir sorgen dafür, dass du langfristig erfolgreich UND gesund bleibst. Dein Agent arbeitet FÜR dich und passt AUF dich auf."

### Täglicher Workflow (Ziel-UX)
1. 07:00 — Push-Notification: "Guten Morgen Oliver. 3 dringende Mails, 2 Termine, Frist für Mandant Schulz in 48h. Hier dein Briefing."
2. Nutzer öffnet App → Swipe-to-Approve für vorbereitete Aktionen
3. Sprachbefehl: "Hey Agent, verschieb den Call mit Benjamin auf 11 Uhr"
4. Agent bestätigt per Sprache, informiert Benjamin per Mail, aktualisiert Kalender
5. Nachts: Agent analysiert eigene Performance, optimiert Prompts, baut Skill Library aus

### Was Agent One NICHT ist
- Kein generischer Chatbot (wie ChatGPT)
- Kein Enterprise-Tool (wie Salesforce Agentforce)
- Kein No-Code Builder (wie n8n oder Make) — der Steuerberater soll NUTZEN nicht BAUEN
- Kein OpenClaw-Fork (Entscheidung vom 15.02.2026 — siehe Abschnitt 8)

---

## 2. ZIELGRUPPE & MARKT

### Primäre Zielgruppe: §203 StGB Berufsgeheimnisträger

| Segment | Anzahl (DE) | Pain Level | Zahlungsbereitschaft |
|---------|-------------|------------|---------------------|
| Steuerberater | 53.800 Praxen | ★★★★★ | Hoch (Ø €191K Überschuss/Inhaber) |
| Anwälte | 47.300 Kanzleien | ★★★★☆ | Mittel-Hoch |
| Ärzte/Therapeuten | ~47.000 Praxen | ★★★☆☆ | Mittel |
| **Gesamt TAM** | **~148.000** | | |

### Warum Steuerberater ZUERST
- **Fachkräftemangel:** 75% der Kanzleien müssen Aufträge ablehnen (ifo 2023)
- **Deadline-Druck:** Steuererklärungen, USt-VA, Jahresabschlüsse — alles fristgebunden
- **DATEV-Digitalisierungsdruck:** Branche im Umbruch
- **Direkter Zugang:** Pilotkunde Benjamin Arras (Steuerberater), Community-Netzwerk
- **Klar definierter Markt:** Überschaubar, gut erreichbar, Budget vorhanden

### Markt-Gap (WARUM es Agent One noch nicht gibt)
1. **Datenschutz-Angst:** "Wo sind meine Mandantendaten?" — kein US-Provider kann das zufriedenstellend beantworten
2. **Regulatorische Komplexität:** DSGVO + EU AI Act + BSI Grundschutz + §203 StGB = Overkill für Startups
3. **Fehlende Branchenlösung:** ChatGPT ist generisch, Salesforce ist Enterprise, nichts ist gebaut für 5-50 MA Steuerkanzlei
4. **Professionelle Hürden:** §203 StGB macht Cloud-Lösungen zum juristischen Minenfeld

### Marktdaten (verifiziert)
- Deutscher KI-Markt: €10 Mrd. (2025) → €32 Mrd. (2030)
- Nur 20% deutsche Unternehmen nutzen aktiv KI (Bitkom Feb 2025)
- Mittelstand investiert ~30% weniger in KI als Gesamtmarkt (Horváth Jan 2026)
- 82% planen Budget-Erhöhungen — Blocker ist NICHT fehlendes Interesse
- Gartner: 40% Enterprise Apps integrieren Task-spezifische AI Agents bis Ende 2026 (von <5% Anfang 2025)

---

## 3. BUSINESS MODEL & FINANZEN

### Pricing

| Tier | Preis/Mo | Zielgruppe |
|------|----------|-----------|
| Starter | €149 | Einzelkämpfer, erste Automatisierung |
| Professional | €299 | Kanzlei 5-15 MA, voller Funktionsumfang |
| Enterprise | €499 | Große Kanzlei, Multi-Agent, SLA |
| Level 5 Premium | +€200 | Selbstevolution, Guardian Angel, World Model |
| On-Premise | €999+ | Kliniken, Behörden, maximale Kontrolle |

### Zusätzliche Revenue Streams
- Connector Marketplace: 20% Revenue Share
- Setup-Fees: einmalig
- Consulting: €150/h
- White-Label: €999/Mo für Netzwerke/Verbände

### Unit Economics (Professional Tier)
- Revenue: €299/Mo
- Kosten: €25-52/Mo (LLM €15-30, Infra €1-3, Push €0.50, Voice €3-8, Support €5-10)
- **Gross Margin: 83-92%**
- CAC: ~€200 (Content + Referral)
- Payback: <1 Monat
- LTV (24 Mo): ~€7.176
- **LTV/CAC: ~36x**

### Break-Even: ~21 zahlende Kunden

### Finanzprognose (Konservativ)

| Zeitpunkt | Kunden | MRR | ARR |
|-----------|--------|-----|-----|
| Mo 6 | 20 | €4K | €48K |
| Mo 12 | 80 | €20K | €240K |
| Mo 24 | 400 | €108K | €1.3M |
| Mo 36 | 1.200 | €360K | €4.3M |

### Deployment-Modelle

| Modell | Anteil | Für wen |
|--------|--------|---------|
| Full Cloud SaaS | ~80% | Standard-Kunden |
| Hybrid | ~15% | §203-Berufe (Daten beim Kunden, Intelligenz bei uns) |
| Full On-Premise | ~5% | Kliniken, Behörden, maximale Paranoia |

Hosting: **Hetzner Cloud** (Nürnberg/Falkenstein — deutsche Server, DSGVO-konform)

---

## 4. DIE 5 ARCHITEKTUR-LEVEL

### Level 1 — Das Fundament
**LangGraph Multi-Agent + Graphiti Temporal Knowledge Graph + FalkorDB**

Der Agent hat ein Gedächtnis das nicht nur speichert WAS passiert ist, sondern WANN Fakten gültig und ungültig wurden. Graphiti extrahiert automatisch Entitäten und Beziehungen aus unstrukturierten Gesprächen.

Statt OpenClaws flacher MEMORY.md (4.000 Token, Compaction zerstört Memories):
→ Graphiti Entity Extraction + Bi-temporale Relationen + Hybrid Search (Semantic + BM25 + Graph)
→ 200 Token relevante Fakten statt 4.000 Token Dump = **95% Kostenersparnis**

### Level 2 — Die Festung (DSGVO)
- Multi-Tenant mit **Row-Level-Security** (PostgreSQL)
- 4-Schichten-Datenisolation
- **HashiCorp Vault** für Secrets (nicht .env)
- **Microsoft Presidio** für PII-Filterung VOR LLM-Calls
- **Write-Once Audit Trail** (BSI Grundschutz++)
- Intelligentes **Semantic Caching** (Redis): 75-95% Kostensenkung
- **RouteLLM** + **LiteLLM**: Multi-Provider, 95% GPT-4-Qualität bei 14-26% der Kosten
- Next.js Dashboard mit White-Label Support

### Level 3 — Der Ambient Agent (Proaktivität)
**Paradigmenwechsel: Agent handelt PROAKTIV statt auf Befehle zu warten.**

Basierend auf Harrison Chases "Ambient Agents" Konzept (LangChain, Jan 2025):

**Vier Schichten proaktiver Intelligenz:**
1. Reaktion: Agent antwortet auf direkte Anfragen
2. Monitoring: Agent überwacht und benachrichtigt (Push)
3. Proaktivität: Agent erkennt Situation und handelt
4. Antizipation: Agent sagt voraus was du brauchen wirst

**Progressive Autonomie (Trust Scores):**
```
[E-Mail an bestehende Mandanten senden]
  Genehmigt: 47x | Abgelehnt: 2x | Bearbeitet: 5x
  → Trust Score: 87% → AUTO-GENEHMIGT (Schwellenwert: 85%)

[E-Mail an unbekannte Kontakte senden]
  Genehmigt: 3x | Abgelehnt: 4x | Bearbeitet: 6x
  → Trust Score: 23% → IMMER GENEHMIGUNG ERFORDERLICH
```
- Neue Aktionstypen starten IMMER bei 0% Trust
- Agent verdient sich Autonomie durch Zuverlässigkeit
- Nutzer behält immer die Kontrolle

**Drei HITL-Patterns (Human-in-the-Loop):**
1. **Notify:** Agent flaggt etwas Wichtiges, handelt NICHT
2. **Question:** Agent braucht Input um weiterzumachen
3. **Review:** Agent hat etwas vorbereitet, braucht Freigabe (Swipe-to-Approve)

**LangGraph Cron Jobs** für Hintergrund-Tasks:
- Morgen-Briefing (täglich 07:00)
- E-Mail-Monitoring (alle 5 Min)
- Fristen-Wächter (täglich 08:00)
- Wochen-Review (freitags 16:00)

**Event-Driven Triggers:**
- Neue E-Mail → Kategorisieren, Frist extrahieren, Antwort entwerfen
- Verpasster Anruf → Rückruf planen, Voicemail zusammenfassen
- Kalendererinnerung → Vorbereitung zusammenstellen
- Frist nähert sich → Erinnerung an Mandant
- Neuer Mandant → Willkommens-Workflow
- Dokument eingegangen → OCR, Klassifizierung, Ablage

**Mobile App** (das Herzstück — siehe Abschnitt 6)

### Level 4 — Zero-Data-Architektur
**Agent liest Daten aus Kundensystemen via MCP, denkt nach, schreibt zurück. Nur abstrahierte Fakten werden im Graph gespeichert.**

- **MCP Gateway** als universelle Connector-Schicht
- **n8n Bridge** für 1.200+ Integrationen (bidirektional)
- **HTTP Universal Connector**: Jede REST API in 5 Min via UI anbindbar
- Drei Deployment-Modelle (Cloud, Hybrid, On-Premise)

### Level 5 — Der Lebendige Agent

**Selbstevolution:**
- Nightly Reflection: Agent analysiert eigene Performance
- Skill Library: Erfolgreiche Patterns werden extrahiert und wiederverwendet
- Prompt Evolution: A/B-Testing eigener Prompts mit Auto-Rollback
- Safety Rail: Agent darf Prompts ändern, NIEMALS Code

**Business World Model:**
- Counterfactual Reasoning auf Graphiti-Temporaldaten
- "Was passiert wenn wir Mandant Schulz nicht heute erinnern?" → 34% Wahrscheinlichkeit verspäteter Unterlagen
- Simuliert Szenarien bevor Handlungen ausgeführt werden

**Guardian Angel (Wellbeing):**
- Wellbeing Score aus 5 Signalen: Arbeitszeiten, Entscheidungslast, Pausen, freie Tage, Kommunikationston
- "Du arbeitest seit 14 Tagen ohne Pause. Wellbeing Score: 4/10. Soll ich diese Woche mehr automatisch übernehmen?"
- Adaptive Load Balancer: Bei niedrigem Wellbeing-Score verschiebt Agent nicht-dringende Tasks

---

## 5. TECH STACK (AKTUELL — EIGENER NEUBAU)

### 5.1 Backend
```
Agent One Backend (Python — EIGENER NEUBAU)
├── Framework: FastAPI
├── Agent Runtime: LangGraph Multi-Agent
├── Memory: Graphiti Engine → FalkorDB (Sub-10ms Graph Queries)
├── Database: PostgreSQL + Row-Level-Security (Multi-Tenant)
├── Cache: Redis (Semantic Caching)
├── LLM Router: LiteLLM + RouteLLM (Multi-Provider)
├── Observability: Langfuse (Tracing, Kosten-Tracking)
├── Security: HashiCorp Vault, Presidio (PII), Audit Trail
├── n8n Bridge: Bidirektionale Integration
└── MCP Gateway: Universal Connector Layer
```

### 5.2 Dashboard
```
React App (EXISTIERT — 70% fertig)
├── Multi-Tenant Admin Panel
├── Knowledge Graph Visualizer (geplant: D3.js/Cytoscape)
├── Cost Intelligence Dashboard
├── Approval Workflow UI
├── White-Label Support (geplant)
└── DSGVO Compliance Center (geplant)
```

**WICHTIG:** Das Dashboard ist aktuell eine React App (NICHT Next.js). Das ist der aktuelle Ist-Zustand der 70%-fertigen Implementierung.

### 5.3 Mobile App (GEPLANT — Kommerziell)

**Entscheidung offen: React Native (Expo) vs. Flutter**

Argumente für Flutter (aus vorherigem Chat):
- Nativer ARM-Code, kein Bridge → bessere Audio-Performance
- Porcupine Wake Word Flutter-Plugin mit Background Listening out of the box
- TensorFlow Lite + Dart FFI für On-Device AI
- Impeller Engine: konstante 60/120 FPS

Argumente für React Native / Expo:
- Oliver hat bereits React-Erfahrung (Dashboard ist React)
- Expo hat verbessertes Background-Handling
- Teilweise Code-Wiederverwendung mit Dashboard möglich
- TypeScript-Ökosystem konsistent

**OFFENE FRAGE: "Awake" / Background Execution ist das größte Thema.** Für einen proaktiven Agent der Push Notifications, Wake Word Listening und Hintergrund-Monitoring braucht, ist die Background-Execution-Fähigkeit des Frameworks entscheidend.

### 5.4 Mobile App Features (geplant)
```
Mobile App
├── Wake Word: "Hey Agent" (offline, deutsch — Porcupine)
├── Live Voice: WebRTC (Chained Architecture: Deepgram STT → LLM → ElevenLabs TTS)
│   └── Ziel-Latenz: ~600ms End-to-End
├── Push Notifications (Rich Briefings, Ambient Agent)
├── Biometric Auth (Face ID / Fingerprint)
├── Swipe-to-Approve (Agent Inbox mit Approve/Reject/Edit)
├── Voice Memos → Graphiti (Sprache direkt in Knowledge Graph)
├── Knowledge Graph Browser (Graph mobil durchsuchen)
├── Cost Dashboard (Token-Verbrauch in Echtzeit)
├── On-Device AI: Llama 3.2 1B (ExecuTorch) oder TFLite (Offline-Triage)
├── Dokument-Scanner → Agent Pipeline
└── §203-Modus Toggle
```

### 5.5 Infrastruktur
```
Docker Compose Stack (One-Click Deploy)
├── Agent One Backend (FastAPI + LangGraph)
├── FalkorDB (Graphiti)
├── PostgreSQL
├── Redis
├── n8n (optional, für Power-User)
├── Reverse Proxy (Caddy mit Auto-TLS)
└── Monitoring (Grafana + Prometheus)

Hosting: Hetzner Cloud (Nürnberg/Falkenstein)
```

---

## 6. VOICE-ARCHITEKTUR (DETAIL)

### Voice-Prioritätspyramide
1. **In-App Voice** (Höchste Prio): App öffnen → Mikrofon → sprechen → natürliche deutsche Antwort
2. **Wake Word**: "Hey Agent" → Agent hört zu → antwortet mit natürlicher Stimme (Porcupine, offline, deutsch)
3. **Telefon-Integration**: Vapi für eingehende/ausgehende Anrufe
4. **Hintergrund-Channels**: WhatsApp, Telegram, Slack als optionale Convenience
5. **Proaktivität**: Die Krone — Morgen-Briefing, Auto-Antworten, Frist-Warnungen

### Chained Voice Architecture
```
User spricht
    ↓
Porcupine Wake Word (on-device, offline)
    ↓
Deepgram STT (Nova-2, deutsch, streaming)
    ↓
LangGraph Agent (Denken + Handeln)
    ↓
ElevenLabs TTS (deutsche Stimme, streaming)
    ↓
User hört Antwort (~600ms Gesamtlatenz)
```

### Warum NICHT OpenAI Realtime API allein
- $100/h Gesprächskosten (unhaltbar für KMU)
- Keine Kontrolle über Agent-Logik zwischen STT und TTS
- Chained Architecture: Deepgram ($0.0043/min) + ElevenLabs ($0.30/1K chars) = ~€0.08-0.15/Gespräch

---

## 7. WETTBEWERBS-MATRIX

| Feature | OpenClaw | ChatGPT | Salesforce | Agent One |
|---------|----------|---------|------------|-----------|
| Channels (WhatsApp, Telegram etc.) | ✅ 15+ | ❌ | ❌ | ✅ (via MCP+n8n) |
| DSGVO / §203 StGB Compliance | ❌ | ❌ | Teilweise | ✅ |
| Deutsche Server | ❌ | ❌ | ❌ | ✅ Hetzner |
| Temporaler Knowledge Graph | ❌ | ❌ | ❌ | ✅ Graphiti |
| Progressive Autonomie | ❌ | ❌ | ❌ | ✅ Trust Scores |
| Native Mobile App | ❌ | Teilweise | ❌ | ✅ |
| Wake Word | ❌ | ❌ | ❌ | ✅ Porcupine |
| Live Voice Conversation | ❌ | ✅ (teuer) | ❌ | ✅ Chained |
| Ambient/Proaktiv | ❌ | ❌ | Teilweise | ✅ |
| n8n Integration | ❌ | ❌ | ❌ | ✅ Nativ |
| Multi-Agent | Begrenzt | ❌ | ✅ | ✅ LangGraph |
| Cost Intelligence | Basis | ❌ | ❌ | ✅ RouteLLM+Cache |
| Selbstevolution | ❌ | ❌ | ❌ | ✅ Level 5 |
| Guardian Angel (Wellbeing) | ❌ | ❌ | ❌ | ✅ Level 5 |
| Bezahlbar für KMU (<€500/Mo) | Kostenlos | €20-200 | €1000+ | ✅ €149-499 |

---

## 8. KRITISCHE ENTSCHEIDUNG: KEIN OPENCLAW-FORK

### Entscheidung (15. Februar 2026): Eigener Neubau, kein Fork

### Warum NICHT forken

**1. 120 Commits/Tag = Fork sofort tot**
OpenClaw hat 500+ Contributors und ~120 tägliche Commits. Ein Fork eines solchen Repos ist kein Fork — es ist ein Snapshot der in 48 Stunden obsolet ist. Optionen: ständig Upstream mergen (Vollzeit-Job mit Merge-Konflikten) oder Fork einfrieren und allein maintainen (dann ist es ein eigenes Projekt, kein Fork). Beides ist Wahnsinn.

**2. Inkompatible Architekturen**
- OpenClaw: TypeScript, Node.js, CLI Daemon, lokaler Desktop-Agent, MEMORY.md + SQLite
- Agent One: Python, FastAPI, LangGraph, Multi-Tenant Cloud SaaS, Graphiti + FalkorDB, Mobile App
- Keine wiederverwendbaren Komponenten — unterschiedliche Sprache, Deployment, Memory, Security-Modell

**3. 512 Vulnerabilities, 21.639 exponierte Instanzen**
- CVE-2026-25253: One-Click RCE
- 63% der Instanzen verwundbar
- 7,1% der ClawHub Skills sind Malware
- Gateway bindet auf 0.0.0.0 — alles offen

**4. Wir sind 70% fertig mit dem Neubau**
Funktionierende React App + Backend. Fork bedeutet: Wochen Arbeit wegwerfen, fremden TypeScript-Code verstehen, 512 Vulnerabilities fixen.

**5. Grundverschiedene Produkt-Philosophie**
OpenClaw = "Power User Playground" (CLI, Node.js >= 22, Gateway-Konfiguration, manuelle MEMORY.md)
Agent One = "It just works" (Steuerberater öffnet App morgens, sieht Briefing, Swipe-Approve, fertig)

### Was wir von OpenClaw ÜBERNEHMEN (Ideen, kein Code)
- Channel-Adapter-Konzept → als MCP Connectors in unserer Architektur
- Skill Marketplace Idee → als signierte, sandboxed Plugins in unserem Store
- Heartbeat/Cron Pattern → bereits besser gelöst mit LangGraph Cron Jobs
- SOUL.md Persönlichkeit → ähnliches Konzept für Agent-Persönlichkeit
- Community-Aufmerksamkeit → Positionierung als "sichere, einfache Alternative für Nicht-Entwickler"

---

## 9. TECHNISCHE DIFFERENZIERUNG (7 MOATS)

1. **Temporaler Knowledge Graph (Graphiti + FalkorDB):** Trackt WANN Fakten gültig/ungültig waren. Ermöglicht World Model Pattern Recognition.

2. **Progressive Autonomie (Trust Score):** Agent verdient Autonomie durch bewiesene Zuverlässigkeit. Neue Aktionstypen starten bei 0%.

3. **Zero-Data-Retention:** Agent liest aus Kundensystemen via MCP, denkt, schreibt zurück — nur abstrahierte Fakten im Graph.

4. **Selbstevolution (Level 5):** Nightly Analysis, Lessons aus Edits extrahieren, eigene Prompts verbessern mit A/B-Testing und Auto-Rollback.

5. **Guardian Angel:** Trackt Arbeitszeiten, Entscheidungslast, Pausen, freie Tage — interveniert wenn Wellbeing Score sinkt.

6. **MCP + n8n = 1.200+ Integrationen:** Standardisierte Connector-Schicht plus HTTP Universal Connector (jede REST API in 5 Min via UI).

7. **On-Device AI:** Llama 3.2 1B auf Smartphone via ExecuTorch für DSGVO-kritische Clients.

**Warum schwer zu kopieren:** Einzelne Komponenten sind Open Source, aber die Kombination erfordert 12+ Monate Entwicklung und tiefes Domain-Wissen. Das gelernte Wissen des Agents nach 12 Monaten beim Kunden erzeugt echte Switching Costs.

---

## 10. TEAM & RESSOURCEN

- **Oliver Hees:** 20 Jahre Software-Dev, n8n/AI-Spezialisierung, YouTube (~2.700 Subs), TikTok (~3.000 Follower), AI Automation Engineers Community (200+ Mitglieder), bestehende §203-Kundenbeziehungen. Vollzeit Agent One ab März 2026.
- **Alina Rosenbusch:** Co-Founder, Business Development, Kundenbeziehungen, Projektmanagement.
- **"Secret Weapon":** Claude Code als Entwickler — PRD ist so geschrieben dass Claude Code alles implementieren kann.

### Olivers Tech-Profil
- 20 Jahre: WordPress, Full Stack, Next.js, diverse Web-Technologien
- Aktuell: n8n, AI Automation, Voice AI, LangGraph
- OS: Pop!_OS (Linux)
- Präferenz: Self-hosted (Coolify), Open Source, Production-ready
- Style: Energisch, humorvoll, experimentierfreudig, ADHS-bedingte Organisations-Challenges

### Skalierung
- Bootstrap (Mo 1-6): 2 Founder + Claude Code, €3-5K/Mo
- Erste Revenue (Mo 6-12): +1 Student, €5-7K/Mo
- Growth (Mo 12-24): +1 Senior Dev +1 CS, €12-18K/Mo
- Scale (Mo 24-36): +2 Devs +1 Sales +1 Marketing, €30-45K/Mo

---

## 11. GO-TO-MARKET

### Phase 1 (Monat 1-6): Community + Content + Erste Kunden
- YouTube-Inhalte zu Agent One Entwicklung (Build in Public)
- AI Automation Engineers Community als Early Adopter Pool
- Benjamin Arras (Steuerberater) als Pilotkunde
- 5-10 Beta-Kunden über persönliches Netzwerk

### Phase 2 (Monat 6-12): Referenzen + Partnerschaften
- Steuerberater-Verbände, IHK
- DATEV-Berater-Kooperation (Agent ergänzt DATEV, ersetzt es nicht)
- Konferenzen, Webinare
- Case Studies von Pilotkunden

### Phase 3 (Jahr 2+): Skalierung
- White-Label für Netzwerke
- Connector Marketplace
- Internationalisierung: Österreich, Schweiz

---

## 12. ROADMAP

### 2026 Q1 (Feb–Apr): Foundation + MVP
- Monorepo aufsetzen
- Backend: FastAPI + LangGraph Basis
- Dashboard v1 (React — existiert zu 70%)
- Mobile App v1 (Grundstruktur)
- Gmail/Calendar Connectors (MCP)
- 3-5 Alpha-Tester

### 2026 Q2 (Mai–Jul): Security + Proaktivität
- Multi-Tenant + DSGVO (Level 2)
- Audit Trail
- Trust Scores + Approval Gates
- Morgen-Briefing + Cron Jobs
- Voice Integration (Deepgram + ElevenLabs)
- Vapi Telefon-Integration
- 10-20 Beta-Kunden

### 2026 Q3 (Aug–Okt): Connectors + Scaling
- MCP Gateway
- n8n Bridge (bidirektional)
- DATEV/HubSpot Connectors
- Hybrid Deployment
- White-Label v1
- 50-80 zahlende Kunden

### 2026 Q4 (Nov–Dez): Level 5 + Growth
- Self-Evolution Engine
- World Model
- Guardian Angel
- App Store Launch
- 80-150 zahlende Kunden

### 2027 Q1: Optimierung + Scale
- Prompt Evolution mit A/B-Testing
- Connector Marketplace
- On-Device AI
- 200-400 Kunden → €100K+ MRR

### Milestones
- **MVP funktional:** Ende März 2026
- **Erster zahlender Kunde:** April 2026
- **Product-Market Fit:** Juli 2026 (NPS >50, Churn <5%, 20+ Kunden)
- **€25K MRR:** Oktober 2026
- **Level 5 live:** Dezember 2026
- **€100K MRR:** Q1 2027

---

## 13. RISIKEN & MITIGATION

| Risiko | Mitigation |
|--------|-----------|
| LLM-Kosten steigen | RouteLLM + Caching + Multi-Provider (Anthropic, OpenAI, Mistral, Llama) |
| LLM-Qualität schwankt | A/B-Testing, Monitoring, automatische Fallbacks |
| Langsame Adoption | Content Marketing + Community + persönliche Demos |
| DATEV blockiert | Agent ergänzt DATEV, ersetzt nicht. n8n Workaround. |
| Großer Player tritt ein | First-Mover + Switching Costs + Branchen-Fokus + deutsche Compliance |
| KI-Hype lässt nach | Messbarer ROI ("Agent spart 4,5h/Woche, kostet €299/Mo") |
| Wirtschaftskrise | Agent spart Personalkosten = antizyklisch |

---

## 14. AKTUELLER STAND (15.02.2026)

### Was EXISTIERT (70%)
- React Dashboard App (funktionsfähig)
- Backend-Grundstruktur
- Grundlegende Agent-Logik

### Was FEHLT (30%)
- Graphiti/FalkorDB Integration
- Multi-Tenant + DSGVO-Schicht
- Mobile App (komplett)
- Voice-Integration
- MCP Gateway + n8n Bridge
- Trust Scores + Approval Gates
- Level 5 Features
- Produktions-Deployment

### Nächste Schritte für Claude Code
1. **Repo analysieren:** Aktuellen Code verstehen, Architektur bewerten
2. **Graphiti integrieren:** FalkorDB + Graphiti als Memory-Layer einbauen
3. **Multi-Tenant:** PostgreSQL RLS, Tenant-Isolation
4. **Mobile App starten:** Framework-Entscheidung (Expo vs Flutter) + Grundstruktur
5. **Voice MVP:** Deepgram STT + ElevenLabs TTS + WebSocket-Streaming

---

## 15. REFERENZ-DOKUMENTE

- **PRD (vollständig):** 2.315 Zeilen, 90KB — enthält detaillierte API-Specs, Datenmodelle, Implementierungs-Details für alle 5 Level
- **Projektbeschreibung:** Marktanalyse, Business Case, GTM, Finanzprognosen
- **OpenClaw-Analyse:** Security Audit, Architektur-Vergleich, Fork-Entscheidung

Diese Dokumente wurden in separaten Claude-Chats erstellt und können bei Bedarf über Past Chats durchsucht werden.

---

## 16. KONVENTIONEN & HINWEISE FÜR CLAUDE CODE

### Sprache
- Code: Englisch (Variablen, Kommentare, Commits)
- UI-Texte: Deutsch (Zielgruppe ist DACH)
- Dokumentation: Deutsch (Oliver bevorzugt)

### Tech-Präferenzen (Oliver)
- Self-hosted wo möglich (Coolify)
- Open Source bevorzugt
- Production-ready, keine Prototyp-Qualität
- Docker Compose für alles
- Hosting-Empfehlung: Hostinger KVM 2+ (Link: https://hostinger.com/kiheroes, Code: KIHEROES, 5% Rabatt)
- OS: Pop!_OS

### Architektur-Regeln
- KEIN OpenClaw-Code verwenden — komplett eigener Neubau
- Python Backend (FastAPI + LangGraph), NICHT TypeScript/Node
- Graphiti + FalkorDB als Memory, NICHT SQLite/MEMORY.md
- Multi-Tenant by Design von Tag 1
- DSGVO/§203 als Architektur-Prinzip, nicht als Nachgedanke
- Safety first: Agent darf Prompts ändern, NIEMALS Code ausführen

---

*Dieses Dokument konsolidiert alle Gespräche zwischen Oliver Hees und Claude (Januar–Februar 2026) zum Thema Agent One. Es dient als Single Source of Truth für die weitere Entwicklung mit Claude Code.*
