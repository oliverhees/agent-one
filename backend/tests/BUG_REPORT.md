# Bug Report - Phase 1 Backend Tests

## Gefundene Bugs und Probleme

### BUG 1 | Schwere: Critical
**Test:** SQLite Kompatibilität für Tests
**Erwartet:** Tests sollten mit SQLite in-memory DB laufen können
**Tatsächlich:** Models verwenden PostgreSQL-spezifische Typen die mit SQLite inkompatibel sind
**Dateien:**
- `/backend/app/models/base.py` - Line 22: `UUID(as_uuid=True)` von `sqlalchemy.dialects.postgresql`
- `/backend/app/models/conversation.py` - Line 23: `PG_UUID(as_uuid=True)`
- `/backend/app/models/message.py` - Line 32: `PG_UUID(as_uuid=True)` + Line 53: `JSONB`
- `/backend/app/models/refresh_token.py` - Line 23: `PG_UUID(as_uuid=True)`

**Problem:**
`sqlalchemy.dialects.postgresql.UUID` und `JSONB` funktionieren NICHT mit SQLite. Tests mit SQLite in-memory DB werden fehlschlagen.

**Lösungsvorschläge:**
1. **Option A (empfohlen für Tests):** Conditional imports - verwende generisches `String` für SQLite, `UUID` für PostgreSQL
2. **Option B:** Nutze PostgreSQL testcontainer statt SQLite
3. **Option C:** Verwende `sqlalchemy.types.UUID` statt `postgresql.UUID` (falls verfügbar in neueren Versionen)

**Impact:** Tests werden aktuell NICHT lauffähig sein ohne PostgreSQL

---

### BUG 2 | Schwere: High
**Test:** test_refresh_revoked_token
**Erwartet:** Nach Token-Refresh sollte das alte Token revoked sein und nicht mehr funktionieren
**Tatsächlich:** Token Rotation ist implementiert, aber es gibt keinen Test ob der neue Token funktioniert UND der alte nicht mehr
**Datei:** `/backend/app/services/auth.py` - Line 199-216

**Problem:**
Die Token-Rotation-Logik revoked das alte Token (Line 200: `db_token.is_revoked = True`), aber es gibt keinen expliziten Test der:
1. Prüft ob das NEUE Token funktioniert
2. Prüft ob das ALTE Token wirklich nicht mehr verwendet werden kann

**Empfehlung:** Test existiert bereits in `test_auth.py::TestTokenRefresh::test_refresh_revoked_token`

---

### BUG 3 | Schwere: Medium
**Test:** Chat SSE Streaming Error Handling
**Erwartet:** Bei Fehlern sollte ein "error" SSE Event gesendet werden
**Tatsächlich:** Error Handling ist vorhanden, aber keine Tests dafür
**Datei:** `/backend/app/api/v1/chat.py` - Line 145-152

**Problem:**
Der Error Handler in der SSE Stream-Funktion ist implementiert:
```python
except Exception as e:
    error_data = {"detail": str(e), "code": "STREAM_ERROR"}
    yield f"event: error\n"
    yield f"data: {json.dumps(error_data)}\n\n"
```

Aber es gibt keinen Test der diesen Error-Fall provoziert und prüft ob das error Event korrekt gesendet wird.

**Empfehlung:** Test für Stream-Errors hinzufügen (z.B. ungültige conversation_id, AI Service Fehler, etc.)

---

### BUG 4 | Schwere: Medium
**Test:** Rate Limiting
**Erwartet:** Rate Limits sollten getestet werden
**Tatsächlich:** Rate Limiting Dependencies sind in den Endpoints definiert, aber keine Tests dafür
**Dateien:**
- `/backend/app/api/v1/auth.py` - Line 25: `dependencies=[Depends(auth_rate_limit)]`
- `/backend/app/api/v1/chat.py` - Line 33: `dependencies=[Depends(chat_rate_limit)]`

**Problem:**
Rate Limiting ist implementiert über Dependencies, aber:
1. Keine Tests die prüfen ob Rate Limits greifen
2. Rate Limit Datei (`/backend/app/core/rate_limit.py`) wurde nicht gelesen - kann nicht beurteilen ob die Implementierung korrekt ist

**Empfehlung:** Tests für Rate Limiting hinzufügen (100 Requests nacheinander senden, prüfen ob 429 zurückkommt)

---

### BUG 5 | Schwere: Low
**Test:** Message Metadata Validation
**Erwartet:** Metadata sollte optional und vom Typ dict sein
**Tatsächlich:** Metadata wird als `dict | None` deklariert mit `default=dict`
**Datei:** `/backend/app/models/message.py` - Line 51-56

**Problem:**
```python
metadata_: Mapped[dict[str, Any] | None] = mapped_column(
    "metadata",
    JSONB,
    nullable=True,
    default=dict,  # <- Problem: mutable default
    ...
)
```

Mutable defaults (`default=dict`) können zu Problemen führen. Sollte `default=None` oder `default=lambda: {}` sein.

**Impact:** Niedrig - In der Praxis funktioniert es wahrscheinlich, aber ist nicht Best Practice.

---

### BUG 6 | Schwere: Low
**Test:** Password Validation Feedback
**Erwartet:** Benutzer bekommt klare Fehlermeldungen welche Passwort-Anforderung fehlt
**Tatsächlich:** Validierung funktioniert, aber testet nur eine Anforderung zur Zeit
**Datei:** `/backend/app/schemas/user.py` - Line 35-55

**Problem:**
Die Validierung wirft beim ersten Fehler eine Exception. Wenn das Passwort z.B. zu kurz ist UND kein Großbuchstabe hat, bekommt der Benutzer nur "zu kurz" zu sehen.

**Empfehlung:**
Nicht critical, aber UX könnte verbessert werden durch Collection aller Fehler und Rückgabe als Liste.

---

### BUG 7 | Schwere: Low
**Test:** Conversation Title Auto-Generation
**Erwartet:** Conversation title sollte automatisch generiert werden wenn nicht angegeben
**Tatsächlich:** Title wird als `None` gespeichert, keine Auto-Generation implementiert
**Dateien:**
- `/backend/app/api/v1/chat.py` - Line 82: `title=None  # Will be auto-generated later`
- `/backend/app/services/chat.py` - Line 43-47

**Problem:**
Der Kommentar sagt "Will be auto-generated later", aber die Implementierung fehlt komplett. Das ist entweder ein TODO oder ein veralteter Kommentar.

**Impact:** Niedrig - Funktional kein Problem, aber der Kommentar ist irreführend.

---

## Zusammenfassung

**Critical Bugs:** 1 (SQLite Inkompatibilität)
**High Bugs:** 1 (Token Rotation Test)
**Medium Bugs:** 2 (Error Handling Tests, Rate Limiting Tests)
**Low Bugs:** 3 (Metadata default, Password validation UX, Auto-title comment)

**Empfohlene nächste Schritte:**
1. **SOFORT:** BUG 1 beheben - entweder PostgreSQL testcontainer verwenden oder Models SQLite-kompatibel machen
2. Token Rotation Tests erweitern
3. Error-Handling-Tests hinzufügen
4. Rate-Limiting-Tests hinzufügen (wenn Zeit)
