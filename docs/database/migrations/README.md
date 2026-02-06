# Datenbank-Migrationen

Dieses Verzeichnis enthält die Dokumentation aller Alembic-Migrationen für die ALICE Datenbank.

---

## Migrations-Historie

| Nr. | Datei | Datum | Phase | Beschreibung | Status |
|-----|-------|-------|-------|--------------|--------|
| 001 | `001_initial_schema.py` | 2026-02-06 | 1 | Grundstruktur: users, conversations, messages, refresh_tokens | Erstellt |

---

## Konventionen

### Dateinamen

Migrations-Dateien folgen dem Schema:
```
XXX_beschreibung.py
```

- **XXX** = Fortlaufende 3-stellige Nummer (001, 002, ...)
- **beschreibung** = Kurze, beschreibende Bezeichnung in snake_case

Beispiele:
- `001_initial_schema.py`
- `002_add_tasks_table.py`
- `003_add_brain_entries.py`

### Dokumentation

Jede Migration MUSS eine begleitende Markdown-Dokumentation haben:
```
XXX_beschreibung.md
```

Diese enthält:
- Übersicht der Änderungen
- Datenverlust-Risiko
- Reversibilitäts-Bewertung
- Testing-Schritte
- Rollback-Plan

---

## Migration erstellen

### 1. Automatisch (mit autogenerate)

Wenn SQLAlchemy Models geändert wurden:

```bash
cd backend
alembic revision --autogenerate -m "Beschreibung der Änderung"
```

Alembic vergleicht die Models mit dem DB-Schema und generiert automatisch die Migration.

**WICHTIG:** Überprüfe die generierte Migration manuell. Autogenerate erkennt nicht alles!

### 2. Manuell (ohne autogenerate)

Für komplexere Änderungen oder wenn autogenerate nicht ausreicht:

```bash
cd backend
alembic revision -m "Beschreibung der Änderung"
```

Dann manuell `upgrade()` und `downgrade()` in der generierten Datei implementieren.

---

## Migration anwenden

### Upgrade (vorwärts)

```bash
cd backend

# Alle ausstehenden Migrationen anwenden
alembic upgrade head

# Nur eine Migration vorwärts
alembic upgrade +1

# Zu einer bestimmten Revision
alembic upgrade 001_initial_schema
```

### Downgrade (rückwärts)

```bash
cd backend

# Eine Migration zurück
alembic downgrade -1

# Zu einer bestimmten Revision
alembic downgrade 001_initial_schema

# Alle Migrationen zurücksetzen
alembic downgrade base
```

### Status anzeigen

```bash
cd backend

# Aktuelle Revision
alembic current

# Historie anzeigen
alembic history

# Ausstehende Migrationen
alembic history --verbose
```

---

## Workflow

### 1. Vor der Migration

- [ ] Backup der Datenbank erstellen (bei Production)
- [ ] SCHEMA.md mit geplanten Änderungen aktualisieren
- [ ] Migration lokal erstellen und testen

### 2. Migration erstellen

- [ ] SQLAlchemy Models anpassen (falls nötig)
- [ ] Alembic Migration generieren (auto oder manuell)
- [ ] `upgrade()` Funktion überprüfen/implementieren
- [ ] `downgrade()` Funktion überprüfen/implementieren
- [ ] Migration lokal testen (`upgrade` + `downgrade`)

### 3. Dokumentation

- [ ] `XXX_beschreibung.md` erstellen
- [ ] SCHEMA.md aktualisieren (Letzte Migration, Tabellen, Indizes)
- [ ] README.md Historie-Tabelle aktualisieren

### 4. Nach der Migration

- [ ] Migration in Git committen
- [ ] Linear-Task als "Done" markieren
- [ ] Team Lead informieren

---

## Wichtige Regeln

### 1. NIEMALS bestehende Migrationen ändern

Migrationen sind **unveränderlich**. Wenn eine Migration bereits committed wurde, darf sie NICHT mehr geändert werden.

Falls ein Fehler gefunden wird:
- Erstelle eine **neue** Migration die den Fehler korrigiert
- Dokumentiere den Fehler in der neuen Migration

### 2. Jede Migration MUSS reversibel sein

Jede `upgrade()` Funktion MUSS eine funktionierende `downgrade()` Funktion haben.

Ausnahme: Datenverändernde Operationen, die nicht sicher rückgängig gemacht werden können (z.B. Spalte löschen mit Daten). Diese müssen explizit dokumentiert werden.

### 3. Foreign Keys IMMER mit ON DELETE Aktion

Standard: `ON DELETE CASCADE` (wenn Child-Daten gelöscht werden sollen)
Alternative: `ON DELETE SET NULL` (wenn Child-Daten erhalten bleiben sollen)

### 4. Timestamps IMMER mit Timezone

NIEMALS `DateTime` ohne `timezone=True` verwenden.
IMMER `DateTime(timezone=True)` verwenden.

### 5. Indizes für häufige Queries

Erstelle Indizes für:
- Foreign Keys (für JOIN-Performance)
- WHERE-Klauseln (für Filter-Performance)
- ORDER BY-Klauseln (für Sortier-Performance)

### 6. Datenverlust dokumentieren

Wenn eine Migration potenziell Daten löscht:
- **STOPP** → Team Lead informieren
- Datenverlust-Risiko in Migrations-Doku klar benennen
- Backup-Plan dokumentieren
- Bestätigung vom Team Lead einholen

---

## Testing

Jede Migration MUSS lokal getestet werden:

### 1. Upgrade testen

```bash
cd backend

# Migration anwenden
alembic upgrade head

# Datenbank inspizieren
psql $DATABASE_URL
\dt  # Tabellen anzeigen
\d+ users  # Schema einer Tabelle anzeigen
\di  # Indizes anzeigen
```

### 2. Downgrade testen

```bash
cd backend

# Migration zurückrollen
alembic downgrade -1

# Überprüfen dass Tabellen/Spalten entfernt wurden
psql $DATABASE_URL
\dt
```

### 3. Re-Upgrade testen

```bash
cd backend

# Migration erneut anwenden
alembic upgrade head

# Sicherstellen dass es funktioniert
psql $DATABASE_URL
\dt
```

---

## Troubleshooting

### Problem: "Target database is not up to date"

```bash
# Aktuelle Revision anzeigen
alembic current

# Sollte die erwartete Revision sein
# Falls nicht: manuelle Korrektur der alembic_version Tabelle (Vorsicht!)
```

### Problem: Migration schlägt fehl

```bash
# 1. Downgrade zur letzten funktionierenden Version
alembic downgrade -1

# 2. Fehler in Migration-File beheben

# 3. Erneut versuchen
alembic upgrade head
```

### Problem: Alembic kennt aktuelle Revision nicht

```bash
# alembic_version Tabelle manuell aktualisieren
psql $DATABASE_URL
UPDATE alembic_version SET version_num = '001_initial_schema';
```

---

## Kontakt

Bei Fragen oder Problemen:
- **Database Manager** Agent kontaktieren
- SCHEMA.md als Single Source of Truth konsultieren
- Linear-Task erstellen für DB-Änderungen
