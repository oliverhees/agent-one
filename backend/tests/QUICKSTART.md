# Quick Start - Backend Tests

## 🚀 Tests in 3 Schritten

### 1️⃣ PostgreSQL starten
```bash
docker compose up -d db
```

Warte bis der Container healthy ist:
```bash
docker compose ps db
```

### 2️⃣ Test-Datenbank einrichten
```bash
./scripts/setup-test-db.sh
```

### 3️⃣ Tests ausführen
```bash
cd backend
pytest
```

## ✅ Erfolgreiche Test-Session

```
====================================== test session starts ======================================
platform linux -- Python 3.12.x, pytest-8.x.x, pluggy-1.x.x
rootdir: /backend
configfile: pyproject.toml
testpaths: tests
plugins: asyncio-0.24.x, cov-6.x.x
collected 47 items

tests/test_auth.py ....................... [ 44%]
tests/test_chat.py ........... [ 68%]
tests/test_security.py ............... [100%]

====================================== 47 passed in 2.34s =======================================
```

## 🔧 Troubleshooting

### Problem: Connection refused
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Lösung:** PostgreSQL läuft nicht
```bash
docker compose up -d db
```

### Problem: Database does not exist
```
sqlalchemy.exc.OperationalError: database "alice_test" does not exist
```

**Lösung:** Test-DB erstellen
```bash
./scripts/setup-test-db.sh
```

### Problem: Permission denied
```
permission denied while trying to connect to the Docker daemon
```

**Lösung:** Docker mit sudo starten oder User zur docker Gruppe hinzufügen
```bash
sudo usermod -aG docker $USER
# Neu einloggen
```

## 📊 Coverage Report

```bash
pytest --cov=app --cov-report=html
```

Öffne dann `htmlcov/index.html` im Browser.

## 🎯 Best Practices

- **Vor jedem Test-Run:** Stelle sicher dass PostgreSQL läuft
- **Nach Code-Änderungen:** Lasse alle Tests laufen, nicht nur die betroffenen
- **Test-DB aufräumen:** Bei merkwürdigem Verhalten `./scripts/setup-test-db.sh` ausführen
- **Coverage:** Ziel ist >= 80% für produktionsrelevanten Code
