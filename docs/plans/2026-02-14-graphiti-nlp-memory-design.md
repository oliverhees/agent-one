# ALICE Memory System – Graphiti + NLP Design

**Datum:** 2026-02-14
**Status:** Genehmigt
**Phase:** 5 (Knowledge Graph & NLP)

---

## Zusammenfassung

ALICE erhaelt ein persistentes Gedaechtnis basierend auf Graphiti (temporaler Knowledge Graph) mit FalkorDB als Backend. Jedes Gespraech wird als Episode analysiert: Fakten werden in den Knowledge Graph extrahiert, ADHS-spezifische Verhaltensmuster erkannt und Stimmungs-/Fokus-Scores ueber Zeit getrackt. Vor jeder Chat-Antwort wird der System Prompt mit relevantem Wissen und Verhaltenstrends angereichert.

**Ziele:**
- ALICE merkt sich Fakten ueber den User (Personen, Orte, Vorlieben, Trigger)
- ALICE erkennt ADHS-Muster (Prokrastination, Hyperfokus, Task-Switching, etc.) und reagiert praediktiv
- Fakten fliessen unsichtbar ein (System Prompt), Muster-Erkennungen werden explizit angesprochen
- System entdeckt automatisch neue Muster und schlaegt sie dem User vor

---

## Ansatz

**Gewaehlt: Full Graphiti mit FalkorDB**

Graphiti mit FalkorDB als zentrales Gedaechtnis. Jedes Gespraech wird als Episode eingespeist. Graphiti uebernimmt Entity-Extraktion, Relationen und temporale Verwaltung automatisch via LLM.

**Verworfen:**
- DIY mit PostgreSQL + pgvector: Zu viel eigener Code, kein temporales Graph-Modell
- Zep Cloud (Managed): DSGVO/Paragraph 203 StGB Risiko bei US-Anbieter mit therapie-nahen Daten

---

## Architektur

```
User Chat --> FastAPI Chat Endpoint
                    |
                    +-> [Sync] ContextBuilder.enrich_system_prompt()  (~300ms)
                    |     +-> Graphiti.search(user_query)
                    |     +-> PatternAnalyzer.get_recent_trends(user_id)
                    |     +-> Merged in System Prompt
                    |
                    +-> Claude API (Chat-Antwort wie bisher)
                    |
                    +-> [Async] EpisodeCollector
                              |
                              v
                    ConversationEnd Event (5min Inaktivitaet)
                              |
                              v
                    MemoryService.process_episode()
                              |
                    +---------+----------+
                    |                    |
                    v                    v
              Graphiti                NLP Analyzer
              add_episode()          (Stimmung, Muster)
                    |                    |
                    v                    v
              FalkorDB              PostgreSQL
              (Knowledge Graph)     (pattern_logs)
```

### Kernkomponenten

1. **MemoryService** – Orchestriert Graphiti und NLP-Analyse
2. **EpisodeCollector** – Sammelt Nachrichten pro Gespraech, triggert Verarbeitung bei Gespraechsende
3. **NLPAnalyzer** – Stimmung, Energie, ADHS-Muster pro Episode (ein Claude API Call)
4. **ContextBuilder** – Baut den angereicherten System Prompt vor jeder Chat-Antwort
5. **PatternAnalyzer** – Erkennt Trends ueber Zeit aus pattern_logs
6. **PatternDiscoveryService** – Entdeckt neue Muster und schlaegt sie dem User vor

---

## Datenmodell

### Graphiti Entity Types

| Entity Type | Beispiele | Zweck |
|-------------|-----------|-------|
| Person | "Schwester Lisa", "Chef Marcus" | Soziales Netzwerk |
| Place | "Buero", "Fitnessstudio" | Orte und Kontexte |
| Habit | "Morgens joggen", "Kaffee um 9" | Routinen |
| Preference | "Hasst Montags-Meetings" | Vorlieben/Abneigungen |
| Trigger | "Stress bei Deadlines" | Ausloesende Faktoren |
| CopingStrategy | "Timer stellen", "Body Doubling" | Bewaeltigungsstrategien |

### ADHS Behavioral Pattern Entities (13 Seed-Patterns)

| Pattern | Beschreibung |
|---------|-------------|
| Procrastination | Aufschieben trotz Dringlichkeit |
| Hyperfocus | Uebermaessige Vertiefung in eine Aufgabe |
| Task-Switching | Haeufiger Wechsel zwischen Aufgaben ohne Abschluss |
| Paralysis by Analysis | Entscheidungsunfaehigkeit durch Ueberanalyse |
| Time Blindness | Fehleinschaetzung von Zeitdauern |
| Emotional Dysregulation | Uebermaessige emotionale Reaktionen |
| Rejection Sensitivity | Ueberempfindlichkeit gegenueber Kritik/Ablehnung |
| Dopamine Seeking | Impulsives Suchen nach Stimulation |
| Working Memory Overload | Vergessen von gerade Besprochenem |
| Sleep Disruption | Einschlafprobleme, Revenge Bedtime Procrastination |
| Transition Difficulty | Schwierigkeiten beim Aktivitaetswechsel |
| Perfectionism Paralysis | Nichts anfangen weil es perfekt sein muss |
| Social Masking | Erschoepfung durch Anpassung an neurotypische Erwartungen |

### Graphiti Relations (temporal)

```
[User] --EXHIBITS--> [Procrastination]          (frequency, severity)
[Procrastination] --TRIGGERED_BY--> [Deadline-Stress]   (observed: 8/12)
[Procrastination] --MITIGATED_BY--> [Pomodoro Timer]    (success_rate: 0.8)
[Procrastination] --OFTEN_BEFORE--> [Emotional Dysregulation]  (correlation)
[Hyperfocus] --TRIGGERED_BY--> [Neues Projekt]
[Hyperfocus] --LEADS_TO--> [Vergessene Mahlzeit]
[Task-Switching] --OCCURS_DURING--> [Morgens: 9-11 Uhr]
```

### PostgreSQL Erweiterung

**Neue Tabelle: pattern_logs**

```sql
CREATE TABLE pattern_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    episode_id VARCHAR(255),
    mood_score FLOAT,
    energy_level FLOAT,
    focus_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pattern_logs_user_date ON pattern_logs(user_id, created_at DESC);
```

---

## Pattern Discovery (3-Stufen-Modell)

### Stufe 1: Vordefinierte Patterns
Die 13 Seed-Patterns werden beim Setup als Entities in den Graph geladen. Graphiti matched Gespraechsinhalte automatisch gegen diese.

### Stufe 2: Automatische Entdeckung
Graphiti extrahiert frei neue Entities aus Gespraechen. Wenn der User 3x von "Chaos in der Kueche nach Hyperfokus" erzaehlt, erstellt Graphiti eine neue Entity mit Relation.

### Stufe 3: User-Vorschlaege
PatternDiscoveryService prueft periodisch: Gibt es Entities die 3+ Mal mit dem User verknuepft sind und kein bekanntes Pattern sind? Falls ja, schlaegt ALICE dem User vor, es als Muster zu tracken.

---

## Infrastruktur

### FalkorDB (ersetzt Redis)

```yaml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
    command: >
      --loadmodule /usr/lib/redis/modules/falkordb.so
```

FalkorDB ist vollstaendig Redis-kompatibel. Bestehende Redis-Nutzungen (Cache, Celery Broker) funktionieren weiterhin. Kein zusaetzlicher Container.

### Python Dependencies

```
graphiti-core[falkordb,anthropic]
```

---

## Chat-Integration

### Timing: Hybrid-Ansatz

- **Vor dem Chat (sync, ~300ms):** ContextBuilder holt relevantes Wissen aus Graph + Trends aus pattern_logs
- **Nach dem Chat (async, ~2-5s):** Gesamtes Gespraech wird als Episode verarbeitet (Graphiti + NLP-Analyse)

### System Prompt Aufbau (erweitert)

```
[1. Personality] (bestehend)
Du bist ALICE, ein empathischer ADHS-Coach...

[2. Memory Context] (NEU)
## Was du ueber den User weisst:
- Arbeitet als Designer bei Agentur XY (seit Juni 2025)
- Hat Schwester Lisa (enge Beziehung)
- Deadline: Freitag fuer Kundenprojekt
- Bevorzugt Pomodoro-Technik bei Fokus-Problemen

## Aktuelle Verhaltenstrends:
- Focus-Score letzte 3 Tage: 0.35 (niedrig)
- 2x Prokrastination diese Woche (Trigger: Deadline)
- Stimmung: leicht gedrueckt seit Montag

## Handlungsempfehlung:
- Fokus-Probleme empathisch ansprechen
- Pomodoro vorschlagen (hat 4/5 Mal geholfen)

[3. Zeitbewusstsein] (bestehend)
```

Max ~500 Tokens fuer Memory-Block. Nur kontextuell relevante Fakten via Graphiti Hybrid Search.

### Wissen-Nutzung

- **Leise (System Prompt):** Fakten fliessen unsichtbar ein – ALICE weiss es, sagt es nicht explizit
- **Laut (Proaktiv):** Verhaltensmuster werden explizit angesprochen wenn relevant

---

## NLP-Analyse Pipeline

Ein einziger Claude API Call pro Gespraech:

```
Prompt: "Analysiere dieses Gespraech. Extrahiere:
  1. mood_score (-1 bis 1)
  2. energy_level (0 bis 1)
  3. focus_score (0 bis 1)
  4. detected_patterns[]
  5. pattern_triggers[]
  6. notable_facts[]
  Respond as JSON."
```

Kosten: ~0.01-0.03 USD pro Gespraech.

### Proaktive Muster-Hinweise

| Erkennung | ALICE sagt |
|-----------|-----------|
| focus_score < 0.3 fuer 3 Tage | "Dein Fokus war die letzten Tage niedrig. Sollen wir schauen was los ist?" |
| Prokrastination 4x in 7 Tagen | "Du schiebst diese Woche oefter Dinge auf. Pomodoro hat dir dabei geholfen - wollen wir das probieren?" |
| energy_level sinkt nach 15 Uhr | "Deine Energie faellt nachmittags immer ab. Wichtige Tasks lieber vormittags?" |
| Neues Muster 3x beobachtet | "Mir faellt auf dass [X]. Soll ich das als Muster im Auge behalten?" |

---

## API Endpoints (neu)

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | `/api/v1/memory/status` | Memory aktiv? Letzte Analyse? |
| GET | `/api/v1/memory/export` | Alle Fakten + Patterns (DSGVO Art. 15) |
| DELETE | `/api/v1/memory` | Kompletter Memory-Reset (DSGVO Art. 17) |
| PUT | `/api/v1/settings/memory` | Memory ein/ausschalten |

---

## Error Handling

| Szenario | Verhalten |
|----------|-----------|
| FalkorDB nicht erreichbar | Chat funktioniert ohne Memory-Enrichment (graceful degradation) |
| Graphiti add_episode fehlgeschlagen | Retry 2x mit Backoff, dann Dead-Letter-Queue in PostgreSQL |
| Leerer Knowledge Graph (neue User) | Leerer Memory-Block, ALICE verhaelt sich wie bisher |
| Widersprüchliche Fakten | Graphiti invalidiert alte Relation (valid_until), erstellt neue |
| User schaltet Memory aus | Keine neuen Episodes, kein Enrichment, Graph bleibt fuer Re-Aktivierung |
| User loescht Memory (DSGVO) | Graph komplett geloescht + pattern_logs DELETE, irreversibel |
| Analyse-LLM-Call fehlgeschlagen | Episode geht trotzdem an Graphiti, nur Scores fehlen |

---

## Testing

| Test-Typ | Was | Wie | Geschaetzt |
|-----------|-----|-----|-----------|
| Unit | MemoryService, NLPAnalyzer, ContextBuilder, PatternAnalyzer | pytest, Mocked Graphiti | ~15 Tests |
| Integration | Graphiti add_episode + search Roundtrip | FalkorDB Testcontainer | ~8 Tests |
| API | Memory-Endpoints (status, export, delete, settings) | TestClient | ~8 Tests |
| E2E | Chat -> Episode -> Graph -> Enriched Chat | Full-Stack | ~5 Tests |
| **Gesamt** | | | **~36 Tests** |

---

## Quellen

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [FalkorDB + Graphiti Integration](https://www.falkordb.com/blog/graphiti-falkordb-multi-agent-performance/)
- [Graphiti FalkorDB Docs](https://docs.falkordb.com/agentic-memory/graphiti.html)
- [Zep Paper: Temporal Knowledge Graphs](https://arxiv.org/abs/2501.13956)
- [graphiti-core PyPI](https://pypi.org/project/graphiti-core/)
