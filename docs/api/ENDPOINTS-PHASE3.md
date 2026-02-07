# API Endpoints -- Phase 3: ADHS-Modus

**Version:** 3.0 (Ergaenzung zu ENDPOINTS.md)
**Datum:** 2026-02-06
**Base URL:** `https://api.alice-app.de/api/v1`

> Dieses Dokument spezifiziert die neuen Endpoints fuer **Phase 3 (ADHS-Modus)**. Es ergaenzt die bestehende ENDPOINTS.md (Phase 1+2). Nach Fertigstellung werden beide Dokumente zusammengefuehrt.

---

## Inhaltsverzeichnis (Phase 3)

1. [Gamification Endpoints](#gamification-endpoints)
2. [Task Breakdown Endpoints](#task-breakdown-endpoints)
3. [Nudge Endpoints](#nudge-endpoints)
4. [Dashboard Endpoint](#dashboard-endpoint)
5. [ADHS Settings Endpoints](#adhs-settings-endpoints)
   - [GET /api/v1/settings/adhs](#get-apiv1settingsadhs)
   - [PUT /api/v1/settings/adhs](#put-apiv1settingsadhs)
   - [POST /api/v1/settings/push-token](#post-apiv1settingspush-token)
6. [Neue Fehlercodes (Phase 3)](#neue-fehlercodes-phase-3)
7. [Zusammenfassung Phase 3](#zusammenfassung-phase-3)

---

## Gamification Endpoints

Alle Gamification-Endpoints sind unter `/api/v1/gamification/` gruppiert. Alle erfordern Authentifizierung. Der Gamification-Bereich liefert XP-, Level-, Streak- und Achievement-Daten fuer das Dopamin-Belohnungssystem.

### `GET /api/v1/gamification/stats`

Gibt die aktuellen Gamification-Statistiken des Nutzers zurueck: XP, Level, Streak und Fortschritt zum naechsten Level.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "total_xp": 1250,
  "level": 5,
  "current_streak": 7,
  "longest_streak": 14,
  "xp_for_next_level": 1500,
  "progress_percent": 83.3,
  "tasks_completed": 42
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `total_xp` | `int` | Gesamt-XP des Nutzers |
| `level` | `int` | Aktuelles Level |
| `current_streak` | `int` | Aktuelle Streak (aufeinanderfolgende Tage mit mind. 1 erledigtem Task) |
| `longest_streak` | `int` | Laengste Streak aller Zeiten |
| `xp_for_next_level` | `int` | XP-Schwelle fuer das naechste Level |
| `progress_percent` | `float` | Fortschritt zum naechsten Level in Prozent (0.0 - 100.0) |
| `tasks_completed` | `int` | Gesamtanzahl erledigter Tasks |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/gamification/history`

Gibt den XP-Verlauf des Nutzers pro Tag zurueck. Nuetzlich fuer Diagramme und Fortschrittsvisualisierungen.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `days` | int | 30 | Anzahl Tage zurueck (max 365) |

**Response 200 OK:**
```json
{
  "history": [
    {
      "date": "2026-02-06",
      "xp_earned": 150,
      "tasks_completed": 4
    },
    {
      "date": "2026-02-05",
      "xp_earned": 75,
      "tasks_completed": 2
    },
    {
      "date": "2026-02-04",
      "xp_earned": 200,
      "tasks_completed": 5
    }
  ],
  "total_days": 30
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `history` | `DailyXP[]` | XP-Verlauf pro Tag (absteigend nach Datum) |
| `total_days` | `int` | Angefragter Zeitraum in Tagen |

**DailyXP Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `date` | `str` | Datum im Format `YYYY-MM-DD` |
| `xp_earned` | `int` | An diesem Tag verdiente XP |
| `tasks_completed` | `int` | An diesem Tag erledigte Tasks |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger `days`-Wert (< 1 oder > 365) |

---

### `GET /api/v1/gamification/achievements`

Gibt alle verfuegbaren Achievements mit dem Unlock-Status des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "achievements": [
    {
      "id": "ach-uuid-001",
      "name": "Erste Schritte",
      "description": "Erledige deinen ersten Task",
      "icon": "rocket",
      "category": "beginner",
      "xp_reward": 50,
      "unlocked": true,
      "unlocked_at": "2026-02-01T10:30:00Z"
    },
    {
      "id": "ach-uuid-002",
      "name": "Streak-Starter",
      "description": "Erreiche eine 3-Tage-Streak",
      "icon": "fire",
      "category": "streak",
      "xp_reward": 100,
      "unlocked": true,
      "unlocked_at": "2026-02-04T18:00:00Z"
    },
    {
      "id": "ach-uuid-003",
      "name": "Unaufhaltsam",
      "description": "Erreiche eine 30-Tage-Streak",
      "icon": "trophy",
      "category": "streak",
      "xp_reward": 500,
      "unlocked": false,
      "unlocked_at": null
    },
    {
      "id": "ach-uuid-004",
      "name": "Brain-Builder",
      "description": "Erstelle 10 Brain-Eintraege",
      "icon": "brain",
      "category": "brain",
      "xp_reward": 150,
      "unlocked": false,
      "unlocked_at": null
    }
  ],
  "total_count": 4,
  "unlocked_count": 2
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `achievements` | `AchievementResponse[]` | Alle verfuegbaren Achievements |
| `total_count` | `int` | Gesamtanzahl Achievements |
| `unlocked_count` | `int` | Anzahl freigeschalteter Achievements |

**AchievementResponse Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Achievement-ID |
| `name` | `str` | Achievement-Name |
| `description` | `str` | Beschreibung der Freischaltbedingung |
| `icon` | `str` | Icon-Bezeichnung |
| `category` | `str` | Kategorie: `beginner`, `streak`, `tasks`, `brain`, `special` |
| `xp_reward` | `int` | XP-Belohnung bei Freischaltung |
| `unlocked` | `bool` | Vom Nutzer freigeschaltet? |
| `unlocked_at` | `datetime | null` | Zeitpunkt der Freischaltung (null wenn nicht freigeschaltet) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

## Task Breakdown Endpoints

Die Task-Breakdown-Endpoints erweitern die bestehenden Task-Endpoints unter `/api/v1/tasks/`. Alle erfordern Authentifizierung. Sie ermoeglichen die KI-gestuetzte Zerlegung grosser Tasks in handhabbare Sub-Tasks (ADHS-optimiert: 3-7 Schritte).

### `POST /api/v1/tasks/{id}/breakdown`

Generiert einen KI-gestuetzten Vorschlag zur Zerlegung eines Tasks in 3-7 Sub-Tasks. Die Sub-Tasks werden NICHT sofort erstellt, sondern als Vorschlag zurueckgegeben.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 10/min (AI-Endpoint)

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID des zu zerlegenden Tasks |

**Request Body:** Kein Request Body erforderlich.

**Response 200 OK:**
```json
{
  "parent_task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Umzug vorbereiten",
    "priority": "high",
    "estimated_minutes": 480
  },
  "suggested_subtasks": [
    {
      "title": "Umzugskartons besorgen",
      "description": "10-15 Kartons im Baumarkt kaufen oder bei Nachbarn fragen",
      "estimated_minutes": 30,
      "order": 1
    },
    {
      "title": "Kueche einpacken",
      "description": "Geschirr, Tassen und Kochutensilien sicher verpacken",
      "estimated_minutes": 90,
      "order": 2
    },
    {
      "title": "Umzugshelfer organisieren",
      "description": "Mindestens 2-3 Freunde fuer den Umzugstag anfragen",
      "estimated_minutes": 20,
      "order": 3
    },
    {
      "title": "Transporter reservieren",
      "description": "Mietwagen fuer den 15.03. buchen, Groesse: mind. 3.5t",
      "estimated_minutes": 15,
      "order": 4
    },
    {
      "title": "Adressaenderungen erledigen",
      "description": "Post-Nachsendeauftrag, Versicherungen, Bank, Arbeitgeber informieren",
      "estimated_minutes": 45,
      "order": 5
    }
  ]
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `parent_task` | `object` | Zusammenfassung des Eltern-Tasks |
| `parent_task.id` | `UUID` | Task-ID |
| `parent_task.title` | `str` | Task-Titel |
| `parent_task.priority` | `str` | Prioritaet |
| `parent_task.estimated_minutes` | `int | null` | Geschaetzte Dauer |
| `suggested_subtasks` | `SuggestedSubtask[]` | 3-7 vorgeschlagene Sub-Tasks |

**SuggestedSubtask Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `title` | `str` | Vorgeschlagener Sub-Task-Titel |
| `description` | `str` | Vorgeschlagene Beschreibung |
| `estimated_minutes` | `int` | Geschaetzte Dauer in Minuten |
| `order` | `int` | Empfohlene Reihenfolge (1-basiert) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |
| 409 | `TASK_ALREADY_HAS_SUBTASKS` | Task hat bereits Sub-Tasks |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele AI-Anfragen |
| 503 | `AI_SERVICE_UNAVAILABLE` | KI-Service nicht erreichbar |

---

### `POST /api/v1/tasks/{id}/breakdown/confirm`

Bestaetigt und erstellt die vorgeschlagenen Sub-Tasks. Der Nutzer kann die Vorschlaege vor der Bestaetigung anpassen (Titel, Beschreibung, Dauer aendern oder einzelne Sub-Tasks entfernen).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID des Eltern-Tasks |

**Request Body:**
```json
{
  "subtasks": [
    {
      "title": "Umzugskartons besorgen",
      "description": "10-15 Kartons im Baumarkt kaufen",
      "estimated_minutes": 30
    },
    {
      "title": "Kueche einpacken",
      "description": "Geschirr und Kochutensilien verpacken",
      "estimated_minutes": 90
    },
    {
      "title": "Umzugshelfer organisieren",
      "description": "3 Freunde anfragen",
      "estimated_minutes": 20
    }
  ]
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `subtasks` | `object[]` | Ja | Min 1, Max 10 Sub-Tasks | Liste der zu erstellenden Sub-Tasks |
| `subtasks[].title` | `str` | Ja | Min 1, Max 500 Zeichen | Sub-Task-Titel |
| `subtasks[].description` | `str` | Nein | Max 5000 Zeichen | Sub-Task-Beschreibung |
| `subtasks[].estimated_minutes` | `int` | Nein | Min 1, Max 1440 | Geschaetzte Dauer in Minuten |

**Response 201 Created:**
```json
{
  "parent_task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Umzug vorbereiten",
    "status": "in_progress"
  },
  "created_subtasks": [
    {
      "id": "sub-uuid-001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Umzugskartons besorgen",
      "description": "10-15 Kartons im Baumarkt kaufen",
      "priority": "high",
      "status": "open",
      "due_date": null,
      "completed_at": null,
      "xp_earned": 0,
      "parent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "is_recurring": false,
      "recurrence_rule": null,
      "tags": [],
      "source": "breakdown",
      "source_message_id": null,
      "estimated_minutes": 30,
      "sub_tasks": [],
      "created_at": "2026-02-06T12:00:00Z",
      "updated_at": "2026-02-06T12:00:00Z"
    }
  ]
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `parent_task` | `object` | Zusammenfassung des Eltern-Tasks |
| `parent_task.id` | `UUID` | Eltern-Task-ID |
| `parent_task.title` | `str` | Eltern-Task-Titel |
| `parent_task.status` | `str` | Neuer Status des Eltern-Tasks (wird auf `in_progress` gesetzt) |
| `created_subtasks` | `TaskResponse[]` | Erstellte Sub-Tasks (source=breakdown) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |
| 409 | `TASK_ALREADY_HAS_SUBTASKS` | Task hat bereits Sub-Tasks |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (leere Liste, Titel leer, etc.) |

---

## Nudge Endpoints

Alle Nudge-Endpoints sind unter `/api/v1/nudges/` gruppiert. Alle erfordern Authentifizierung. Nudges sind sanfte Erinnerungen, die ALICE proaktiv sendet, um den Nutzer an faellige oder ueberfaellige Tasks zu erinnern -- mit steigender Intensitaet (gentle, moderate, firm).

### `GET /api/v1/nudges`

Gibt alle aktiven (noch nicht bestaetigten) Nudges des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "nudges": [
    {
      "id": "nudge-uuid-001",
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "task_title": "Arzttermin vereinbaren",
      "nudge_level": "gentle",
      "nudge_type": "deadline_approaching",
      "message": "Hey, dein Arzttermin-Task ist morgen faellig. Magst du den jetzt angehen?",
      "delivered_at": "2026-02-09T09:00:00Z"
    },
    {
      "id": "nudge-uuid-002",
      "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "task_title": "Steuererklaerung abgeben",
      "nudge_level": "moderate",
      "nudge_type": "overdue",
      "message": "Die Steuererklaerung ist seit 2 Tagen ueberfaellig. Soll ich den Task in kleinere Schritte aufteilen?",
      "delivered_at": "2026-02-09T10:00:00Z"
    }
  ],
  "count": 2
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `nudges` | `NudgeResponse[]` | Aktive Nudges (unbestaetigt) |
| `count` | `int` | Anzahl aktiver Nudges |

**NudgeResponse Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Nudge-ID |
| `task_id` | `UUID` | Zugehoeriger Task |
| `task_title` | `str` | Titel des zugehoerigen Tasks |
| `nudge_level` | `str` | Intensitaet: `gentle`, `moderate`, `firm` |
| `nudge_type` | `str` | Typ: `deadline_approaching`, `overdue`, `stale`, `follow_up` |
| `message` | `str` | Personalisierte Erinnerungsnachricht |
| `delivered_at` | `datetime` | Zeitpunkt der Zustellung |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `POST /api/v1/nudges/{id}/acknowledge`

Markiert einen Nudge als gelesen/bestaetigt. Der Nudge wird danach nicht mehr in der aktiven Liste angezeigt.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Nudge-ID |

**Request Body:** Kein Request Body erforderlich.

**Response 200 OK:**
```json
{
  "id": "nudge-uuid-001",
  "acknowledged_at": "2026-02-09T09:15:00Z"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Nudge-ID |
| `acknowledged_at` | `datetime` | Zeitpunkt der Bestaetigung |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `NUDGE_NOT_FOUND` | Nudge existiert nicht oder gehoert nicht dem User |
| 409 | `NUDGE_ALREADY_ACKNOWLEDGED` | Nudge wurde bereits bestaetigt |

---

### `GET /api/v1/nudges/history`

Gibt den Nudge-Verlauf des Nutzers zurueck (inklusive bereits bestaetigter Nudges).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 50 | Items pro Seite (max 100) |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "nudge-uuid-001",
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "task_title": "Arzttermin vereinbaren",
      "nudge_level": "gentle",
      "nudge_type": "deadline_approaching",
      "message": "Hey, dein Arzttermin-Task ist morgen faellig. Magst du den jetzt angehen?",
      "delivered_at": "2026-02-09T09:00:00Z",
      "acknowledged_at": "2026-02-09T09:15:00Z"
    }
  ],
  "next_cursor": "nudge-uuid-002",
  "has_more": true,
  "total_count": 24
}
```

**Response Schema:** `PaginatedResponse<NudgeHistoryResponse>`

**NudgeHistoryResponse Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Nudge-ID |
| `task_id` | `UUID` | Zugehoeriger Task |
| `task_title` | `str` | Titel des zugehoerigen Tasks |
| `nudge_level` | `str` | Intensitaet: `gentle`, `moderate`, `firm` |
| `nudge_type` | `str` | Typ: `deadline_approaching`, `overdue`, `stale`, `follow_up` |
| `message` | `str` | Personalisierte Erinnerungsnachricht |
| `delivered_at` | `datetime` | Zeitpunkt der Zustellung |
| `acknowledged_at` | `datetime | null` | Zeitpunkt der Bestaetigung (null wenn noch offen) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

## Dashboard Endpoint

Der Dashboard-Endpoint aggregiert verschiedene Datenquellen fuer eine kompakte Uebersicht auf dem Startbildschirm.

### `GET /api/v1/dashboard/summary`

Gibt aggregierte Dashboard-Daten zurueck: Heutige Tasks, Gamification-Status, naechste Deadline, aktive Nudges und ein Motivationszitat.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "today_tasks": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Arzttermin",
      "priority": "high",
      "status": "open",
      "due_date": "2026-02-06T14:00:00Z",
      "estimated_minutes": 60
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "title": "Einkaufen",
      "priority": "low",
      "status": "open",
      "due_date": null,
      "estimated_minutes": 30
    }
  ],
  "gamification": {
    "total_xp": 1250,
    "level": 5,
    "streak": 7,
    "progress_percent": 83.3
  },
  "next_deadline": {
    "task_title": "Arzttermin",
    "due_date": "2026-02-06T14:00:00Z"
  },
  "active_nudges_count": 2,
  "motivational_quote": "Jeder grosse Schritt beginnt mit einem kleinen. Du schaffst das!"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `today_tasks` | `DashboardTask[]` | Heutige Tasks (max 10, sortiert nach Prioritaet) |
| `gamification` | `object` | Gamification-Kurzuebersicht |
| `gamification.total_xp` | `int` | Gesamt-XP |
| `gamification.level` | `int` | Aktuelles Level |
| `gamification.streak` | `int` | Aktuelle Streak |
| `gamification.progress_percent` | `float` | Fortschritt zum naechsten Level (0.0 - 100.0) |
| `next_deadline` | `object | null` | Naechster faelliger Task (null wenn keine Deadlines) |
| `next_deadline.task_title` | `str` | Titel des Tasks |
| `next_deadline.due_date` | `datetime` | Faelligkeitsdatum |
| `active_nudges_count` | `int` | Anzahl aktiver (unbestaetigter) Nudges |
| `motivational_quote` | `str` | Kontextabhaengiges Motivationszitat |

**DashboardTask Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Task-ID |
| `title` | `str` | Task-Titel |
| `priority` | `str` | Prioritaet |
| `status` | `str` | Status |
| `due_date` | `datetime | null` | Faelligkeitsdatum |
| `estimated_minutes` | `int | null` | Geschaetzte Dauer |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

## ADHS Settings Endpoints

Die ADHS-Settings-Endpoints sind unter `/api/v1/settings/` gruppiert. Alle erfordern Authentifizierung. Sie verwalten die ADHS-spezifischen Einstellungen des Nutzers wie Nudge-Intensitaet, Auto-Breakdown, Gamification-Toggle und Ruhezeiten.

### `GET /api/v1/settings/adhs`

Gibt die aktuellen ADHS-Einstellungen des Nutzers zurueck. Falls noch keine Einstellungen existieren, werden Defaults zurueckgegeben.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "adhs_mode": true,
  "nudge_intensity": "medium",
  "auto_breakdown": true,
  "gamification_enabled": true,
  "focus_timer_minutes": 25,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "preferred_reminder_times": ["09:00", "13:00", "18:00"]
}
```

**Response Schema (ADHSSettingsResponse):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `adhs_mode` | `bool` | ADHS-Modus aktiviert? (Aktiviert Nudges, Breakdown, Gamification) |
| `nudge_intensity` | `str` | Nudge-Intensitaet: `low`, `medium`, `high` |
| `auto_breakdown` | `bool` | Automatischen Task-Breakdown vorschlagen bei grossen Tasks? |
| `gamification_enabled` | `bool` | Gamification-System (XP, Level, Achievements) aktiviert? |
| `focus_timer_minutes` | `int` | Standard-Dauer des Fokus-Timers in Minuten |
| `quiet_hours_start` | `str` | Beginn der Ruhezeit (Format: `HH:MM`, keine Nudges in dieser Zeit) |
| `quiet_hours_end` | `str` | Ende der Ruhezeit (Format: `HH:MM`) |
| `preferred_reminder_times` | `str[]` | Bevorzugte Uhrzeiten fuer Erinnerungen (Format: `HH:MM`) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/settings/adhs`

Aktualisiert die ADHS-Einstellungen des Nutzers. Partial Update: Nur uebergebene Felder werden geaendert.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "nudge_intensity": "high",
  "focus_timer_minutes": 15,
  "quiet_hours_start": "21:00",
  "preferred_reminder_times": ["08:00", "12:00", "17:00", "20:00"]
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `adhs_mode` | `bool` | Nein | -- | ADHS-Modus ein/ausschalten |
| `nudge_intensity` | `str` | Nein | `low`, `medium`, `high` | Nudge-Intensitaet |
| `auto_breakdown` | `bool` | Nein | -- | Auto-Breakdown ein/ausschalten |
| `gamification_enabled` | `bool` | Nein | -- | Gamification ein/ausschalten |
| `focus_timer_minutes` | `int` | Nein | Min 5, Max 120 | Fokus-Timer-Dauer |
| `quiet_hours_start` | `str` | Nein | Format `HH:MM` | Beginn der Ruhezeit |
| `quiet_hours_end` | `str` | Nein | Format `HH:MM` | Ende der Ruhezeit |
| `preferred_reminder_times` | `str[]` | Nein | Max 10 Zeiten, Format `HH:MM` | Bevorzugte Erinnerungszeiten |

**Response 200 OK:** `ADHSSettingsResponse` (aktualisierte Einstellungen, siehe oben)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (ungueltige Intensitaet, Timer-Wert ausserhalb des Bereichs, ungueltiges Zeitformat) |

---

### `POST /api/v1/settings/push-token`

Registriert einen Expo Push Notification Token fuer den authentifizierten Nutzer. Der Token wird verwendet, um Push-Benachrichtigungen an das Geraet des Nutzers zu senden (z.B. Deadline-Erinnerungen, Streak-Warnungen, Tagesplaene).

**Auth:** Bearer Token erforderlich
**Rate Limit:** Standard (60/min)

**Request Body:**
```json
{
  "expo_push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `expo_push_token` | `str` | Ja | Min. 10 Zeichen | Expo Push Notification Token vom Geraet |

**Response:** 204 No Content

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Token zu kurz oder ungueltig |

---

## Neue Fehlercodes (Phase 3)

Die folgenden Fehlercodes ergaenzen die bestehende Fehlercodes-Tabelle aus ENDPOINTS.md:

| Code | HTTP Status | Beschreibung | Phase |
|---|---|---|---|
| `TASK_ALREADY_HAS_SUBTASKS` | 409 | Task hat bereits Sub-Tasks (Breakdown nicht moeglich) | 3 |
| `NUDGE_NOT_FOUND` | 404 | Nudge nicht gefunden | 3 |
| `NUDGE_ALREADY_ACKNOWLEDGED` | 409 | Nudge wurde bereits bestaetigt | 3 |

---

## Zusammenfassung Phase 3

### Phase 3: ADHS-Modus

| Method | Path | Beschreibung | Auth | Rate Limit |
|---|---|---|---|---|
| GET | `/api/v1/gamification/stats` | XP, Level, Streak, Fortschritt | Ja | 60/min |
| GET | `/api/v1/gamification/history` | XP-Verlauf pro Tag | Ja | 60/min |
| GET | `/api/v1/gamification/achievements` | Achievements mit Unlock-Status | Ja | 60/min |
| POST | `/api/v1/tasks/{id}/breakdown` | KI-Task-Zerlegung vorschlagen | Ja | 10/min |
| POST | `/api/v1/tasks/{id}/breakdown/confirm` | Sub-Tasks bestaetigen und erstellen | Ja | 60/min |
| GET | `/api/v1/nudges` | Aktive Nudges abrufen | Ja | 60/min |
| POST | `/api/v1/nudges/{id}/acknowledge` | Nudge bestaetigen | Ja | 60/min |
| GET | `/api/v1/nudges/history` | Nudge-Verlauf (paginiert) | Ja | 60/min |
| GET | `/api/v1/dashboard/summary` | Aggregierte Dashboard-Daten | Ja | 60/min |
| GET | `/api/v1/settings/adhs` | ADHS-Einstellungen lesen | Ja | 60/min |
| PUT | `/api/v1/settings/adhs` | ADHS-Einstellungen aendern | Ja | 60/min |
| POST | `/api/v1/settings/push-token` | Expo Push Token registrieren | Ja | 60/min |

**Gesamt Phase 3: 12 neue Endpoints**

### Gesamt ueber alle Phasen

| Phase | Endpoints | Status |
|---|---|---|
| Phase 1: Foundation | 10 | Implementiert |
| Phase 2: Core Features | 14 | Implementiert |
| Phase 3: ADHS-Modus | 12 | Spezifiziert |
| **Gesamt** | **36** | -- |
