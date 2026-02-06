# Migration 001: Initial Schema

**Datum:** 2026-02-06
**Autor:** Database Manager
**Phase:** 1 - Foundation
**Status:** Erstellt (nicht angewendet)

---

## Übersicht

Diese Migration erstellt die Grundstruktur der ALICE Datenbank mit den vier Kern-Tabellen für Authentifizierung und Chat-Funktionalität.

---

## Änderungen

### Extensions

- **pgvector aktiviert** - Wird für zukünftige Vector Embeddings benötigt (Phase 2)

### Enums

- **message_role** - Enum für Nachrichtenrollen: `user`, `assistant`, `system`

### Tabellen

#### 1. users

Speichert registrierte Benutzerkonten.

**Spalten:**
- `id` - UUID, Primary Key
- `email` - VARCHAR(255), UNIQUE, NOT NULL
- `password_hash` - VARCHAR(255), NOT NULL (bcrypt)
- `display_name` - VARCHAR(100), NOT NULL
- `avatar_url` - VARCHAR(500), NULL
- `is_active` - BOOLEAN, NOT NULL, DEFAULT true
- `created_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()
- `updated_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()

**Indizes:**
- `ix_users_email` - UNIQUE auf `email` (Login-Performance)
- `ix_users_is_active` - auf `is_active` (Filterung aktiver User)
- `ix_users_id` - auf `id` (Primary Key Index)

#### 2. refresh_tokens

Speichert JWT Refresh Tokens für sichere Authentifizierung mit Token Rotation.

**Spalten:**
- `id` - UUID, Primary Key
- `user_id` - UUID, NOT NULL, FK -> users(id) ON DELETE CASCADE
- `token` - VARCHAR(500), UNIQUE, NOT NULL
- `expires_at` - TIMESTAMPTZ, NOT NULL
- `is_revoked` - BOOLEAN, NOT NULL, DEFAULT false
- `created_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()
- `updated_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()

**Indizes:**
- `ix_refresh_tokens_user_id` - auf `user_id` (User-Lookup)
- `ix_refresh_tokens_token` - UNIQUE auf `token` (Token-Validierung)
- `ix_refresh_tokens_id` - auf `id` (Primary Key Index)

#### 3. conversations

Speichert Chat-Konversationen zwischen Nutzer und ALICE.

**Spalten:**
- `id` - UUID, Primary Key
- `user_id` - UUID, NOT NULL, FK -> users(id) ON DELETE CASCADE
- `title` - VARCHAR(255), NULL (auto-generiert oder manuell gesetzt)
- `created_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()
- `updated_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()

**Indizes:**
- `ix_conversations_user_id` - auf `user_id` (User-Konversationen)
- `ix_conversations_id` - auf `id` (Primary Key Index)

#### 4. messages

Speichert einzelne Nachrichten innerhalb einer Konversation.

**Spalten:**
- `id` - UUID, Primary Key
- `conversation_id` - UUID, NOT NULL, FK -> conversations(id) ON DELETE CASCADE
- `role` - message_role ENUM, NOT NULL
- `content` - TEXT, NOT NULL
- `metadata` - JSONB, NULL (Model-Info, Tokens, Duration, etc.)
- `created_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()
- `updated_at` - TIMESTAMPTZ, NOT NULL, DEFAULT now()

**Indizes:**
- `ix_messages_conversation_id` - auf `conversation_id` (Nachrichten einer Konversation)
- `ix_messages_id` - auf `id` (Primary Key Index)

---

## Datenverlust-Risiko

**Keine** - Dies ist die erste Migration. Es existieren noch keine Daten.

---

## Reversibilität

**Vollständig reversibel** - `alembic downgrade` entfernt alle Tabellen, Indizes, Enums und die pgvector Extension.

Die Downgrade-Reihenfolge beachtet Foreign Key Constraints:
1. refresh_tokens
2. messages
3. conversations
4. users
5. message_role ENUM
6. vector Extension

---

## Abhängigkeiten

### Software
- PostgreSQL 16+
- pgvector Extension (wird automatisch aktiviert)
- SQLAlchemy 2.0+
- Alembic 1.13+

### Environment Variables
- `DATABASE_URL` - PostgreSQL Connection String

---

## Testing-Schritte

Nach Anwendung der Migration:

1. **Tabellen vorhanden?**
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```
   Erwartung: users, refresh_tokens, conversations, messages

2. **pgvector Extension aktiv?**
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
   Erwartung: 1 Zeile

3. **Foreign Keys korrekt?**
   ```sql
   SELECT conname, conrelid::regclass, confrelid::regclass
   FROM pg_constraint
   WHERE contype = 'f'
   ORDER BY conname;
   ```
   Erwartung: 4 Foreign Keys (refresh_tokens->users, conversations->users, messages->conversations)

4. **Indizes vorhanden?**
   ```sql
   SELECT indexname FROM pg_indexes
   WHERE schemaname = 'public'
   ORDER BY indexname;
   ```
   Erwartung: Alle 10 Indizes aus der Migration

5. **Enum Type existiert?**
   ```sql
   SELECT typname, enumlabel
   FROM pg_enum e
   JOIN pg_type t ON e.enumtypid = t.oid
   WHERE typname = 'message_role';
   ```
   Erwartung: 3 Zeilen (user, assistant, system)

---

## Rollback-Plan

Falls Probleme auftreten:

```bash
# Rollback der Migration
alembic downgrade -1

# Oder zurück zur Basis
alembic downgrade base
```

---

## Nächste Schritte

Nach erfolgreicher Anwendung dieser Migration:

1. **Backend-Dev** kann Auth-Endpoints implementieren (Login, Register, Refresh)
2. **Backend-Dev** kann Chat-Endpoints implementieren (Nachrichten senden/empfangen)
3. **Test-Engineer** kann Integrationstests für Auth + Chat schreiben
4. **Database-Mgr** kann mit Phase 2 fortfahren (Tasks, Brain Entries)

---

## Notizen

- **Hinweis:** Einige Felder aus dem vollständigen SCHEMA.md wurden bewusst NICHT in Phase 1 implementiert:
  - `users.device_token` (kommt in Phase 3 mit Notifications)
  - `users.timezone` (kommt bei Bedarf)
  - `users.preferences` JSONB (kommt in Phase 2/3)
  - `conversations.is_archived` (kommt bei Bedarf)
  - `messages.token_count` (kann aus metadata extrahiert werden)

- Diese Felder werden in späteren Migrationen ergänzt, wenn die jeweiligen Features implementiert werden.

- **Performance:** Die gewählten Indizes decken die wichtigsten Queries ab:
  - User-Login (email lookup)
  - Token-Validierung (token lookup)
  - User-Konversationen (user_id lookup)
  - Konversations-Nachrichten (conversation_id lookup)

- **Sicherheit:** Passwort-Hashes werden nie im API-Response zurückgegeben (Pydantic Schema-Validierung).

---

## Review Checklist

- [x] Migration erstellt mit `upgrade()` und `downgrade()`
- [x] Alle Tabellen haben Primary Keys (UUID)
- [x] Alle Timestamps haben Timezone-Awareness (TIMESTAMPTZ)
- [x] Foreign Keys haben ON DELETE CASCADE
- [x] Indizes für häufige Queries erstellt
- [x] pgvector Extension aktiviert
- [x] Downgrade-Funktion vollständig reversibel
- [x] SCHEMA.md aktualisiert
- [x] Migrationsdokumentation erstellt
