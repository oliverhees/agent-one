# ALICE -- Requirements

## Funktionale Anforderungen

### FR-AUTH: Authentifizierung

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-AUTH-01 | Nutzer kann sich mit E-Mail und Passwort registrieren | Must |
| FR-AUTH-02 | Nutzer kann sich einloggen und erhaelt JWT Token-Paar (access + refresh) | Must |
| FR-AUTH-03 | Access Token wird automatisch per Refresh Token erneuert | Must |
| FR-AUTH-04 | Nutzer kann sich ausloggen (Token-Invalidierung) | Must |
| FR-AUTH-05 | Nutzer kann sein Profil abrufen und bearbeiten | Must |
| FR-AUTH-06 | Passwort wird mit bcrypt gehasht gespeichert | Must |
| FR-AUTH-07 | Rate Limiting auf Auth-Endpoints (max 5 Versuche/Minute) | Must |

### FR-CHAT: Chat / Konversation

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-CHAT-01 | Nutzer kann eine Nachricht an ALICE senden und erhaelt Streaming-Antwort | Must |
| FR-CHAT-02 | Konversationshistorie wird persistiert und ist abrufbar | Must |
| FR-CHAT-03 | WebSocket-Verbindung fuer Echtzeit-Kommunikation | Must |
| FR-CHAT-04 | ALICE behaelt Kontext ueber mehrere Nachrichten | Must |
| FR-CHAT-05 | System-Prompt ist konfigurierbar ueber Personality Engine | Should |
| FR-CHAT-06 | Mentioned Items werden automatisch aus Chat extrahiert | Must |
| FR-CHAT-07 | Chat unterstuetzt Markdown-Rendering in der App | Should |

### FR-TASK: Task-Management

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-TASK-01 | Nutzer kann Tasks erstellen, lesen, aktualisieren und loeschen | Must |
| FR-TASK-02 | Tasks haben: Titel, Beschreibung, Prioritaet, Deadline, Status, Tags | Must |
| FR-TASK-03 | Nutzer kann Tasks als erledigt markieren (loest XP-Vergabe aus) | Must |
| FR-TASK-04 | ALICE kann grosse Tasks automatisch in Sub-Tasks zerlegen (Breakdown) | Must |
| FR-TASK-05 | Endpoint liefert heutige Tasks sortiert nach Prioritaet | Must |
| FR-TASK-06 | Tasks koennen aus Chat-Konversationen automatisch erstellt werden | Must |
| FR-TASK-07 | Tasks haben wiederkehrende Optionen (daily, weekly, monthly) | Could |

### FR-BRAIN: Second Brain

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-BRAIN-01 | Nutzer kann Brain-Eintraege erstellen, lesen, aktualisieren und loeschen | Must |
| FR-BRAIN-02 | Eintraege werden automatisch embedded (Vektor-Embeddings via pgvector) | Must |
| FR-BRAIN-03 | Semantische Suche ueber alle Brain-Eintraege (RAG) | Must |
| FR-BRAIN-04 | ALICE nutzt Brain-Eintraege als Kontext fuer Antworten | Must |
| FR-BRAIN-05 | Content Ingestion: URLs koennen als Brain-Eintraege importiert werden | Should |
| FR-BRAIN-06 | Content Ingestion: Dateien (PDF, TXT) koennen importiert werden | Should |
| FR-BRAIN-07 | Brain-Eintraege haben Tags und Kategorien | Should |
| FR-BRAIN-08 | Automatische Verknuepfung verwandter Eintraege | Could |

### FR-PROACTIVE: Proaktiver Agent

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-PROACTIVE-01 | ALICE erstellt taeglich einen Tagesplan basierend auf Tasks und Kalender | Must |
| FR-PROACTIVE-02 | ALICE erinnert an faellige und ueberfallige Tasks | Must |
| FR-PROACTIVE-03 | ALICE monitort Deadlines und warnt rechtzeitig | Must |
| FR-PROACTIVE-04 | Follow-Up auf Mentioned Items die nicht erledigt wurden | Must |
| FR-PROACTIVE-05 | Nudge-Strategien mit Eskalationsstufen (freundlich -> dringlich -> direkt) | Must |
| FR-PROACTIVE-06 | Nutzer kann Notifications snoozen | Must |
| FR-PROACTIVE-07 | Proaktive Einstellungen sind konfigurierbar (Uhrzeiten, Haeufigkeit) | Must |
| FR-PROACTIVE-08 | ALICE lernt aus Nutzerverhalten optimale Erinnerungszeiten | Could |

### FR-GAMIFICATION: Gamification

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-GAMIFICATION-01 | Nutzer erhaelt XP fuer erledigte Tasks | Must |
| FR-GAMIFICATION-02 | Level-System basierend auf XP | Must |
| FR-GAMIFICATION-03 | Streak-Tracking (aufeinanderfolgende produktive Tage) | Must |
| FR-GAMIFICATION-04 | Achievement-System mit definierten Meilensteinen | Should |
| FR-GAMIFICATION-05 | Statistik-Dashboard mit XP-Verlauf und Produktivitaet | Must |
| FR-GAMIFICATION-06 | XP-Verlauf ist einsehbar (Historie) | Should |

### FR-PERSONALITY: Personality Engine

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-PERSONALITY-01 | Nutzer kann Personality-Profile erstellen und aktivieren | Must |
| FR-PERSONALITY-02 | Traits sind ueber Slider einstellbar (z.B. Formalitaet, Humor, Strenge) | Must |
| FR-PERSONALITY-03 | Custom Rules koennen definiert werden (z.B. "Sprich mich mit Du an") | Must |
| FR-PERSONALITY-04 | Voice-Stil ist konfigurierbar (beeinflusst TTS-Parameter) | Should |
| FR-PERSONALITY-05 | Vordefinierte Templates stehen zur Verfuegung (Coach, Freund, Assistent) | Must |
| FR-PERSONALITY-06 | Live-Preview der Personality-Aenderungen | Should |

### FR-PLUGIN: Plugin-System

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-PLUGIN-01 | Plugin Base-Klasse mit definierter API | Must |
| FR-PLUGIN-02 | Plugin Registry + dynamischer Loader | Must |
| FR-PLUGIN-03 | Plugin Store UI zum Installieren/Deinstallieren | Must |
| FR-PLUGIN-04 | Plugins haben eigene Einstellungen | Must |
| FR-PLUGIN-05 | OAuth-Flow fuer Plugin-Authentifizierung (z.B. Google) | Should |
| FR-PLUGIN-06 | Webhook-Support fuer Plugin-Kommunikation | Should |

### FR-VOICE: Voice-Integration

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-VOICE-01 | Nutzer kann per Sprache mit ALICE kommunizieren (Push-to-Talk) | Should |
| FR-VOICE-02 | Speech-to-Text via Deepgram (Streaming) | Should |
| FR-VOICE-03 | Text-to-Speech via ElevenLabs (konfigurierbare Stimme) | Should |
| FR-VOICE-04 | Voice-Streaming ueber LiveKit (Self-Hosted) | Should |
| FR-VOICE-05 | Voice Journal: Sprach-Notizen die ins Brain fliessen | Could |

### FR-CALENDAR: Kalender-Integration

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-CALENDAR-01 | Google Calendar Events abrufen und anzeigen | Should |
| FR-CALENDAR-02 | Bidirektionale Sync (Events erstellen aus ALICE) | Could |
| FR-CALENDAR-03 | Kalender-Events fliessen in Tagesplanung ein | Should |

### FR-UI: User Interface

| ID | Anforderung | Prioritaet |
|---|---|---|
| FR-UI-01 | Tab-Navigation: Chat, Tasks, Brain, Dashboard, Settings | Must |
| FR-UI-02 | Login/Register Screens | Must |
| FR-UI-03 | Chat Screen mit Streaming-Anzeige und Markdown | Must |
| FR-UI-04 | Task Screen mit Filtern und Sortierung | Must |
| FR-UI-05 | Brain Screen mit semantischer Suche | Must |
| FR-UI-06 | Dashboard mit Tagesuebersicht, XP, Streak | Must |
| FR-UI-07 | Settings Screen (Profil, Personality, ADHS, Notifications, Plugins) | Must |
| FR-UI-08 | Dark Mode und Light Mode | Should |
| FR-UI-09 | ADHS-Einstellungen Screen | Must |
| FR-UI-10 | Plugin Store Screen | Should |

---

## Nicht-funktionale Anforderungen

### NFR-PERF: Performance

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-PERF-01 | Chat First-Token Latenz < 2 Sekunden | Must |
| NFR-PERF-02 | App Cold Start < 3 Sekunden | Must |
| NFR-PERF-03 | API Response Time (non-AI) < 200ms (p95) | Must |
| NFR-PERF-04 | Brain-Suche < 1 Sekunde | Must |
| NFR-PERF-05 | Voice Round-Trip Latenz < 3 Sekunden | Should |

### NFR-SEC: Sicherheit

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-SEC-01 | DSGVO-konform (Datensparsamkeit, Loeschrecht, Auskunftsrecht) | Must |
| NFR-SEC-02 | Alle Daten verschluesselt in Transit (TLS 1.3) | Must |
| NFR-SEC-03 | Sensible Daten verschluesselt at Rest | Must |
| NFR-SEC-04 | JWT mit kurzer Laufzeit (15min Access, 7d Refresh) | Must |
| NFR-SEC-05 | Input-Validierung auf allen Endpoints (Pydantic) | Must |
| NFR-SEC-06 | Rate Limiting auf allen oeffentlichen Endpoints | Must |
| NFR-SEC-07 | CORS korrekt konfiguriert | Must |
| NFR-SEC-08 | Kein Logging von sensiblen Daten (Passwoerter, Tokens) | Must |
| NFR-SEC-09 | Paragraph 203 StGB Konformitaet (Vertraulichkeit) | Must |

### NFR-SCALE: Skalierbarkeit

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-SCALE-01 | Bis 10.000 User ohne Architektur-Aenderung | Must |
| NFR-SCALE-02 | Horizontale Skalierung der API-Worker moeglich | Should |
| NFR-SCALE-03 | Background Jobs entkoppelt ueber Celery Queue | Must |

### NFR-AVAIL: Verfuegbarkeit

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-AVAIL-01 | 99.5% Uptime | Must |
| NFR-AVAIL-02 | Health Check Endpoint (/health) | Must |
| NFR-AVAIL-03 | Graceful Degradation bei LLM-Ausfall | Should |
| NFR-AVAIL-04 | Offline-Queue fuer App (Nachrichten werden gequeued) | Should |

### NFR-MAINT: Wartbarkeit

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-MAINT-01 | Alembic Migrationen fuer alle DB-Aenderungen | Must |
| NFR-MAINT-02 | Strukturierte Logs (JSON) | Must |
| NFR-MAINT-03 | OpenAPI/Swagger Dokumentation automatisch generiert | Must |
| NFR-MAINT-04 | Test Coverage >= 80% | Must |
| NFR-MAINT-05 | Typisierter Code (Python Type Hints, TypeScript strict) | Must |

### NFR-UX: Benutzererfahrung

| ID | Anforderung | Prioritaet |
|---|---|---|
| NFR-UX-01 | ADHS-gerechte UI: wenig visuelle Ablenkung, klare Hierarchie | Must |
| NFR-UX-02 | Kurze Interaktionen (max 2-3 Taps fuer Hauptaktionen) | Must |
| NFR-UX-03 | Positive Verstaerkung bei Task-Erledigung (Animation, Sound) | Should |
| NFR-UX-04 | Haptic Feedback bei wichtigen Aktionen | Could |
| NFR-UX-05 | WCAG 2.1 AA soweit auf Mobile anwendbar | Should |
