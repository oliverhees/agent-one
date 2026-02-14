# Milestone 6: Multi-Agent & Trust System — Design

## Ziel

LangGraph-basiertes Multi-Agent-System das die bestehende ai.py/chat.py ersetzt. 4 Sub-Agents (Email/SMTP, Calendar, Research/Tavily, Briefing) orchestriert durch einen Supervisor mit 3-Level Progressive Autonomy, Approval Gates, SSE Activity Feed und Reflexion Framework.

## Architektur

```
Mobile App (React Native)
    | REST + SSE
FastAPI Backend
    |
+-----------------------------------------------+
|  LangGraph Supervisor (StateGraph)             |
|                                                |
|  +--------+  +-----------+  +-----------+      |
|  | Email  |  | Calendar  |  | Research  |      |
|  | Agent  |  | Agent     |  | Agent     |      |
|  | (SMTP) |  | (exist.)  |  | (Tavily)  |      |
|  +---+----+  +-----+-----+  +-----+-----+      |
|      +--------+----+--------------+             |
|               |                                 |
|  +------------v--------------+                  |
|  | Trust Gate (interrupt())  |                  |
|  +------------+--------------+                  |
|               |                                 |
|  +------------v--------------+                  |
|  | Reflexion Node            |                  |
|  +---------------------------+                  |
|               |                                 |
|  PostgreSQL Checkpointer (State Persistence)    |
+-----------------------------------------------+
    | SSE
Agent Activity Feed -> Mobile App
```

### Kern-Prinzipien

- LangGraph **ersetzt** ai.py und chat.py komplett
- Bestehende 23 Tools werden als LangChain Tools migriert
- Graphiti, MemoryService, ContextBuilder bleiben erhalten
- Jeder Sub-Agent-Node hat eigenen Timeout (15-30s)
- SSE streamt jeden State-Uebergang live ans Frontend
- Feature-Flag-Migration — kein Big-Bang-Cutover

### Neue Dependencies

- `langgraph` — Orchestrierung
- `langchain-anthropic` — Claude-Anbindung via LangChain
- `langchain-community` — Tavily-Integration
- `tavily-python` — Research API
- `aiosmtplib` + `aioimaplib` — Async SMTP/IMAP

## LangGraph State & Supervisor

### State-Schema

```python
class AgentState(TypedDict):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str

    # Routing
    next_agent: str | None
    agent_plan: list[str]

    # Trust
    trust_level: int                # 1, 2 oder 3
    requires_approval: bool
    pending_action: dict | None

    # Execution
    agent_results: list[dict]
    current_agent: str | None
    error: str | None

    # Context
    memory_context: str | None
    user_preferences: dict
```

### Graph-Flow

```
START -> context_loader -> supervisor
                             |
             +---------------+---------------+--------------+
             |               |               |              |
         email_agent    calendar_agent  research_agent  direct_response
             |               |               |              |
             +-------+-------+--------------+               |
                     |                                      |
               trust_gate ----------------------------------+
                     |                                      |
               execute_action                               |
                     |                                      |
               reflexion ---------------------------------------+
                     |                                      |
               supervisor (loop) -----------------> response_node -> END
```

### Conditional Edges

- `supervisor` -> routet basierend auf `next_agent`
- `trust_gate` -> wenn `requires_approval=True` -> `interrupt()` (wartet auf User)
- `reflexion` -> zurueck zu `supervisor` wenn weitere Agents geplant (loop)
- `supervisor` -> `response_node` wenn `agent_plan` leer

## Sub-Agents

### Email Agent (SMTP/IMAP)

**Faehigkeiten:**
- `email_read` — IMAP: Postfach lesen, filtern, zusammenfassen
- `email_draft` — Entwurf erstellen (wird User gezeigt vor Versand)
- `email_send` — SMTP: Email versenden
- `email_reply` — Auf bestehende Email antworten

**Config pro User (encrypted in DB):**
- smtp_host, smtp_port, smtp_user, smtp_password
- imap_host, imap_port, imap_user, imap_password

**Timeout:** 30s

### Calendar Agent (bestehend erweitert)

Nutzt bestehenden CalendarService:
- `calendar_list_events`, `calendar_create_event`, `calendar_update_event`, `calendar_delete_event`

**Timeout:** 15s

### Research Agent (Tavily)

- `web_search` — Tavily Search API
- `web_extract` — Tavily Extract API (Seiteninhalte)
- `summarize_results` — ADHS-freundliche Zusammenfassung

**Timeout:** 20s

### Briefing Agent (bestehend erweitert)

Nutzt bestehenden BriefingService:
- `generate_briefing`, `get_brain_dump_summary`

**Timeout:** 15s

## Trust System (3 Level)

### Datenbank-Modell

```python
class TrustScore(Base):
    id: UUID
    user_id: UUID (FK -> users)
    agent_type: str          # "email", "calendar", "research", "briefing"
    action_type: str         # "read", "write", "delete", "send"
    trust_level: int         # 1, 2 oder 3
    successful_actions: int
    total_actions: int
    last_escalation_at: datetime | None
    last_violation_at: datetime | None
```

### Level-Definitionen

| Level | Lesen/Analysieren | Schreiben/Senden | Loeschen |
|-------|-------------------|-------------------|----------|
| 1 (Neu) | Approval | Approval | Approval |
| 2 (Vertraut) | Automatisch | Approval | Approval |
| 3 (Autonom) | Automatisch | Automatisch | Automatisch |

### Eskalations-Logik

- **Level 1 -> 2:** Automatisch nach 10 erfolgreichen Approved-Aktionen ohne Ablehnung
- **Level 2 -> 3:** Nur durch explizite User-Freigabe (Opt-in in Settings)
- **Downgrade 3 -> 2:** Automatisch bei User-Ablehnung oder 2 Fehlschlaegen in Folge
- **Downgrade 2 -> 1:** Nur manuell durch User in Settings

## SSE Activity Feed

### Endpoint

```
GET /api/v1/agents/activity/stream
Headers: Authorization: Bearer <token>
```

### Event-Typen

- `agent_started` — Agent beginnt Arbeit
- `agent_thinking` — Agent denkt (Zwischenstand)
- `approval_required` — Approval noetig (mit Details)
- `agent_completed` — Agent fertig (mit Ergebnis)
- `agent_error` — Timeout oder Fehler
- `trust_escalation` — Trust-Level aendert sich

### Approval API

```
POST /api/v1/agents/approve
Body: {"approval_id": "uuid", "approved": true/false, "reason": "..."}
```

- Graph wartet via interrupt() auf Approval
- Timeout: 5 Minuten, danach automatisch abgebrochen
- Bei Reject: Supervisor bekommt Feedback, passt an oder bricht ab

## Reflexion Framework

Nach jeder Sub-Agent-Aktion bewertet ein Reflexion-Node das Ergebnis:

| Signal | Speicherort | Beispiel |
|--------|-------------|---------|
| User approved | TrustScore +1 | "Email senden genehmigt" |
| User rejected | TrustScore reset + Graphiti Fact | "User will keine Auto-Emails an Firma" |
| Action failed | Graphiti Episode | "SMTP Timeout bei provider X" |
| User Feedback | Graphiti Fact | "User bevorzugt kurze Betreffzeilen" |

Integration mit bestehendem Memory:
- Graphiti speichert Reflexions-Fakten als durchsuchbare Knoten
- PatternAnalyzer erkennt Trends
- ContextBuilder laedt relevante Reflexionen in den naechsten Agent-Lauf

## Migration: ai.py/chat.py -> LangGraph

**Phase 1 — Parallel aufbauen:**
- Neues Verzeichnis `backend/app/agents/` fuer LangGraph-Code
- Neuer Endpoint `POST /api/v1/agents/chat` neben bestehendem Chat
- Bestehende 23 Tools als LangChain Tools migriert

**Phase 2 — Umschalten:**
- Feature-Flag `use_langgraph` in User-Settings (default: False)
- ChatService routet basierend auf Flag

**Phase 3 — Aufraemen:**
- Alte ai.py und Tool-Loop entfernen
- chat.py wird duenn: nur noch Session-Management

## Error Handling & Timeouts

```python
async def safe_agent_node(node_fn, state, timeout_s, agent_name):
    try:
        result = await asyncio.wait_for(node_fn(state), timeout=timeout_s)
        return result
    except asyncio.TimeoutError:
        return {**state, "error": f"{agent_name} Timeout nach {timeout_s}s"}
    except Exception as e:
        return {**state, "error": f"{agent_name} Fehler: {str(e)}"}
```

- Timeout/Crash -> Supervisor bekommt Error-State
- Supervisor: Retry (1x), Skip, oder User informieren
- SSE sendet agent_error Event
- Graph laeuft IMMER weiter

## Neue DB-Tabellen

| Tabelle | Zweck |
|---------|-------|
| `trust_scores` | Trust-Level pro User/Agent/Action |
| `agent_activities` | Log aller Agent-Aktionen |
| `approval_requests` | Offene Approval-Anfragen mit Timeout |
| `email_configs` | SMTP/IMAP-Konfiguration pro User (encrypted) |
| `reflexion_logs` | Agent-Reflexionen und Lessons Learned |
