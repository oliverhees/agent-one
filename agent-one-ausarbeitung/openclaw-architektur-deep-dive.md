# OpenClaw Architektur entschlüsselt: Von Soul-Dateien bis Agentic Loops

## Deep-Dive-Analyse für den Nachbau als sichere Alternative

**OpenClaw behandelt seinen System-Prompt als kompilierten Output, nicht als Konfiguration.** Bei jedem Agent-Turn wird dynamisch ein Prompt aus über 20 modularen Sektionen zusammengebaut — Persönlichkeitsdateien, Skill-Metadaten, Memory, Tool-Schemas und Laufzeit-Kontext — über `buildAgentSystemPrompt()` in `src/agents/system-prompt.ts`. Dieses Design erzeugt ein System, bei dem der Prompt aus dem Laufzeitstatus emergiert statt aus statischen Templates. Das erklärt sowohl die Stärke als auch die Kosten: **Baseline-System-Prompts verbrauchen 20.000–40.000 Tokens**, bevor der Nutzer eine einzige Nachricht sendet. Ursprünglich im November 2025 von Peter Steinberger als Clawdbot veröffentlicht, dann in Moltbot und schließlich OpenClaw umbenannt, hat das Projekt über **185.000 GitHub-Stars** angesammelt und stellt die vollständigste Open-Source-Implementierung eines autonomen KI-Agenten dar — eine Referenzarchitektur für jeden, der ähnliche Systeme bauen will.

---

## 1. Acht Dateien definieren, wer der Agent ist

Die Persönlichkeit und das Verhalten von OpenClaw entstehen aus acht optionalen Markdown-Dateien im Agent-Workspace (definiert in `src/agents/workspace.ts`), jede mit einem eigenen architektonischen Zweck:

| Datei | Funktion |
|-------|----------|
| **SOUL.md** | Interne Verhaltensphilosophie — *wer der Agent ist*. Persönlichkeit, Werte, Grenzen, Kommunikationsstil |
| **IDENTITY.md** | Externe Darstellung — Name, Emoji, Kreatur-Typ, Vibe, Avatar. Wird als strukturierte Key-Value-Paare geparsed |
| **USER.md** | Besitzer-Profil — Arbeitsmuster, Präferenzen, Zeitzone, Kommunikationsstil |
| **AGENTS.md** | Verhaltensrichtlinien — Coding-Standards, Koordinationsregeln (ähnlich `.cursorrules`) |
| **TOOLS.md** | Nutzer-Anleitung zur Tool-Nutzung (kontrolliert NICHT die Tool-Verfügbarkeit — das ist Policy) |
| **HEARTBEAT.md** | Periodische Checkliste für proaktive Monitoring-Aufgaben |
| **BOOTSTRAP.md** | Einmaliges Erst-Setup-Ritual, wird nach der Ersteinrichtung gelöscht |
| **MEMORY.md** | Persistenter kuratierter Speicher, wird jeden Turn in der Hauptsession injiziert |

### SOUL.md — Das Herz des Agenten

SOUL.md ist **freiformatiges Markdown ohne starres Schema**. Das Standard-Template enthält Sektionen für:

**Core Truths** (Kernwahrheiten): "Be genuinely helpful, not performatively helpful" (Sei wirklich hilfreich, nicht performativ hilfreich)

**Boundaries** (Grenzen): "Private things stay private. Period." (Private Dinge bleiben privat. Punkt.)

**Vibe** (Atmosphäre): "Be the assistant you'd actually want to talk to" (Sei der Assistent, mit dem du selbst reden wollen würdest)

**Continuity** (Kontinuität): "Each session, you wake up fresh. These files *are* your memory" (Jede Session erwachst du frisch. Diese Dateien *sind* dein Gedächtnis)

Die Datei ist explizit als **selbstentwickelnd** konzipiert — dem Agent wird gesagt "This file is yours to evolve" und er wird angewiesen, den Nutzer zu informieren, wenn er seine eigene Seele modifiziert.

### IDENTITY.md — Die Visitenkarte

Verwendet einen strukturierten Typ (`AgentIdentityFile` in `src/agents/identity-file.ts`) mit Feldern für `name`, `emoji`, `theme`, `creature`, `vibe` und `avatar`. Die Identitätsauflösung folgt einer **vierstufigen Kaskade**: Globale UI-Config → Per-Agent-Config → IDENTITY.md-Datei → Fallback "Assistant". Der aufgelöste Name wird als Prefix für ausgehende Nachrichten verwendet, das Emoji wird zur Bestätigungs-Reaktion (Standard: 👀).

**Die Trennung zwischen Soul und Identity ist bewusst**: "Soul is what the model embodies. Identity is what users see." Eine formelle, präzise Seele kann mit einem verspielten Emoji und Spitznamen kombiniert werden — internes Verhalten und externe Präsentation operieren unabhängig.

---

## 2. Die System-Prompt-Assembly-Pipeline

Der vollständige Prompt-Zusammenbau folgt einer **fünfstufigen Pipeline**, die Sektionen in genau dieser Reihenfolge erzeugt:

### Stufe 1: Parameter sammeln
`buildSystemPromptParams()` in `system-prompt-params.ts` sammelt alle Laufzeitparameter: verfügbare Tools, Kanal-Fähigkeiten, Skills-Snapshot, Bootstrap-Dateien, Sandbox-Status und Modell-Metadaten.

### Stufe 2: 23 modulare Sektionen zusammenbauen
`buildAgentSystemPrompt()` in `system-prompt.ts` (Zeilen 129–554) baut folgende Sektionen zusammen:

1. Base Identity (Grundidentität)
2. Tooling (gefilterte Tool-Liste mit JSON-Schemas)
3. Safety Guardrails (keine Selbsterhaltung, Replikation oder Machtstreben)
4. Skills (`<available_skills>` XML-Block)
5. Memory Recall Instructions (Erinnerungsabruf-Anweisungen)
6. Self-Update Instructions (Selbstaktualisierungs-Anweisungen)
7. Workspace Path
8. Documentation Links
9. Sandbox Info
10. Current Date/Time (aktuelles Datum/Uhrzeit)
11. User Identity (Nutzeridentität)
12. Model Aliases
13. Reply Tags
14. Messaging Instructions
15. Voice/TTS
16. Silent Replies
17. Heartbeat Protocol
18. Reactions Guidance
19. Extra System Prompt (Gruppenchat oder Sub-Agent-Kontext)
20. Runtime Metadata
21. Reasoning Visibility
22. **Project Context** (alle Bootstrap-Dateien werden hier injiziert)
23. SOUL.md Directive

### Stufen 3–5: Wrapping und Injektion
Wrappen, Override-Funktion erstellen und den Prompt in die Pi-Agent-Session injizieren über `buildEmbeddedSystemPrompt()` → `createSystemPromptOverride()` → `applySystemPromptOverrideToSession()`.

### Bootstrap-Dateien werden gekürzt
Am konfigurierbaren `bootstrapMaxChars` (Standard **20.000 Zeichen** pro Datei, Quellcode-Konstante `DEFAULT_BOOTSTRAP_MAX_CHARS` = 65.536). Die Kürzung verwendet ein **70/20/10-Verhältnis**: 70% Kopf (Kern-Anweisungen), 20% Ende (aktuelle Updates), 10% Kürzungsmarker. Sub-Agent-Sessions injizieren nur AGENTS.md und TOOLS.md und lassen alle anderen Bootstrap-Dateien weg.

### Drei Prompt-Modi
Diese kontrollieren, was inkludiert wird:

| Modus | Verwendung | Inhalt |
|-------|------------|--------|
| `full` | Haupt-User-Sessions | Alle Sektionen |
| `minimal` | Sub-Agenten | Ohne Skills, Memory, Messaging, Heartbeat, Docs |
| `none` | Basis | Nur die Base-Identity-Zeile |

Der Modus wird zur Laufzeit bestimmt, indem geprüft wird, ob der Session-Key zu einem Sub-Agenten gehört. **Ein voller Prompt mit 4 Bootstrap-Dateien** berichtet typischerweise ~2.700 Tokens allein für den Projekt-Kontext, aber Tool-Schemas (besonders Browser mit ~2.453 Tokens), Skills-Metadaten und große Workspace-Dateien können den **gesamten System-Prompt auf 8.000–40.000+ Tokens** treiben.

---

## 3. Memory lebt in drei Stufen

OpenClaws Memory-Architektur folgt einer **File-first, Markdown-getriebenen Philosophie**, bei der einfache Textdateien auf der Festplatte die kanonische Wahrheitsquelle sind. Ein abgeleiteter Suchindex (SQLite mit `sqlite-vec` und FTS5-Erweiterungen) ermöglicht schnelles Retrieval, aber Dateien sind immer autoritativ.

### Stufe 1 — Kuratierter Langzeitspeicher (MEMORY.md)

Enthält dauerhafte Fakten, Nutzer-Präferenzen, Schlüsselentscheidungen und Projekt-Konventionen. **Wird in den System-Prompt bei jedem Turn in privaten/Hauptsessions injiziert** (nie in Gruppenkontext — automatische Privacy-Grenze). Dies ist die "immer geladene" Stufe. Der Agent wird angewiesen, Entscheidungen, Präferenzen und dauerhafte Fakten hier zu speichern.

### Stufe 2 — Tägliche ephemere Logs (`memory/YYYY-MM-DD.md`)

Append-only-Tagesdateien für laufende Notizen, Beobachtungen und Tageskontext. **Heutige und gestrige Logs werden beim Session-Start geladen.** Ältere Logs sind über `memory_search` und `memory_get`-Tools zugänglich, werden aber nicht automatisch injiziert. Das System erstellt automatisch täglich neue Dateien.

### Stufe 3 — Session-Transkripte (`agents/<agentId>/sessions/<sessionId>.jsonl`)

Vollständige Konversationshistorie als Append-only-JSONL-Eventlogs. Die erste Zeile ist ein Session-Header (`type: "session"` mit `id`, `cwd`, `timestamp`). Nachfolgende Zeilen sind Einträge mit `id` und `parentId`, die eine **Baumstruktur für verzweigende Konversationen** bilden.

Eintragstypen:

| Typ | Beschreibung |
|-----|-------------|
| `user` / `assistant` | Nachrichten |
| `tool_call` / `tool_result` | Tool-Aufrufe und Ergebnisse |
| `compaction` | Zusammenfassungen |
| `branch_summary` | Verzweigungs-Zusammenfassungen |

Wenn experimentell aktiviert (`memorySearch.sources: ["sessions"]`), werden diese Transkripte für semantischen Recall indiziert mit Delta-basierter inkrementeller Indexierung (Schwellenwerte: 100KB neue Daten oder 50 neue Nachrichten).

### Hybrid-Suche: Wie Vektoren und Keywords verschmolzen werden

Das `memory_search`-Tool führt zwei Suchkanäle **parallel** aus und verschmilzt Ergebnisse mittels gewichteter Score-Fusion:

**Vektorsuche** verwendet die `chunks_vec`-Tabelle (sqlite-vec-Erweiterung) für semantische Ähnlichkeit — "Gateway Host" findet "Maschine, die das Gateway betreibt".

**Keyword-Suche** verwendet die `chunks_fts`-Tabelle (SQLite FTS5) mit BM25-Ranking für exakte Tokens — Fehlercodes, Funktionsnamen, Commit-Hashes.

Beide rufen `candidateMultiplier × maxResults` Einträge ab (Standard: **4× = 24 Kandidaten** für 6 finale Ergebnisse).

**Die Merge-Formel:**
```
finalScore = (vectorScore × 0.7) + (textScore × 0.3)
```

BM25-Ränge werden auf [0,1] normalisiert über `score = 1 / (1 + rank)`. Ergebnisse unter einem **minScore-Schwellenwert von 0,35** werden gefiltert, und Deduplizierung erfolgt über `(path, startLine, endLine)` Tupel.

**Graceful Degradation:** Wenn Embeddings nicht verfügbar sind, funktioniert BM25-only-Suche; wenn FTS5 ausfällt, geht nur Vektor weiter; wenn beides versagt, bleiben die rohen Markdown-Dateien lesbar.

### Embedding-Provider-Kaskade

Die automatische Auswahl folgt dieser Kette:

1. **Lokal**: embeddinggemma-300M GGUF (~600MB, via node-llama-cpp)
2. **OpenAI**: `text-embedding-3-small` (1.536 Dimensionen)
3. **Gemini**: `gemini-embedding-001` (768 Dimensionen)
4. **Fallback**: BM25-only

Voyage AI wird ebenfalls nativ unterstützt. Alle Remote-Provider unterstützen Batch-Embedding-APIs für ~50% Kostenreduktion. Der Embedding-Cache verwendet SHA-256 Content-Hashing mit LRU-Eviction bei 50.000 Einträgen, gespeichert in `~/.openclaw/memory/<agentId>.sqlite`.

### Chunking-Algorithmus

Der Algorithmus (`src/memory/internal.ts`) zielt auf **~400 Tokens (~1.600 Zeichen) pro Chunk** mit **80-Token (~320-Zeichen) Überlappung** zwischen aufeinanderfolgenden Chunks ab, wobei Zeilengrenzen für Quellzuordnung erhalten bleiben. Dateiänderungen werden mit **1,5-Sekunden-Debounce** überwacht, und Provider-/Modellwechsel lösen automatische vollständige Neuindizierung aus.

---

## 4. Context-Window-Management — Der Kampf gegen den Token-Verbrauch

### Das Problem

Das Context Window repräsentiert alles, was dem Modell in einem einzelnen Turn gesendet wird: System-Prompt, Konversationshistorie, Tool-Aufrufe/-Ergebnisse, Anhänge und Kompaktierungs-Zusammenfassungen. OpenClaws Ansatz, alle Bootstrap-Workspace-Dateien bei jeder API-Anfrage erneut zu injizieren, hat Kritik auf sich gezogen:

- Eine Analyse fand, dass dies **~35.600 Tokens pro Nachricht verbraucht, was 93,5% Verschwendung** in Mehrfach-Nachrichten-Konversationen ausmacht
- Ein Nutzer berichtete, dass seine Hauptsession **56–58% eines 400K-Fensters** belegt (~230K Tokens gecachter Kontext)

### Context Window Guard

`context-window-guard.ts` erzwingt harte Grenzen bevor Sessions starten:

| Fenstergröße | Aktion |
|--------------|--------|
| < 16K Tokens | Modell wird **komplett abgelehnt** mit `FailoverError` |
| 16K – 32K | Warnung wird ausgegeben |
| 128K+ | Empfohlenes Minimum |
| 200K+ | Ideal |

Während Sessions überwacht der Guard Token-Zählungen und löst Compaction oder Loop-Terminierung aus, **bevor inkohärentes Verhalten entsteht**. Der 20–40K System-Prompt-Overhead lässt bei kleineren Modellen fast keinen Raum.

### Compaction — Der primäre Kontextwiederherstellungsmechanismus

Compaction wird in zwei Fällen ausgelöst:

1. **Overflow Recovery**: Modell gibt Context-Overflow zurück → kompaktieren → erneut versuchen
2. **Threshold Maintenance**: Nach erfolgreichem Turn, wenn `contextTokens > contextWindow - reserveTokens`

Der Standard-`reserveTokensFloor` ist **20.000 Tokens**. Compaction fasst ältere Konversationshistorie in einen persistenten `compaction`-Eintrag im JSONL-Transkript zusammen, während aktuelle Nachrichten intakt bleiben.

### Pre-Compaction Memory Flush — Die Schlüsselinnovation

**Bevor Compaction Konversationsdetails zerstört**, führt OpenClaw einen **stillen agentischen Turn** durch, bei dem der Agent dauerhafte Notizen in `memory/YYYY-MM-DD.md` oder `MEMORY.md` schreibt. Dies transformiert Compaction von "Kontext verlieren" zu "Entscheidungen archivieren".

Der Flush wird ausgelöst bei `contextWindow - reserveTokensFloor - softThresholdTokens` (für ein 200K-Fenster mit Standardeinstellungen: ~176K Tokens). Ein Flush pro Compaction-Zyklus, getrackt über `memoryFlushCompactionCount`.

### Acht Kontext-Management-Techniken

1. **Memory Flush vor Compaction** — Wissen archivieren bevor es komprimiert wird
2. **Context Window Guards** — Harte Grenzen für minimale/maximale Fenstergrößen
3. **Tool Result Guards** — Synthetische Platzhalter für verwaiste Tool-Aufrufe
4. **Turn-basierte History-Limitierung** — Schnitt an Konversationsgrenzen, nicht mitten im Austausch
5. **Cache-bewusstes Tool Result Pruning** — Alte Ergebnisse intelligent entfernen
6. **Head/Tail Content Preservation** — Tool-Ergebnisse >4.000 Zeichen behalten erste 1.500 + letzte 1.500
7. **Adaptive Chunk Ratios** — Dynamische Anpassung der Verhältnisse
8. **Staged Summarization** — Zusammenfassung in Phasen, um Overflow während der Zusammenfassung selbst zu verhindern

---

## 5. Heartbeats machen aus einem Chatbot einen proaktiven Assistenten

### Grundmechanismus

Das Heartbeat-System feuert standardmäßig **alle 30 Minuten** (konfigurierbar via `heartbeat.every`) und läuft in der **Hauptsession** mit vollem Konversationskontext. Der Gateway-Prozess (`src/infra/heartbeat-runner.ts`) besitzt den Scheduler und löst `runHeartbeatOnce()` bei jedem Intervall aus.

### HEARTBEAT.md — Die Checkliste

Eine einfache Markdown-Checkliste im Workspace:

```markdown
# Heartbeat checklist
- Check email for urgent messages
- Review calendar for events in next 2 hours
- If a background task finished, summarize results
- If idle for 8+ hours, send a brief check-in
```

### Ausführungslogik

Wenn der Heartbeat feuert:

1. Agent liest HEARTBEAT.md
2. Prüft auf ausstehende Aufgaben mit vollem Session-Kontext
3. **Trifft eine Entscheidung:**
   - Nichts zu tun → gibt `HEARTBEAT_OK` zurück (spezielles Token, wird aus der Antwort gestrippt, die dann komplett verworfen wird wenn verbleibender Inhalt ≤ 300 Zeichen / `ackMaxChars`)
   - Etwas braucht Aufmerksamkeit → sendet Nachricht an konfigurierten Zielkanal

**Kein Benachrichtigungs-Spam:** `HEARTBEAT_OK`-Antworten aktualisieren `lastUpdatedAt` NICHT, wodurch Idle-Expiry-Verhalten erhalten bleibt.

### Active Hours Filtering

`activeHours.start`/`end` mit Zeitzone überspringt Heartbeats während Schlafenszeiten.

### Kostenoptimierung

- Günstiges Modell-Override für Heartbeats nutzen
- HEARTBEAT.md klein halten
- Rotierende Heartbeat-Muster implementieren: Jeder Tick führt nur die am meisten überfällige Prüfung aus

### Heartbeat vs. Cron — Unterschiedliche Zwecke

| Eigenschaft | Heartbeat | Cron |
|-------------|-----------|------|
| Session | Hauptsession (geteilte Historie) | Isolierte Session (frisch) |
| Kontext | Voller Konversationskontext | Kein Kontext |
| Timing | Periodisch (z.B. 30 Min.) | Exakte Zeitplanung (cron-Syntax) |
| Mehrere Checks | Batchet mehrere kontextbewusste Checks | Ein Job pro Auslöser |

**Wichtig:** Main-Session Cron-Jobs queuen Events, die beim nächsten Heartbeat konsumiert werden. Wenn Heartbeats deaktiviert sind, feuern Main-Session-Cron-Events nie — isolierte Cron-Jobs laufen unabhängig davon.

---

## 6. Skills laden on-demand um Context-Budgets zu schützen

### Skill-Format

Jeder Skill ist ein Verzeichnis mit einer `SKILL.md`-Datei mit **YAML-Frontmatter** und natürlichsprachigen Anweisungen. Das Frontmatter-Format folgt der **AgentSkills-Spezifikation** (adaptiert über Claude Code, Cursor und Copilot):

```yaml
---
name: nano-banana-pro
description: Generate or edit images via Gemini 3 Pro
metadata: { "openclaw": { "emoji": "♊️", "always": true,
  "os": ["darwin", "linux"],
  "requires": { "bins": ["uv"], "env": ["GEMINI_API_KEY"] },
  "install": [{ "kind": "brew", "formula": "gemini-cli" }] } }
---
```

Das `metadata`-Feld muss **einzeiliges JSON** sein (Parser-Einschränkung). Gating-Felder unter `metadata.openclaw`:

| Feld | Funktion |
|------|----------|
| `os` | Betriebssystem-Filter |
| `requires.bins` | Benötigte Binaries im PATH |
| `requires.env` | Benötigte Umgebungsvariablen |
| `requires.config` | Benötigte Config-Keys |
| `install` | Installer-Spezifikationen (brew/node/go/uv/download) |

### Drei Lade-Stufen mit absteigender Priorität

1. **Workspace Skills** (`<workspace>/skills/`) — Höchste Priorität
2. **Managed Skills** (`~/.openclaw/skills/`, installiert via ClawHub)
3. **Bundled Skills** (mit npm-Paket ausgeliefert)

Namensgleiche Konflikte lösen sich nach Stufen-Priorität.

### Die kritische Design-Entscheidung: On-Demand Loading

**Nur Skill-Metadaten** (Name, Beschreibung, Pfad) werden als kompaktes XML in den System-Prompt injiziert. Der vollständige SKILL.md-Inhalt wird **on-demand** via `read`-Tool geladen, nur wenn der Agent einen Skill auswählt.

Der System-Prompt weist an: "Before replying: scan `<available_skills>` description entries. If exactly one skill clearly applies: read its SKILL.md, then follow it. Never read more than one skill upfront."

**Token-Kosten pro Skill:** Ungefähr `97 + len(name) + len(description) + len(location)` Zeichen (~24 Tokens Basis-Overhead). Das verhindert upfront Context Bloat.

### ClawHub — Die Skills-Registry

ClawHub (clawhub.com) dient als öffentliches Skills-Registry mit **2.857+ indizierten Skills**, gebaut auf TanStack Start + Convex + OpenAI Embeddings für Vektorsuche. Skills mit 3+ Nutzer-Reports werden automatisch ausgeblendet, und eine VirusTotal-Partnerschaft bietet Sicherheitsscanning. (Wie in unserer Sicherheitsanalyse festgestellt: **26% der analysierten Skills enthalten Schwachstellen** — daher definitiv nicht direkt nutzen.)

---

## 7. Der Agentic Loop delegiert Planung an das Modell selbst

### Überraschend einfache Architektur

OpenClaws Agent Runner verwendet eine täuschend einfache Architektur:

```
LLM aufrufen → Antwort erhalten → Tool-Aufrufe ausführen → Ergebnisse zurückspeisen → Wiederholen bis fertig
```

**Es gibt keinen expliziten Task-Planer, Step-Tracker oder DAG von Subtasks.** Das Sprachmodell selbst treibt den gesamten Workflow durch iterativen Tool-Einsatz.

### Ausführungspipeline

```
Gateway RPC
  → Session-Auflösung
    → agentCommand
      → runEmbeddedPiAgent (serialisiert Runs via Per-Session + globale FIFO-Queues)
        → Model Resolution + Auth Profile Loading
          → Pi Session Creation
            → Event Subscription
              → Streaming Responses
```

Das System importiert `@mariozechner/pi-agent-core`, `pi-ai` und `pi-coding-agent` als eingebettete Abhängigkeiten (keine Subprozesse).

### Core Pi Tools

| Tool | Funktion |
|------|----------|
| `read` | Dateien lesen |
| `write` | Dateien schreiben |
| `edit` | Dateien bearbeiten |
| `exec` | Bash-Befehle ausführen |
| `process` | Prozesse verwalten |

Erweitert durch OpenClaw-spezifische Tools: `browser`, `canvas`, `nodes`, `cron`, `sessions` und `message`.

### Model Resolver — Multi-Provider-Auswahl

Die Auflösung läuft über: Model-Referenz parsen → Aliase auflösen (z.B. "opus" → "anthropic/claude-opus-4-5") → gegen Katalog validieren → Auth-Profile laden → aufgelöstes Modell + Auth zurückgeben.

### Provider Fallback — Zweistufig

1. **Auth-Profile-Rotation** innerhalb desselben Providers (nächstes Profil bei Rate-Limit/Billing/Auth-Fehlern versuchen)
2. **Modell-Fallback** über Provider hinweg mit konfiguriertem `fallbacks`-Array

**Billing-Fehler** lösen exponentielles Backoff aus (Start 5 Stunden, verdoppelt pro Fehler, Maximum 24 Stunden). **Context-Overflow-Fehler** lösen Compaction aus, NICHT Fallback — eine kritische Unterscheidung.

---

## 8. Das Dateisystem ist die Datenbank

### Vollständige Verzeichnisstruktur

```
~/.openclaw/
├── openclaw.json                    # Haupt-Config (JSON5, Zod-validiert, hot-reloaded)
├── .env                             # Globaler Env-Fallback
├── credentials/                     # API-Keys (chmod 600)
├── agents/<agentId>/
│   ├── agent/auth-profiles.json     # Per-Agent Auth + Cooldown-State
│   ├── models.json                  # Custom Provider-Configs
│   └── sessions/<sessionKey>.jsonl  # Session-Transkripte (JSONL)
├── skills/                          # Managed/Lokale Skills (geteilt)
├── memory/<agentId>.sqlite          # Suchindex (sqlite-vec + FTS5)
├── workspace/                       # Standard-Agent-Workspace
│   ├── SOUL.md                      # Persönlichkeit/Seele
│   ├── USER.md                      # Besitzer-Profil
│   ├── IDENTITY.md                  # Externe Identität
│   ├── AGENTS.md                    # Verhaltensregeln
│   ├── TOOLS.md                     # Tool-Nutzungsanleitung
│   ├── HEARTBEAT.md                 # Proaktive Checkliste
│   ├── BOOTSTRAP.md                 # Ersteinrichtung
│   ├── MEMORY.md                    # Persistenter Speicher
│   ├── memory/YYYY-MM-DD.md         # Tägliche Logs
│   └── skills/                      # Workspace-Skills (höchste Priorität)
├── cron/                            # Cron-Job-Definitionen
└── tools/                           # Installierte Tool-Binaries
```

### Quellcode-Organisation

Das Repository (`github.com/openclaw/openclaw`) organisiert Code unter `src/` mit Schlüsselverzeichnissen:

| Verzeichnis | Inhalt |
|-------------|--------|
| `agents/` | System-Prompt, Skills, Tools, Model Auth, Sandbox, Session Management |
| `config/` | Zod-Schemas, Validierung, Hot Reload |
| `gateway/` | WebSocket-Server, Protokoll |
| `auto-reply/` | Command-System, Compaction |
| `infra/` | Heartbeat Runner |
| `memory/` | Manager, Indexierung |
| Kanal-spezifisch | Telegram, Discord, WhatsApp, etc. |

Das Projekt verwendet pnpm Workspaces mit TypeScript, Node 22+ Runtime und ko-lokalisierte `*.test.ts`-Dateien.

---

## 9. Framework-Empfehlung für den Nachbau

### Übersicht der Optionen

| Framework | Stärken | Schwächen | Eignung |
|-----------|---------|-----------|---------|
| **LangGraph** | Stateful Graphs, eingebautes Checkpointing (PostgresSaver/RedisSaver), LangSmith-Observability | Steile Lernkurve, kein natives Heartbeat/Scheduling | ⭐⭐⭐⭐⭐ Beste Balance |
| **Raw Python/TS** | Maximale Kontrolle, OpenClaw beweist Skalierbarkeit (185K+ Stars) | Maximaler Engineering-Aufwand, keine eingebaute Observability | ⭐⭐⭐⭐ Wenn volle Kontrolle nötig |
| **CrewAI** | Multi-Agent-Rollenspiel, einfaches Setup | Fehlende Feingranularität für Single-Agent-mit-Subagenten | ⭐⭐⭐ Für Multi-Agent-Szenarien |
| **LangChain Base** | Reichstes Integrations-Ökosystem | Überengineert einfache Tasks durch Abstraktionsebenen | ⭐⭐ Zu viel Overhead |

### Empfehlung: LangGraph

**LangGraph bietet die beste Framework-Balance** für die meisten Teams:

- Stateful Directed Graphs passen natürlich auf Agentic Loops (jede Phase als Graph-Knoten mit bedingten Kanten)
- Eingebautes Checkpointing bietet die stärkste persistente Memory-Story
- LangSmith-Integration für Produktions-Observability
- Fehlt: natives Heartbeat/Scheduling (benötigt externen APScheduler) und Multi-Channel-Messaging (benötigt Custom Gateway Layer)

### Context-Window-Optimierung — Die sieben Kerntechniken

Anthropics offizielle Guidance betont, dass **Modellgenauigkeit mit steigender Token-Anzahl abnimmt** — jeder Token verbraucht das Aufmerksamkeitsbudget des Modells:

1. **Compaction** — OpenClaws Ansatz: Ältere Historie zusammenfassen
2. **Strukturierte Notizenführung außerhalb des Kontexts** — Wissen in Dateien auslagern
3. **Sub-Agent-Architektur** mit frischem, minimalem Kontext
4. **Just-in-Time Context Retrieval** — Daten via Tools laden statt vorab
5. **Selektive Kontext-Injektion** pro Agent-Rolle
6. **Prompt-Kompression** — Redundante Formatierung und alte Tool-Ergebnisse entfernen
7. **Konservative Trigger bei 50% Context Usage** statt am Limit

**Der Trend geht zu Context Engineering** — das Context Window als knappe Ressource behandeln, die aktiv gemanagt wird, nicht einfach gefüllt.

---

## 10. Schlüsselerkenntnisse für unseren Nachbau

### Die fünf harten Probleme, die gleichzeitig gelöst werden müssen

1. **Prompt-Assembly aus modularen Komponenten** (nicht monolithische Templates)
2. **Persistenter Memory mit Hybrid-Retrieval** der graceful degraded
3. **Aggressives Context-Window-Management** das archiviert bevor es vergisst
4. **Proaktives Verhalten** das im Auftrag des Nutzers handelt ohne Benachrichtigungs-Spam
5. **Skill-System** das Fähigkeiten entdeckt ohne Context-Budget zu verbrauchen

### Die überraschendste Erkenntnis

**OpenClaw hat keinen expliziten Planer.** Das Sprachmodell selbst treibt den Think-Plan-Act-Observe-Loop durch iterative Tool-Aufrufe. Die Intelligenz steckt in der Prompt-Konstruktion, nicht in einem separaten Reasoning-Engine.

### Die folgenreichste Design-Entscheidung

**File-first Architektur:** Markdown-Dateien auf der Festplatte sind die Wahrheitsquelle für Persönlichkeit, Memory und Konfiguration, mit abgeleiteten Indizes für Suche. Das macht das System inspizierbar, versionskontrollierbar und wiederherstellbar — aber es bedeutet auch, dass der System-Prompt mit jeder Datei wächst, was die **Spannung zwischen Reichhaltigkeit und Effizienz** erzeugt, die OpenClaws laufende Engineering-Herausforderung definiert.

### Was wir für Agent One übernehmen

| OpenClaw-Konzept | Unsere Anpassung |
|------------------|-----------------|
| SOUL.md / IDENTITY.md | Persönlichkeitsdateien mit klarer Trennung intern/extern |
| MEMORY.md + Daily Logs | Persistenter Speicher in NocoDB/Supabase statt Dateien |
| Heartbeat System | APScheduler + LangGraph-Trigger statt Gateway-integriert |
| On-Demand Skill Loading | Skills als LangGraph-Sub-Workflows statt Markdown |
| Hybrid Search | Vektorsuche + Keyword-Suche in PostgreSQL (pgvector + tsvector) |
| Compaction | Strukturierte Zusammenfassung + Pre-Compaction Flush |
| Context Window Guard | Harte Token-Limits mit automatischer Warnung |
| Webhook-Anbindung | REST-API-Endpunkte für n8n/externe Systeme |

### Nächste Schritte

1. **Tech-Stack finalisieren**: Next.js Frontend + Python/LangGraph Backend + PostgreSQL (pgvector)
2. **Persönlichkeitssystem implementieren**: Soul/Identity/User/Memory als DB-Einträge statt Dateien
3. **Agentic Loop mit LangGraph bauen**: Stateful Graph mit Tool-Nodes
4. **Heartbeat-System**: APScheduler mit konfigurierbaren Intervallen
5. **Webhook-Layer**: REST-Endpunkte für n8n-Anbindung
6. **Expo-App Integration**: WebSocket/SSE-Verbindung zum Backend

---

*Quellen: OpenClaw GitHub Repository, DeepWiki-Analyse, OpenClaw Official Docs, MMNTM Architecture Series, Anthropic Context Engineering Guide, diverse Community-Analysen (Medium, Substack, saulius.io)*
