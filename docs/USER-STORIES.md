# ALICE -- User Stories

Alle User Stories im INVEST-Format mit Akzeptanzkriterien.
Organisiert nach Milestone und Epic.

---

## Milestone 1: Foundation

---

### Epic: Infrastructure Setup

#### STORY-INFRA-01: Docker Compose Entwicklungsumgebung

**Als** Entwickler
**moechte ich** ein Docker Compose Setup mit FastAPI, PostgreSQL und Redis,
**damit** ich lokal entwickeln kann ohne manuelle Service-Installation.

**Akzeptanzkriterien:**
- [ ] `docker compose up` startet alle Services (api, db, redis)
- [ ] FastAPI erreichbar unter localhost:8000
- [ ] PostgreSQL erreichbar unter localhost:5432
- [ ] Redis erreichbar unter localhost:6379
- [ ] Hot-Reload funktioniert fuer FastAPI Code-Aenderungen
- [ ] .env.example mit allen noetigten Variablen vorhanden
- [ ] Health-Check Endpoint /health antwortet mit 200

**Tasks:**
- [agent:devops-engineer] Docker Compose Datei erstellen (api, db, redis) -- S
- [agent:backend-dev] FastAPI Projekt-Skeleton erstellen (main.py, config, routers) -- M
- [agent:backend-dev] Health-Check Endpoint implementieren -- S
- [agent:devops-engineer] .env.example und Environment-Handling -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-INFRA-02: Datenbank-Grundstruktur

**Als** Entwickler
**moechte ich** eine PostgreSQL Datenbank mit SQLAlchemy und Alembic,
**damit** das Schema versioniert und migrierbar ist.

**Akzeptanzkriterien:**
- [ ] SQLAlchemy 2.0 Base-Model konfiguriert
- [ ] Alembic initialisiert mit auto-generate Support
- [ ] Erste Migration (initial) erstellt und ausfuehrbar
- [ ] `alembic upgrade head` und `alembic downgrade` funktionieren
- [ ] pgvector Extension aktiviert
- [ ] Datenbank-Verbindung ueber Connection Pool

**Tasks:**
- [agent:database-mgr] SQLAlchemy Base-Model + Session-Setup -- S
- [agent:database-mgr] Alembic Konfiguration + erste Migration -- S
- [agent:database-mgr] pgvector Extension aktivieren -- S

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Authentication

#### STORY-AUTH-01: Benutzer-Registrierung

**Als** neuer Nutzer
**moechte ich** mich mit E-Mail und Passwort registrieren,
**damit** ich ALICE nutzen kann.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/auth/register nimmt email, password, display_name entgegen
- [ ] E-Mail-Validierung (Format + Uniqueness)
- [ ] Passwort-Anforderungen: min 8 Zeichen, 1 Grossbuchstabe, 1 Zahl
- [ ] Passwort wird mit bcrypt gehasht gespeichert
- [ ] Erfolg: 201 mit User-Objekt (ohne Passwort)
- [ ] Fehler: 409 bei existierender E-Mail, 422 bei Validierungsfehlern
- [ ] Rate Limiting: max 5 Versuche pro Minute pro IP

**Tasks:**
- [agent:database-mgr] User-Tabelle erstellen (id, email, password_hash, display_name, created_at, updated_at) -- S
- [agent:architect] API-Design fuer Auth Endpoints spezifizieren -- S
- [agent:backend-dev] Register Endpoint implementieren -- M
- [agent:frontend-dev] Register Screen implementieren (React Native) -- M
- [agent:test-engineer] Unit + Integration Tests fuer Register -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-AUTH-02: Benutzer-Login

**Als** registrierter Nutzer
**moechte ich** mich mit E-Mail und Passwort einloggen,
**damit** ich Zugriff auf meine Daten erhalte.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/auth/login nimmt email und password entgegen
- [ ] Erfolg: 200 mit access_token (15min TTL) und refresh_token (7d TTL)
- [ ] Fehler: 401 bei falschen Credentials
- [ ] Rate Limiting: max 5 Versuche pro Minute pro IP
- [ ] Failed Login Attempts werden geloggt (ohne Passwort)

**Tasks:**
- [agent:backend-dev] Login Endpoint mit JWT-Generierung implementieren -- M
- [agent:backend-dev] JWT Middleware fuer Protected Routes -- M
- [agent:frontend-dev] Login Screen implementieren (React Native) -- M
- [agent:frontend-dev] Token Storage (SecureStore) + Auto-Refresh -- M
- [agent:test-engineer] Unit + Integration Tests fuer Login -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-AUTH-03: Token Refresh

**Als** eingeloggter Nutzer
**moechte ich** dass mein Token automatisch erneuert wird,
**damit** ich nicht staendig neu einloggen muss.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/auth/refresh nimmt refresh_token entgegen
- [ ] Erfolg: 200 mit neuem access_token und neuem refresh_token
- [ ] Fehler: 401 bei abgelaufenem oder invalidem refresh_token
- [ ] Alter Refresh Token wird nach Nutzung invalidiert (Rotation)

**Tasks:**
- [agent:backend-dev] Refresh Endpoint + Token Rotation implementieren -- S
- [agent:frontend-dev] Auto-Refresh Interceptor in API Client -- S
- [agent:test-engineer] Tests fuer Token Refresh Flow -- S

**Prioritaet:** Must
**Groesse:** S

---

#### STORY-AUTH-04: Logout

**Als** eingeloggter Nutzer
**moechte ich** mich ausloggen koennen,
**damit** meine Session sicher beendet wird.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/auth/logout invalidiert den Refresh Token
- [ ] Access Token wird in Blacklist aufgenommen (Redis, TTL = Restlaufzeit)
- [ ] Erfolg: 204 No Content

**Tasks:**
- [agent:backend-dev] Logout Endpoint + Token Blacklist (Redis) -- S
- [agent:frontend-dev] Logout Button + Token-Cleanup -- S
- [agent:test-engineer] Tests fuer Logout -- S

**Prioritaet:** Must
**Groesse:** S

---

#### STORY-AUTH-05: Profil abrufen

**Als** eingeloggter Nutzer
**moechte ich** mein Profil abrufen koennen,
**damit** ich meine Daten sehen kann.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/auth/me liefert User-Profil (id, email, display_name, created_at)
- [ ] Nur mit gueltigem Access Token erreichbar
- [ ] Fehler: 401 ohne Token

**Tasks:**
- [agent:backend-dev] Me Endpoint implementieren -- S
- [agent:test-engineer] Tests fuer Me Endpoint -- S

**Prioritaet:** Must
**Groesse:** S

---

### Epic: Chat

#### STORY-CHAT-01: Nachricht an ALICE senden

**Als** Nutzer
**moechte ich** eine Textnachricht an ALICE senden und eine Streaming-Antwort erhalten,
**damit** ich natuerlich mit ALICE kommunizieren kann.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/chat/message nimmt message und optional conversation_id entgegen
- [ ] Antwort wird als Server-Sent Events (SSE) gestreamt
- [ ] First-Token Latenz < 2 Sekunden
- [ ] Nachricht und Antwort werden in conversations/messages Tabelle persistiert
- [ ] Neue Konversation wird erstellt wenn keine conversation_id angegeben
- [ ] Claude API wird als LLM verwendet
- [ ] System Prompt enthaelt ALICE Basis-Persoenlichkeit

**Tasks:**
- [agent:database-mgr] Conversations + Messages Tabellen erstellen -- S
- [agent:architect] Chat-API Design + System Prompt Spezifikation -- M
- [agent:backend-dev] Chat Endpoint mit Claude API Streaming (SSE) -- L
- [agent:backend-dev] Conversation Persistence Service -- M
- [agent:frontend-dev] Chat Screen mit Streaming-Anzeige -- L
- [agent:test-engineer] Tests fuer Chat Endpoint -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-CHAT-02: Konversationshistorie

**Als** Nutzer
**moechte ich** meine frueheren Konversationen mit ALICE einsehen,
**damit** ich auf vorherige Gespraeche zurueckgreifen kann.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/chat/history liefert paginierte Liste der Konversationen
- [ ] GET /api/v1/chat/history/{conversation_id} liefert alle Nachrichten einer Konversation
- [ ] Pagination mit cursor-based Pagination
- [ ] Konversationen sortiert nach letzter Aktivitaet

**Tasks:**
- [agent:backend-dev] Chat History Endpoints implementieren -- M
- [agent:frontend-dev] Konversationsliste + Navigation in Chat Screen -- M
- [agent:test-engineer] Tests fuer Chat History -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-CHAT-03: WebSocket Echtzeit-Verbindung

**Als** Nutzer
**moechte ich** ueber WebSocket in Echtzeit mit ALICE kommunizieren,
**damit** die Interaktion schnell und fliesend ist.

**Akzeptanzkriterien:**
- [ ] WebSocket Endpoint unter /api/v1/chat/ws
- [ ] Authentifizierung ueber Token im Query-Parameter oder Header
- [ ] Heartbeat/Ping-Pong fuer Connection Health
- [ ] Reconnection-Logik in der App
- [ ] Unterstuetzt gleichzeitig SSE (HTTP) und WebSocket Modus

**Tasks:**
- [agent:backend-dev] WebSocket Endpoint in FastAPI implementieren -- M
- [agent:frontend-dev] WebSocket Client + Reconnection-Logik -- M
- [agent:test-engineer] WebSocket Integration Tests -- M

**Prioritaet:** Must
**Groesse:** M

---

### Epic: React Native App Setup

#### STORY-APP-01: Expo Projekt mit Navigation

**Als** Entwickler
**moechte ich** ein React Native Expo Projekt mit Tab-Navigation,
**damit** die App-Grundstruktur steht.

**Akzeptanzkriterien:**
- [ ] Expo Projekt mit TypeScript (strict)
- [ ] Expo Router mit Tab-Navigation (Chat, Tasks, Brain, Dashboard, Settings)
- [ ] NativeWind / Tailwind konfiguriert
- [ ] Zustand Store Setup
- [ ] TanStack Query Provider konfiguriert
- [ ] API Client mit Base URL Konfiguration und Auth Interceptor
- [ ] Splash Screen konfiguriert

**Tasks:**
- [agent:frontend-dev] Expo Projekt initialisieren + TypeScript Config -- M
- [agent:ux-designer] Tab-Navigation Design + Icon-Auswahl -- S
- [agent:frontend-dev] Expo Router Tab-Navigation implementieren -- M
- [agent:frontend-dev] Zustand + TanStack Query + API Client Setup -- M
- [agent:test-engineer] Jest Setup fuer React Native Tests -- S

**Prioritaet:** Must
**Groesse:** M

---

## Milestone 2: Core Features

---

### Epic: Task Management

#### STORY-TASK-01: Tasks erstellen und verwalten

**Als** Nutzer
**moechte ich** Tasks erstellen, bearbeiten und loeschen,
**damit** ich meine Aufgaben in ALICE verwalten kann.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/tasks -- Task erstellen (title, description, priority, deadline, tags)
- [ ] GET /api/v1/tasks -- Alle Tasks des Nutzers (paginiert, filterbar)
- [ ] GET /api/v1/tasks/{id} -- Einzelnen Task abrufen
- [ ] PUT /api/v1/tasks/{id} -- Task aktualisieren
- [ ] DELETE /api/v1/tasks/{id} -- Task loeschen
- [ ] Prioritaeten: low, medium, high, urgent
- [ ] Status: open, in_progress, done, cancelled
- [ ] Validierung aller Eingaben mit Pydantic

**Tasks:**
- [agent:database-mgr] Tasks-Tabelle erstellen -- S
- [agent:architect] Task API Design + Pydantic Schemas -- S
- [agent:backend-dev] Task CRUD Endpoints implementieren -- M
- [agent:frontend-dev] Task Screen mit Liste + CRUD UI -- L
- [agent:test-engineer] Tests fuer Task CRUD -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-TASK-02: Task erledigen mit XP

**Als** Nutzer
**moechte ich** Tasks als erledigt markieren und dafuer XP erhalten,
**damit** ich motiviert bleibe meine Aufgaben zu erledigen.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/tasks/{id}/complete markiert Task als done
- [ ] XP-Berechnung basierend auf Prioritaet und Rechtzeitigkeit
- [ ] XP werden in user_stats aktualisiert
- [ ] Response enthaelt XP-Vergabe Details (+X XP, neues Level wenn aufgestiegen)
- [ ] Streak wird aktualisiert wenn erster Task des Tages

**Tasks:**
- [agent:database-mgr] user_stats + xp_history Tabellen erstellen -- S
- [agent:backend-dev] Task Complete Endpoint + XP Service -- M
- [agent:frontend-dev] Task-Erledigung Animation + XP-Anzeige -- M
- [agent:test-engineer] Tests fuer Task Complete + XP -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-TASK-03: Heutige Tasks

**Als** Nutzer
**moechte ich** eine Uebersicht meiner heutigen Tasks sehen,
**damit** ich weiss was heute ansteht.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/tasks/today liefert Tasks fuer heute
- [ ] Sortiert nach Prioritaet, dann Deadline
- [ ] Enthaelt ueberfaellige Tasks von gestern
- [ ] Enthaelt Tasks aus Daily Plan (wenn vorhanden)

**Tasks:**
- [agent:backend-dev] Today Endpoint implementieren -- S
- [agent:frontend-dev] Tages-Task-Uebersicht im Dashboard -- M
- [agent:test-engineer] Tests fuer Today Endpoint -- S

**Prioritaet:** Must
**Groesse:** S

---

### Epic: Second Brain

#### STORY-BRAIN-01: Brain-Eintraege verwalten

**Als** Nutzer
**moechte ich** Wissens-Eintraege in meinem Second Brain speichern und verwalten,
**damit** ich mein Wissen zentral organisieren kann.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/brain/entries -- Eintrag erstellen (title, content, tags, source_type)
- [ ] GET /api/v1/brain/entries -- Alle Eintraege (paginiert, filterbar nach Tags)
- [ ] GET /api/v1/brain/entries/{id} -- Einzelnen Eintrag abrufen
- [ ] PUT /api/v1/brain/entries/{id} -- Eintrag aktualisieren
- [ ] DELETE /api/v1/brain/entries/{id} -- Eintrag loeschen
- [ ] Source Types: manual, chat_extract, url_import, file_import, voice_note

**Tasks:**
- [agent:database-mgr] brain_entries + brain_embeddings Tabellen erstellen -- S
- [agent:architect] Brain API Design + Embedding-Pipeline Spezifikation -- M
- [agent:backend-dev] Brain CRUD Endpoints implementieren -- M
- [agent:frontend-dev] Brain Screen mit Eintragsliste + CRUD UI -- L
- [agent:test-engineer] Tests fuer Brain CRUD -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-BRAIN-02: Semantische Suche

**Als** Nutzer
**moechte ich** mein Second Brain semantisch durchsuchen,
**damit** ich relevante Informationen schnell finde -- auch ohne exakte Stichwort-Treffer.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/brain/search?q={query} fuehrt semantische Suche durch
- [ ] Verwendet pgvector fuer Vektor-Aehnlichkeitssuche
- [ ] Embeddings werden bei Erstellung/Update automatisch generiert
- [ ] Ergebnisse nach Relevanz sortiert mit Score
- [ ] Suchzeit < 1 Sekunde
- [ ] Kombiniert Vektor-Suche mit Keyword-Suche (Hybrid)

**Tasks:**
- [agent:backend-dev] Embedding-Pipeline Service (Sentence Transformers) -- M
- [agent:backend-dev] Semantische Suche Endpoint (pgvector) -- M
- [agent:frontend-dev] Suchfeld + Ergebnisanzeige im Brain Screen -- M
- [agent:test-engineer] Tests fuer Embedding + Suche -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-BRAIN-03: Content Ingestion

**Als** Nutzer
**moechte ich** URLs und Dateien in mein Brain importieren,
**damit** ich externes Wissen einfach aufnehmen kann.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/brain/ingest nimmt URL oder Datei entgegen
- [ ] URL: Webseite wird gescraped und als Eintrag gespeichert
- [ ] Datei: PDF und TXT werden extrahiert und als Eintrag gespeichert
- [ ] Automatische Embedding-Generierung
- [ ] Fortschrittsanzeige fuer grosse Dateien
- [ ] Max Dateigroesse: 10MB

**Tasks:**
- [agent:backend-dev] Ingest Endpoint + URL Scraper + File Parser -- L
- [agent:frontend-dev] Import-Dialog in Brain Screen -- M
- [agent:test-engineer] Tests fuer Ingestion -- M

**Prioritaet:** Should
**Groesse:** L

---

### Epic: CrewAI Integration

#### STORY-CREW-01: ALICE Orchestrator Agent

**Als** System
**moechte ich** einen CrewAI-basierten Orchestrator der Sub-Agents koordiniert,
**damit** ALICE komplexe Aufgaben intelligent bearbeiten kann.

**Akzeptanzkriterien:**
- [ ] CrewAI Setup mit ALICE als Orchestrator Agent
- [ ] Sub-Agents: TaskManager, BrainSearcher, Planner, Analyst
- [ ] Orchestrator entscheidet basierend auf Nutzer-Input welche Agents aktiv werden
- [ ] Integration in Chat-Endpoint (Orchestrator ersetzt direkten Claude-Aufruf)
- [ ] Fallback auf direkten Claude-Aufruf bei CrewAI-Fehler

**Tasks:**
- [agent:architect] CrewAI Agent-Architektur spezifizieren -- M
- [agent:backend-dev] CrewAI Setup + ALICE Orchestrator Agent -- L
- [agent:backend-dev] Sub-Agents implementieren (TaskManager, BrainSearcher, Planner, Analyst) -- L
- [agent:backend-dev] Chat-Endpoint auf CrewAI umstellen -- M
- [agent:test-engineer] Tests fuer CrewAI Integration -- M

**Prioritaet:** Must
**Groesse:** XL (aufgeteilt in Tasks)

---

#### STORY-CREW-02: Mentioned Items Extraktion

**Als** Nutzer
**moechte ich** dass ALICE automatisch Aufgaben und Themen aus meinen Chat-Nachrichten erkennt,
**damit** nichts verloren geht was ich erwaehne.

**Akzeptanzkriterien:**
- [ ] ALICE extrahiert Tasks, Termine, Ideen, Follow-Ups aus Chat-Nachrichten
- [ ] Mentioned Items werden in mentioned_items Tabelle gespeichert
- [ ] GET /api/v1/proactive/mentioned-items liefert unbearbeitete Items
- [ ] Items koennen in Tasks oder Brain-Eintraege konvertiert werden
- [ ] Nutzer wird auf offene Mentioned Items hingewiesen

**Tasks:**
- [agent:database-mgr] mentioned_items Tabelle erstellen -- S
- [agent:backend-dev] Mentioned Items Extraction Service (LLM-basiert) -- M
- [agent:backend-dev] Mentioned Items API Endpoints -- S
- [agent:frontend-dev] Mentioned Items Uebersicht + Konvertierung -- M
- [agent:test-engineer] Tests fuer Mentioned Items -- M

**Prioritaet:** Must
**Groesse:** L

---

### Epic: Proaktiver Agent

#### STORY-PROACTIVE-01: Tagesplanung

**Als** Nutzer
**moechte ich** dass ALICE mir jeden Morgen einen Tagesplan erstellt,
**damit** ich strukturiert in den Tag starten kann.

**Akzeptanzkriterien:**
- [ ] APScheduler Job laeuft taeglich zur konfigurierbaren Uhrzeit
- [ ] Tagesplan beruecksichtigt: offene Tasks, Kalender-Events, Mentioned Items
- [ ] Plan wird als Push Notification gesendet
- [ ] GET /api/v1/proactive/daily-plan liefert aktuellen Plan
- [ ] Plan ist im Dashboard sichtbar

**Tasks:**
- [agent:backend-dev] APScheduler Setup + Daily Planning Job -- M
- [agent:backend-dev] Daily Plan Generation Service (LLM-basiert) -- M
- [agent:backend-dev] Push Notification Service (Expo + FCM) -- M
- [agent:frontend-dev] Tagesplan-Anzeige im Dashboard -- M
- [agent:test-engineer] Tests fuer Daily Planning -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-PROACTIVE-02: Proaktive Einstellungen

**Als** Nutzer
**moechte ich** einstellen wann und wie oft ALICE mich proaktiv kontaktiert,
**damit** ich nicht gestoert werde wenn ich es nicht will.

**Akzeptanzkriterien:**
- [ ] GET/PUT /api/v1/proactive/settings -- Einstellungen lesen/schreiben
- [ ] Einstellbar: quiet_hours_start, quiet_hours_end, max_notifications_per_day
- [ ] Einstellbar: daily_plan_time, nudge_intensity (low/medium/high)
- [ ] POST /api/v1/proactive/snooze -- Alle Notifications fuer X Minuten snoozen

**Tasks:**
- [agent:backend-dev] Proactive Settings Endpoints -- S
- [agent:frontend-dev] Proaktive Einstellungen im Settings Screen -- M
- [agent:test-engineer] Tests fuer Proactive Settings -- S

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Push Notifications

#### STORY-NOTIF-01: Push Notification Setup

**Als** Nutzer
**moechte ich** Push Notifications von ALICE erhalten,
**damit** ich auch ausserhalb der App informiert werde.

**Akzeptanzkriterien:**
- [ ] Expo Push Notifications konfiguriert
- [ ] FCM (Firebase Cloud Messaging) als Backend
- [ ] Device Token wird bei Login registriert
- [ ] notification_log Tabelle trackt alle gesendeten Notifications
- [ ] Notifications koennen Deeplinks in die App enthalten

**Tasks:**
- [agent:database-mgr] notification_log Tabelle erstellen -- S
- [agent:backend-dev] Push Notification Service (Expo Push API) -- M
- [agent:frontend-dev] Push Notification Registration + Handling -- M
- [agent:devops-engineer] FCM Setup + Konfiguration -- S
- [agent:test-engineer] Tests fuer Push Notifications -- S

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Personality Engine

#### STORY-PERSONALITY-01: Personality-Profile erstellen

**Als** Nutzer
**moechte ich** ALICEs Persoenlichkeit anpassen koennen,
**damit** die Interaktion meinen Vorlieben entspricht.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/personality/profiles -- Profil erstellen
- [ ] GET /api/v1/personality/profiles -- Alle Profile des Nutzers
- [ ] PUT /api/v1/personality/profiles/{id} -- Profil bearbeiten
- [ ] DELETE /api/v1/personality/profiles/{id} -- Profil loeschen
- [ ] POST /api/v1/personality/profiles/{id}/activate -- Profil aktivieren
- [ ] Nur ein Profil gleichzeitig aktiv

**Tasks:**
- [agent:database-mgr] personality_profiles + personality_templates Tabellen -- S
- [agent:architect] Personality Engine Datenmodell + API Design -- M
- [agent:backend-dev] Personality Profile CRUD + Activation -- M
- [agent:frontend-dev] Personality Profile Screen -- M
- [agent:test-engineer] Tests fuer Personality Profiles -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-PERSONALITY-02: Traits und Rules konfigurieren

**Als** Nutzer
**moechte ich** einzelne Persoenlichkeits-Traits per Slider einstellen und eigene Regeln definieren,
**damit** ALICE genau so kommuniziert wie ich es mag.

**Akzeptanzkriterien:**
- [ ] GET/PUT /api/v1/personality/traits -- Traits lesen/schreiben
- [ ] Traits: formality (0-100), humor (0-100), strictness (0-100), empathy (0-100), verbosity (0-100)
- [ ] GET/POST/DELETE /api/v1/personality/rules -- Custom Rules verwalten
- [ ] Rules Beispiel: "Sprich mich mit Du an", "Verwende keine Emojis"
- [ ] Traits und Rules fliessen in den System Prompt ein

**Tasks:**
- [agent:backend-dev] Traits + Rules Endpoints implementieren -- M
- [agent:backend-dev] System Prompt Compose Service (Traits + Rules -> Prompt) -- M
- [agent:frontend-dev] Trait Slider UI + Rules Editor -- M
- [agent:test-engineer] Tests fuer Traits + Rules -- S

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-PERSONALITY-03: Vordefinierte Templates

**Als** Nutzer
**moechte ich** aus vordefinierten Personality-Templates waehlen,
**damit** ich schnell eine passende Persoenlichkeit fuer ALICE finde.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/personality/templates -- Alle Templates abrufen
- [ ] Templates: "Strenger Coach", "Freundlicher Begleiter", "Sachlicher Assistent", "Motivierende Cheerleaderin"
- [ ] Template kann als Basis fuer eigenes Profil verwendet werden
- [ ] GET /api/v1/personality/preview -- Live-Preview einer Personality-Konfiguration

**Tasks:**
- [agent:backend-dev] Templates Endpoint + Seed Data -- S
- [agent:backend-dev] Preview Endpoint (generiert Beispiel-Antwort) -- S
- [agent:frontend-dev] Template-Auswahl + Preview UI -- M
- [agent:test-engineer] Tests fuer Templates + Preview -- S

**Prioritaet:** Must
**Groesse:** M

---

## Milestone 3: ADHS-Modus

---

### Epic: Erweiterte Proaktivitaet

#### STORY-PROACTIVE-03: Follow-Up und Deadline Monitor

**Als** Nutzer mit ADHS
**moechte ich** dass ALICE mich aktiv an vergessene Aufgaben und Deadlines erinnert,
**damit** nichts unter den Tisch faellt.

**Akzeptanzkriterien:**
- [ ] Follow-Up Job prueft taeglich unerledigte Mentioned Items
- [ ] Deadline Monitor warnt 24h, 4h und 1h vor Deadline
- [ ] Ueberfallige Tasks werden eskaliert (hoehere Dringlichkeit in Notification)
- [ ] Alle Proaktiv-Jobs respektieren Quiet Hours und Snooze

**Tasks:**
- [agent:backend-dev] Follow-Up Job implementieren -- M
- [agent:backend-dev] Deadline Monitor Job implementieren -- M
- [agent:backend-dev] Quiet Hours + Snooze Logik in Job-Basis -- S
- [agent:test-engineer] Tests fuer Follow-Up + Deadline Monitor -- M

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-PROACTIVE-04: Nudge-Strategien mit Eskalation

**Als** Nutzer mit ADHS
**moechte ich** dass ALICE ihre Erinnerungen eskaliert wenn ich nicht reagiere,
**damit** wirklich wichtige Aufgaben nicht vergessen werden.

**Akzeptanzkriterien:**
- [ ] 3 Eskalationsstufen: freundlich -> bestimmt -> dringlich
- [ ] Eskalation basierend auf: Prioritaet des Tasks + Anzahl ignorierter Reminders
- [ ] Stufe 1: Freundliche Erinnerung mit positivem Framing
- [ ] Stufe 2: Klare Aufforderung mit Konsequenz-Hinweis
- [ ] Stufe 3: Dringliche Nachricht, Option zum Task-Breakdown
- [ ] Nutzer kann Eskalationsintensitaet in Settings einstellen

**Tasks:**
- [agent:backend-dev] Nudge Strategy Engine implementieren -- M
- [agent:backend-dev] Eskalationsstufen-Templates -- S
- [agent:frontend-dev] Nudge-Notification-Darstellung (visuell differenziert) -- M
- [agent:test-engineer] Tests fuer Nudge-Strategien -- M

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Task Breakdown

#### STORY-TASK-04: KI-gestuetzter Task-Breakdown

**Als** Nutzer mit ADHS
**moechte ich** dass ALICE grosse Aufgaben automatisch in kleine Schritte zerlegt,
**damit** ich nicht ueberwaeltigt werde.

**Akzeptanzkriterien:**
- [ ] POST /api/v1/tasks/{id}/breakdown zerlegt einen Task in Sub-Tasks
- [ ] LLM analysiert den Task und erstellt 3-7 konkrete, kleine Schritte
- [ ] Sub-Tasks sind eigenstaendig erledigbar (max 30min geschaetzt)
- [ ] Sub-Tasks erben Deadline und Tags des Eltern-Tasks
- [ ] Nutzer kann generierte Sub-Tasks bearbeiten vor dem Speichern

**Tasks:**
- [agent:backend-dev] Task Breakdown Endpoint + LLM Service -- M
- [agent:frontend-dev] Breakdown UI (Vorschau, Bearbeiten, Bestaetigen) -- M
- [agent:test-engineer] Tests fuer Task Breakdown -- S

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Gamification

#### STORY-GAMIFICATION-01: XP und Level System

**Als** Nutzer
**moechte ich** fuer erledigte Tasks XP erhalten und Level aufsteigen,
**damit** ich durch spielerische Elemente motiviert bleibe.

**Akzeptanzkriterien:**
- [ ] XP-Vergabe: low=10, medium=25, high=50, urgent=100 Basis-XP
- [ ] Bonus: +50% fuer rechtzeitig, +25% fuer Streak-Tag
- [ ] Level berechnet sich aus Gesamt-XP (Level = floor(sqrt(total_xp / 100)))
- [ ] GET /api/v1/gamification/stats liefert XP, Level, Streak, Level-Fortschritt
- [ ] GET /api/v1/gamification/history liefert XP-Verlauf (letzte 30 Tage)
- [ ] Level-Up wird als besonderes Event angezeigt

**Tasks:**
- [agent:backend-dev] XP Calculation Service erweitern -- S
- [agent:backend-dev] Gamification Stats + History Endpoints -- M
- [agent:frontend-dev] XP-Bar + Level-Anzeige + Level-Up Animation -- M
- [agent:test-engineer] Tests fuer Gamification -- M

**Prioritaet:** Must
**Groesse:** M

---

#### STORY-GAMIFICATION-02: Streaks

**Als** Nutzer
**moechte ich** dass meine produktiven Tage als Streak gezaehlt werden,
**damit** ich motiviert bin taeglich mindestens eine Aufgabe zu erledigen.

**Akzeptanzkriterien:**
- [ ] Streak zaehlt aufeinanderfolgende Tage mit mindestens 1 erledigtem Task
- [ ] Streak wird in user_stats gespeichert und taeglich aktualisiert
- [ ] Streak-Break wird dem Nutzer kommuniziert (motivierend, nicht bestrafend)
- [ ] Streak-Milestone Notifications (7 Tage, 30 Tage, 100 Tage)

**Tasks:**
- [agent:backend-dev] Streak Tracking Service implementieren -- S
- [agent:frontend-dev] Streak-Anzeige im Dashboard (Flammen-Symbol) -- S
- [agent:test-engineer] Tests fuer Streak Tracking -- S

**Prioritaet:** Must
**Groesse:** S

---

#### STORY-GAMIFICATION-03: Achievements

**Als** Nutzer
**moechte ich** Achievements fuer besondere Leistungen erhalten,
**damit** ich Langzeitziele habe auf die ich hinarbeiten kann.

**Akzeptanzkriterien:**
- [ ] achievements Tabelle mit vordefinierten Achievements
- [ ] user_achievements Tabelle trackt freigeschaltete Achievements
- [ ] Achievements z.B.: "First Task", "7-Day Streak", "100 Tasks", "Brain Scholar (50 Brain Entries)"
- [ ] Achievement-Benachrichtigung bei Freischaltung
- [ ] Achievement-Uebersicht in der App

**Tasks:**
- [agent:database-mgr] achievements + user_achievements Tabellen -- S
- [agent:backend-dev] Achievement Check Service + Seed Data -- M
- [agent:frontend-dev] Achievement-Uebersicht + Unlock-Animation -- M
- [agent:test-engineer] Tests fuer Achievements -- S

**Prioritaet:** Should
**Groesse:** M

---

### Epic: Dashboard

#### STORY-DASHBOARD-01: ADHS-Dashboard

**Als** Nutzer mit ADHS
**moechte ich** ein uebersichtliches Dashboard mit meiner Tagesuebersicht,
**damit** ich auf einen Blick sehe was heute ansteht und wie ich vorankomme.

**Akzeptanzkriterien:**
- [ ] Tagesplan-Uebersicht (aus Daily Planning)
- [ ] Heutige Tasks mit Quick-Complete
- [ ] XP-Fortschritt + Level + Streak
- [ ] Naechste Deadline
- [ ] Motivierender Tagesspruch von ALICE
- [ ] Pull-to-Refresh

**Tasks:**
- [agent:ux-designer] Dashboard Layout + Widget Design -- M
- [agent:frontend-dev] Dashboard Screen implementieren -- L
- [agent:test-engineer] Tests fuer Dashboard -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-DASHBOARD-02: ADHS-Einstellungen

**Als** Nutzer mit ADHS
**moechte ich** ADHS-spezifische Einstellungen vornehmen,
**damit** ALICE optimal auf meine Beduerfnisse eingestellt ist.

**Akzeptanzkriterien:**
- [ ] ADHS-Modus ein/aus Toggle
- [ ] Nudge-Intensitaet (low/medium/high)
- [ ] Auto Task-Breakdown (ein/aus)
- [ ] Gamification (ein/aus)
- [ ] Focus-Mode Timer Laenge
- [ ] Bevorzugte Erinnerungszeiten

**Tasks:**
- [agent:frontend-dev] ADHS Settings Screen implementieren -- M
- [agent:backend-dev] ADHS Settings Endpoints (Teil von User Preferences) -- S
- [agent:test-engineer] Tests fuer ADHS Settings -- S

**Prioritaet:** Must
**Groesse:** M

---

### Epic: Plugin System

#### STORY-PLUGIN-01: Plugin Base-Klasse und Registry

**Als** Entwickler
**moechte ich** ein erweiterbares Plugin-System,
**damit** neue Features modular hinzugefuegt werden koennen.

**Akzeptanzkriterien:**
- [ ] Plugin Base-Klasse mit definierter API (on_install, on_uninstall, on_message, on_schedule)
- [ ] Plugin Registry zum Registrieren und Auffinden von Plugins
- [ ] Plugin Loader fuer dynamisches Laden von Plugins
- [ ] Plugin-Konfiguration ueber JSON Schema
- [ ] Plugins haben isolierten Daten-Storage (plugin_data Tabelle)

**Tasks:**
- [agent:database-mgr] user_plugins + plugin_data Tabellen -- S
- [agent:architect] Plugin System Architektur spezifizieren -- M
- [agent:backend-dev] Plugin Base-Klasse + Registry + Loader -- L
- [agent:test-engineer] Tests fuer Plugin System -- M

**Prioritaet:** Must
**Groesse:** L

---

#### STORY-PLUGIN-02: Plugin Store

**Als** Nutzer
**moechte ich** Plugins in einem Store installieren und verwalten,
**damit** ich ALICE um Funktionen erweitern kann.

**Akzeptanzkriterien:**
- [ ] GET /api/v1/plugins -- Liste aller verfuegbaren Plugins
- [ ] POST /api/v1/plugins/{id}/install -- Plugin installieren
- [ ] POST /api/v1/plugins/{id}/uninstall -- Plugin deinstallieren
- [ ] GET/PUT /api/v1/plugins/{id}/settings -- Plugin-Einstellungen
- [ ] Plugin Store Screen in der App

**Tasks:**
- [agent:backend-dev] Plugin Store Endpoints -- M
- [agent:frontend-dev] Plugin Store Screen -- M
- [agent:test-engineer] Tests fuer Plugin Store -- S

**Prioritaet:** Should
**Groesse:** M

---

### Epic: Erweiterter Personality Editor

#### STORY-PERSONALITY-04: Voice-Stil und erweiterter Editor

**Als** Nutzer
**moechte ich** ALICEs Voice-Stil konfigurieren und einen erweiterten Personality-Editor nutzen,
**damit** ALICE wirklich zu meiner persoenlichen Assistentin wird.

**Akzeptanzkriterien:**
- [ ] GET/PUT /api/v1/personality/voice -- Voice-Einstellungen (speed, pitch, emotion)
- [ ] Erweiterter Editor mit Kategorien: Kommunikationsstil, Motivationsstil, Grenzen
- [ ] Import/Export von Personality-Profilen (JSON)
- [ ] Community-Profile (spaeter)

**Tasks:**
- [agent:backend-dev] Voice Settings + Extended Personality Endpoints -- M
- [agent:frontend-dev] Erweiterter Personality Editor Screen -- L
- [agent:test-engineer] Tests fuer erweiterten Editor -- S

**Prioritaet:** Should
**Groesse:** M

---

## Milestone 4: Polish & Extras

---

### Epic: Voice Integration

#### STORY-VOICE-01: Spracheingabe und -ausgabe

**Als** Nutzer
**moechte ich** per Sprache mit ALICE kommunizieren,
**damit** ich Hands-Free interagieren kann.

**Akzeptanzkriterien:**
- [ ] Push-to-Talk Button im Chat Screen
- [ ] Speech-to-Text via Deepgram (Streaming)
- [ ] Text-to-Speech via ElevenLabs (konfigurierbare Stimme)
- [ ] Voice-Streaming ueber LiveKit (Self-Hosted)
- [ ] Latenz Speech-to-Response-Audio < 3 Sekunden
- [ ] Fallback auf Text bei Voice-Fehler

**Tasks:**
- [agent:devops-engineer] LiveKit Server Setup (Docker) -- M
- [agent:backend-dev] Voice Pipeline: STT (Deepgram) -> LLM -> TTS (ElevenLabs) -- L
- [agent:backend-dev] LiveKit Integration fuer Voice-Streaming -- L
- [agent:frontend-dev] Voice UI (Push-to-Talk, Audio Playback, Waveform) -- L
- [agent:test-engineer] Voice Integration Tests -- M

**Prioritaet:** Should
**Groesse:** XL (aufgeteilt)

---

#### STORY-VOICE-02: Voice Journal

**Als** Nutzer
**moechte ich** Sprach-Notizen aufnehmen die automatisch ins Brain fliessen,
**damit** ich Gedanken schnell festhalten kann.

**Akzeptanzkriterien:**
- [ ] Aufnahme-Button in Brain Screen
- [ ] Audio wird transkribiert (Deepgram)
- [ ] Transkription wird als Brain-Eintrag gespeichert
- [ ] Automatische Tag-Erkennung aus Inhalt
- [ ] Audio-Original optional speicherbar

**Tasks:**
- [agent:backend-dev] Voice Journal Endpoint (Audio -> Transkription -> Brain) -- M
- [agent:frontend-dev] Voice Recording UI + Transkription-Anzeige -- M
- [agent:test-engineer] Tests fuer Voice Journal -- S

**Prioritaet:** Could
**Groesse:** M

---

### Epic: Plugins (Konkrete)

#### STORY-PLUGIN-CALENDAR: Google Calendar Plugin

**Als** Nutzer
**moechte ich** meinen Google Calendar mit ALICE verbinden,
**damit** Termine in die Tagesplanung einfliessen.

**Akzeptanzkriterien:**
- [ ] OAuth 2.0 Flow fuer Google Calendar API
- [ ] GET /api/v1/calendar/events -- Events abrufen
- [ ] POST /api/v1/calendar/sync -- Manueller Sync ausloesen
- [ ] Automatischer Sync alle 15 Minuten
- [ ] Events werden in calendar_events Tabelle gecacht
- [ ] Events fliessen in Daily Planning ein

**Tasks:**
- [agent:database-mgr] calendar_events Tabelle erstellen -- S
- [agent:backend-dev] Google Calendar OAuth + Sync Plugin -- L
- [agent:backend-dev] Calendar Events API -- S
- [agent:frontend-dev] Calendar-Ansicht + OAuth-Flow UI -- M
- [agent:test-engineer] Tests fuer Calendar Plugin -- M

**Prioritaet:** Should
**Groesse:** L

---

#### STORY-PLUGIN-N8N: n8n Bridge Plugin

**Als** Power-User
**moechte ich** ALICE mit n8n verbinden,
**damit** ich eigene Automations-Workflows erstellen kann.

**Akzeptanzkriterien:**
- [ ] Webhook Endpoint fuer n8n Trigger
- [ ] POST /api/v1/plugins/n8n/webhook -- Eingehende n8n Events
- [ ] ALICE kann n8n Workflows triggern (ausgehend)
- [ ] Konfiguration der n8n Base URL in Plugin Settings

**Tasks:**
- [agent:backend-dev] n8n Bridge Plugin implementieren -- M
- [agent:frontend-dev] n8n Plugin Settings UI -- S
- [agent:test-engineer] Tests fuer n8n Plugin -- S

**Prioritaet:** Could
**Groesse:** M

---

### Epic: Polish

#### STORY-POLISH-01: Dark/Light Mode

**Als** Nutzer
**moechte ich** zwischen Dark und Light Mode wechseln,
**damit** die App angenehm fuer meine Augen ist.

**Akzeptanzkriterien:**
- [ ] System-Praeferenz wird als Default verwendet
- [ ] Manueller Toggle in Settings
- [ ] Alle Screens unterstuetzen beide Modi
- [ ] Smooth Transition zwischen Modi

**Tasks:**
- [agent:ux-designer] Color System fuer Dark + Light Mode -- M
- [agent:frontend-dev] Theme-System + Toggle implementieren -- M
- [agent:test-engineer] Visual Tests fuer beide Modi -- S

**Prioritaet:** Should
**Groesse:** M

---

#### STORY-POLISH-02: Offline-Queue

**Als** Nutzer
**moechte ich** die App auch offline nutzen koennen,
**damit** Aktionen nicht verloren gehen.

**Akzeptanzkriterien:**
- [ ] Offline-Erkennung in der App
- [ ] Nachrichten, Tasks und Brain-Eintraege werden lokal gespeichert
- [ ] Automatische Synchronisation bei Reconnect
- [ ] Visueller Indikator fuer Offline-Status
- [ ] Conflict Resolution bei gleichzeitigen Aenderungen

**Tasks:**
- [agent:frontend-dev] Offline Queue + Local Storage -- L
- [agent:frontend-dev] Sync-Service + Conflict Resolution -- M
- [agent:frontend-dev] Offline-UI-Indikatoren -- S
- [agent:test-engineer] Offline Tests -- M

**Prioritaet:** Should
**Groesse:** L

---

#### STORY-POLISH-03: Performance-Optimierung

**Als** Nutzer
**moechte ich** dass die App schnell und fluessig laeuft,
**damit** die Nutzung angenehm ist.

**Akzeptanzkriterien:**
- [ ] App Start < 3 Sekunden
- [ ] Screen-Transitions < 300ms
- [ ] Liste scrollt mit 60fps
- [ ] Memory Usage unter 150MB
- [ ] Bundle Size optimiert

**Tasks:**
- [agent:frontend-dev] Performance Audit + Optimierung -- L
- [agent:backend-dev] API Response Time Optimierung + Caching -- M
- [agent:test-engineer] Performance Tests + Benchmarks -- M

**Prioritaet:** Should
**Groesse:** L

---

#### STORY-POLISH-04: App Store Vorbereitung

**Als** Product Owner
**moechte ich** die App fuer den App Store vorbereiten,
**damit** sie veroeffentlicht werden kann.

**Akzeptanzkriterien:**
- [ ] App Icons in allen Groessen
- [ ] Splash Screen final
- [ ] App Store Screenshots erstellt
- [ ] App Store Beschreibungstexte geschrieben
- [ ] Privacy Policy erstellt
- [ ] Terms of Service erstellt
- [ ] EAS Build konfiguriert (Expo Application Services)
- [ ] TestFlight / Internal Testing eingerichtet

**Tasks:**
- [agent:ux-designer] App Icons + Splash Screen finalisieren -- M
- [agent:ux-designer] App Store Screenshots + Texte -- M
- [agent:devops-engineer] EAS Build Konfiguration -- M
- [agent:security-auditor] Privacy Policy + ToS erstellen -- L
- [agent:docs-writer] User-Dokumentation finalisieren -- M
- [agent:test-engineer] Finaler Regression Test -- L

**Prioritaet:** Must (fuer Release)
**Groesse:** XL (aufgeteilt)

---

### Epic: Security & Compliance

#### STORY-SEC-01: DSGVO + Security Audit

**Als** Product Owner
**moechte ich** dass die App DSGVO-konform und sicher ist,
**damit** wir rechtskonform launchen koennen.

**Akzeptanzkriterien:**
- [ ] Datenschutzerklaerung vorhanden
- [ ] Daten-Loeschung implementiert (Right to Erasure)
- [ ] Daten-Export implementiert (Right to Portability)
- [ ] Consent-Management implementiert
- [ ] Security Audit ohne Critical/High Findings
- [ ] OWASP Top 10 geprueft
- [ ] Paragraph 203 StGB Konformitaet dokumentiert

**Tasks:**
- [agent:security-auditor] DSGVO-Analyse + Massnahmen definieren -- L
- [agent:backend-dev] Daten-Loeschung Endpoint -- M
- [agent:backend-dev] Daten-Export Endpoint -- M
- [agent:security-auditor] Security Audit durchfuehren -- L
- [agent:security-auditor] Paragraph 203 StGB Analyse -- M
- [agent:docs-writer] Datenschutzerklaerung schreiben -- M

**Prioritaet:** Must
**Groesse:** XL (aufgeteilt)

---

### Epic: Deployment

#### STORY-DEPLOY-01: Production Deployment

**Als** DevOps Engineer
**moechte ich** die App auf Coolify deployen,
**damit** sie oeffentlich erreichbar ist.

**Akzeptanzkriterien:**
- [ ] Dockerfile fuer FastAPI optimiert (Multi-Stage Build)
- [ ] Docker Compose fuer Production (mit Traefik/Nginx)
- [ ] GitHub Actions CI/CD Pipeline
- [ ] Coolify Deployment konfiguriert
- [ ] SSL/TLS konfiguriert
- [ ] Backup-Strategie fuer PostgreSQL
- [ ] Monitoring + Alerting Setup
- [ ] Rollback-Plan dokumentiert

**Tasks:**
- [agent:devops-engineer] Production Dockerfile (Multi-Stage) -- M
- [agent:devops-engineer] Docker Compose Production Setup -- M
- [agent:devops-engineer] GitHub Actions CI/CD Pipeline -- L
- [agent:devops-engineer] Coolify Deployment + SSL -- M
- [agent:devops-engineer] Backup-Strategie + Monitoring -- M
- [agent:docs-writer] Deployment Dokumentation -- M

**Prioritaet:** Must
**Groesse:** XL (aufgeteilt)
