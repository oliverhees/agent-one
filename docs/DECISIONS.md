# Architektur-Entscheidungen (ADRs)

**Projekt:** ALICE (Adaptive Living Intelligence & Cognitive Enhancement)
**Datum:** 2026-02-06
**Autor:** Architect Agent

---

## ADR-001: FastAPI statt Next.js API Routes

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE ist eine KI-intensive Applikation mit Multi-Agent-Orchestrierung (CrewAI), Embedding-Generierung (Sentence Transformers), Vektor-Suche (pgvector), Background-Jobs (Celery) und proaktiven Scheduled Tasks (APScheduler). Das Backend muss nahtlos mit dem Python AI/ML-Ecosystem interagieren. Das Frontend ist eine React Native App, kein Web-Frontend -- es gibt also keinen Vorteil durch ein einheitliches JavaScript-Ecosystem.

**Entscheidung:**
Wir verwenden Python 3.12+ mit FastAPI als Backend-Framework.

**Begruendung:**
1. **Python AI/ML Ecosystem:** CrewAI, LangChain, Sentence Transformers, anthropic SDK, openai SDK -- alles nativ Python. Keine JavaScript-Wrapper oder Bridges noetig.
2. **Async-First:** FastAPI basiert auf Starlette und unterstuetzt nativ async/await, WebSockets und Server-Sent Events. Performance vergleichbar mit Node.js fuer I/O-bound Workloads.
3. **Pydantic v2:** Automatische Request/Response-Validierung, OpenAPI-Generierung, und Type Safety. Besser integriert als Zod in Next.js API Routes.
4. **Background Jobs:** Celery mit Redis ist der De-facto-Standard fuer Python Background Jobs. Keine vergleichbare Loesung in Next.js fuer die Komplexitaet unserer proaktiven Features.
5. **Kein Web-Frontend:** Da die einzige Nutzerschnittstelle eine React Native App ist, gibt es keinen Vorteil durch Server-Side Rendering oder das Next.js Ecosystem.

**Alternativen:**
- **Next.js API Routes:** Verworfen. Kein nativer Zugriff auf Python AI/ML Libraries. Wuerde Python-Microservices oder Bridges erfordern und die Architektur unnoetig verkomplizieren.
- **Django + DRF:** Verworfen. Schwerer, synchron-first, schlechtere WebSocket/SSE-Unterstuetzung. Zu viel Overhead fuer unsere Anforderungen.
- **Flask:** Verworfen. Kein nativer async Support, keine automatische OpenAPI-Generierung, weniger moderner als FastAPI.

**Konsequenzen:**
- Zwei separate Projekte (Backend: Python, Frontend: TypeScript). Kein Code-Sharing zwischen Frontend und Backend.
- Team benoetigt Python- UND TypeScript-Kompetenz.
- API-Dokumentation wird automatisch via FastAPI/Swagger generiert.
- Deployment wird ueber Docker gemanaged, daher kein Problem mit separaten Runtimes.

---

## ADR-002: SQLAlchemy statt Prisma

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
Das Projekt verwendet Python (FastAPI) als Backend. Wir benoetigen ein ORM das async Datenbankzugriffe unterstuetzt, mit PostgreSQL 16 und der pgvector Extension kompatibel ist, und Migrations-Management bietet.

**Entscheidung:**
Wir verwenden SQLAlchemy 2.0 (async) mit Alembic fuer Migrationen.

**Begruendung:**
1. **Python-native:** SQLAlchemy ist das Standard-ORM fuer Python. Nahtlose Integration mit FastAPI und dem restlichen Python-Ecosystem.
2. **Async Support:** SQLAlchemy 2.0 unterstuetzt native async Sessions ueber asyncpg. Ideal fuer FastAPI.
3. **pgvector Kompatibilitaet:** SQLAlchemy hat ueber `pgvector-python` volle Unterstuetzung fuer VECTOR-Spalten und Similarity-Suche.
4. **Alembic Migrationen:** Ausgereiftes, bewaehertes Migrations-Tool mit auto-generate Support. Bidirektionale Migrationen (up/down).
5. **Flexibilitaet:** SQLAlchemy erlaubt sowohl ORM-Style (Models) als auch Core-Style (Raw SQL) Queries. Wichtig fuer komplexe pgvector-Queries.
6. **Community & Maturity:** 20+ Jahre Entwicklung, groesste Python-ORM-Community, exzellente Dokumentation.

**Alternativen:**
- **Prisma:** Verworfen. Prisma ist primaer fuer Node.js/TypeScript. Der Python-Client (prisma-client-py) ist ein Community-Projekt mit eingeschraenktem Feature-Set und keine pgvector-Unterstuetzung.
- **Tortoise ORM:** Verworfen. Weniger ausgereift, kleinere Community, keine vergleichbare Migrations-Loesung.
- **Raw SQL (asyncpg):** Verworfen. Zu viel Boilerplate, keine Typsicherheit, kein Schema-Management.

**Konsequenzen:**
- Schema wird in Python (SQLAlchemy Models) definiert, nicht in einem separaten Schema-File.
- Migrationen werden ueber Alembic verwaltet (`alembic revision --autogenerate`).
- SCHEMA.md muss manuell synchron gehalten werden mit den SQLAlchemy Models.
- Entwickler muessen SQLAlchemy 2.0 async Patterns kennen (AsyncSession, select(), etc.).

---

## ADR-003: JWT statt Session-based Auth

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE ist eine Mobile App (React Native). Die Authentifizierung muss funktionieren ueber:
- HTTPS REST API (Standard-Requests)
- WebSocket-Verbindungen (Token als Query-Parameter)
- Server-Sent Events (Token als Header)
- Push Notifications (Token fuer Device-Identifikation)

Ausserdem soll die API stateless sein und horizontal skalierbar.

**Entscheidung:**
Wir verwenden JWT (JSON Web Tokens) mit Access Token (15 Minuten TTL) + Refresh Token (7 Tage TTL) mit Token-Rotation.

**Begruendung:**
1. **Stateless:** JWTs erfordern keine serverseitige Session-Speicherung. Der Server muss lediglich die Signatur pruefen. Ideal fuer horizontale Skalierung.
2. **Mobile-Kompatibilitaet:** JWTs koennen in expo-secure-store gespeichert werden. Kein Cookie-Management noetig (problematisch auf Mobile).
3. **Multi-Protocol:** JWT funktioniert ueber HTTP Headers, WebSocket Query-Parameter, und SSE Headers gleichermaessen.
4. **Token-Rotation:** Refresh Tokens werden bei Nutzung invalidiert und neu ausgestellt. Dies verhindert Replay-Angriffe.
5. **Token-Blacklist:** Fuer Logout wird der Access Token in einer Redis-Blacklist gespeichert (TTL = Restlaufzeit). Minimaler Overhead.
6. **Kurze Access Token TTL:** 15 Minuten minimiert das Risiko bei Token-Kompromittierung.

**Alternativen:**
- **Session-based Auth (Cookies):** Verworfen. Cookies funktionieren schlecht in React Native. Session-Storage erfordert serverseitige Speicherung und ist nicht stateless.
- **BetterAuth:** Verworfen. BetterAuth ist fuer Next.js optimiert und nicht kompatibel mit FastAPI/Python.
- **OAuth2 (mit externem Provider):** Verworfen fuer Phase 1. Social Login (Google, Apple) kann spaeter als Ergaenzung hinzugefuegt werden, aber das Basis-Auth muss unabhaengig funktionieren.

**Konsequenzen:**
- Token-Blacklist (Redis) muss geprueft werden bei jedem authentifizierten Request. Minimaler Latenz-Overhead (~1ms).
- Refresh Token muss sicher gespeichert werden (expo-secure-store nutzt iOS Keychain / Android Keystore).
- Auto-Refresh-Logik muss im React Native API Client implementiert werden.
- Abgelaufene Access Tokens fuehren zu 401. Der Client muss automatisch refreshen und den Request wiederholen.

---

## ADR-004: CrewAI fuer Multi-Agent Orchestrierung

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE ist ein proaktiver AI-Assistent, der mehrere Aufgaben gleichzeitig bearbeiten muss: Chat beantworten, Tasks managen, Wissen durchsuchen, Mentioned Items extrahieren, und Tagesplaene erstellen. Diese Aufgaben erfordern spezialisierte "Sub-Agents" die koordiniert zusammenarbeiten.

**Entscheidung:**
Wir verwenden CrewAI als Multi-Agent Orchestrierung Framework.

**Begruendung:**
1. **Agent-Spezialisierung:** CrewAI erlaubt es, spezialisierte Agents mit eigenen Tools, Rollen und Zielen zu definieren. Jeder Agent ist ein Experte fuer seinen Bereich (Tasks, Brain, Planung, Analyse).
2. **Orchestrierung:** Der ALICE Orchestrator entscheidet dynamisch welche Sub-Agents fuer eine Anfrage relevant sind. Nicht jeder Agent wird bei jeder Nachricht aktiviert.
3. **Tool-Integration:** CrewAI Agents koennen Python-Funktionen als Tools nutzen. Unsere Services (TaskService, BrainService) werden als Tools exponiert.
4. **Streaming-Kompatibel:** CrewAI unterstuetzt Streaming-Callbacks, die wir fuer SSE/WebSocket Token-Streaming nutzen.
5. **Python-native:** CrewAI ist ein Python-Framework das nahtlos mit unserem FastAPI-Backend integriert.
6. **Graceful Degradation:** Bei CrewAI-Fehlern kann auf einen direkten Claude-API-Aufruf zurueckgefallen werden.

**Alternativen:**
- **LangChain Agents:** Verworfen. LangChain Agents sind weniger strukturiert als CrewAI. Kein klares Konzept fuer Agent-Spezialisierung und -Koordination.
- **Autogen (Microsoft):** Verworfen. Fokus auf Multi-Agent-Konversation, nicht auf Tool-basierte Ausfuehrung. Weniger geeignet fuer unseren Use Case.
- **Custom Orchestrierung:** Verworfen. Wuerde Monate Eigenentwicklung erfordern fuer Features die CrewAI out-of-the-box bietet.
- **Direkter LLM-Aufruf (kein Agents):** Verworfen. Funktioniert fuer einfache Chat-Antworten, aber nicht fuer komplexe Aufgaben die Tool-Nutzung und Multi-Step-Reasoning erfordern.

**Konsequenzen:**
- Dependency auf CrewAI Framework (aktive Entwicklung, potentiell Breaking Changes).
- Agent-Definitionen und Tools muessen gewartet werden.
- LLM-Kosten steigen, da Agent-Orchestrierung mehr Tokens verbraucht als direkte Aufrufe.
- Latenz erhoeht sich leicht durch Agent-Koordination (mittigiert durch Streaming).
- Testbarkeit: Agents muessen mit Mock-LLMs getestet werden.

---

## ADR-005: pgvector statt eigenstaendiger Vektordatenbank

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE benoetigt Vektor-Embeddings fuer die semantische Suche im Second Brain (RAG). Die Embeddings muessen gespeichert, indexiert und effizient durchsuchbar sein. Gleichzeitig muessen sie mit den relationalen Daten (Brain-Eintraege, User-Zuordnung) verknuepft sein.

**Entscheidung:**
Wir verwenden pgvector als PostgreSQL Extension statt einer eigenstaendigen Vektordatenbank.

**Begruendung:**
1. **Vereinfachung:** Eine einzige Datenbank fuer relationale UND Vektordaten. Kein zweites System zu deployen, zu monitoren und zu warten.
2. **Joins:** Vektor-Suchergebnisse koennen direkt mit relationalen Daten gejoined werden (z.B. `WHERE user_id = $1 ORDER BY embedding <=> $query_vector`). Bei separater Vektordatenbank muessten IDs hin- und hergereicht werden.
3. **ACID-Transaktionen:** Embedding-Inserts und Entry-Inserts koennen in der gleichen Transaktion erfolgen. Konsistenz ist garantiert.
4. **HNSW Index:** pgvector unterstuetzt HNSW-Indexierung fuer effiziente Approximate Nearest Neighbor Suche. Ausreichend fuer unsere Datenmenge (bis 10.000 User, geschaetzt 50-100 Embeddings pro User = max ~1 Million Vektoren).
5. **Hosting-Vereinfachung:** Eine PostgreSQL-Instanz auf Coolify statt PostgreSQL + Pinecone/Qdrant/Weaviate. Reduziert Kosten und Komplexitaet.
6. **384 Dimensionen:** Sentence Transformers (`all-MiniLM-L6-v2`) generiert 384-dimensionale Vektoren. Das ist klein genug fuer effiziente pgvector-Suche.

**Alternativen:**
- **Pinecone:** Verworfen. Managed Service, externe Abhaengigkeit, Kosten, Latenz durch Netzwerk-Roundtrip, kein Self-Hosting.
- **Qdrant:** Verworfen. Gute Self-Hosted Option, aber ein zusaetzlicher Service zu deployen und zu warten. Fuer unsere Datenmenge Overkill.
- **Weaviate:** Verworfen. Aehnlich wie Qdrant -- zu viel Overhead fuer unsere Anforderungen.
- **ChromaDB:** Verworfen. Primaer fuer Prototyping, nicht fuer Production. Keine PostgreSQL-Integration.

**Konsequenzen:**
- pgvector Extension muss in der PostgreSQL-Installation aktiviert sein. Wir verwenden das `pgvector/pgvector:pg16` Docker Image.
- Bei sehr grosser Datenmenge (>> 1 Million Vektoren) muss die Skalierung evaluiert werden. Migration zu einer dedizierten Vektordatenbank ist dann moeglich.
- HNSW-Index-Parameter (m, ef_construction) muessen getunt werden basierend auf der tatsaechlichen Datenmenge.
- Embedding-Dimensionen sind auf 384 festgelegt (Modell-Abhaengigkeit).

---

## ADR-006: React Native + Expo statt Flutter

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE ist eine Cross-Platform Mobile App fuer iOS und Android. Die App benoetigt: Push Notifications, Secure Storage, WebSocket-Kommunikation, Audio-Aufnahme (Voice), Background-Processing, und Deep Linking. Die Entwicklung soll effizient sein mit einer einzigen Codebase.

**Entscheidung:**
Wir verwenden React Native mit Expo als Mobile-Framework.

**Begruendung:**
1. **JavaScript/TypeScript Ecosystem:** Das Team hat starke TypeScript-Kompetenz. React Native ermoeglicht Code-Sharing von Types, Validierungs-Schemas (Zod) und Utility-Funktionen.
2. **Expo:** Managed Workflow reduziert nativen Konfigurationsaufwand drastisch. Expo-Module fuer Push Notifications, SecureStore, Audio, etc. sind battle-tested.
3. **OTA Updates:** Expo ermoeglicht Over-the-Air Updates ohne App Store Review. Kritisch fuer schnelle Bug-Fixes und Feature-Rollouts.
4. **Expo Router:** File-based Routing aehnlich Next.js. Vertrautes Entwicklungsmodell. Deep Linking out-of-the-box.
5. **NativeWind/Tailwind:** Styling mit Tailwind CSS Syntax. Konsistent mit dem Web-Ecosystem des Teams.
6. **Library-Ecosystem:** Zustand, TanStack Query, React Hook Form, Zod -- alles verfuegbar und optimiert fuer React Native.
7. **EAS Build:** Expo Application Services fuer Cloud Builds. Kein lokales Xcode/Android Studio Setup noetig fuer Builds.

**Alternativen:**
- **Flutter:** Verworfen. Dart-Sprache erfordert neue Lernkurve. Kein Code-Sharing mit dem TypeScript-Ecosystem. Kleineres Library-Ecosystem fuer unsere spezifischen Anforderungen (AI-Integration, Streaming).
- **Swift/Kotlin (Native):** Verworfen. Zwei separate Codebases wuerde den Entwicklungsaufwand verdoppeln. Nicht realisierbar mit unserem Team und Zeitplan.
- **Ionic/Capacitor:** Verworfen. Web-basiert mit nativem Wrapper. Performance-Probleme bei komplexen UIs und Animationen.

**Konsequenzen:**
- Expo Managed Workflow. Bei Bedarf kann ein "Eject" zu einem Bare Workflow durchgefuehrt werden fuer nativen Code.
- Native Module die nicht ueber Expo verfuegbar sind erfordern einen Expo Config Plugin oder Eject.
- Performance ist generell gut, aber fuer sehr komplexe Animationen (Gamification) muessen React Native Reanimated und optimierte Rendering-Strategien verwendet werden.
- App Store Submission ueber EAS Build (Apple Developer Account + Google Play Developer Account erforderlich).

---

## ADR-007: Celery + Redis fuer Background Jobs

**Datum:** 2026-02-06 | **Status:** Akzeptiert

**Kontext:**
ALICE hat umfangreiche Background-Processing-Anforderungen:
- **Embedding-Generierung:** Sentence Transformers Encoding ist CPU-intensiv und darf den API-Thread nicht blockieren.
- **Proaktive Jobs:** Taegliche Tagesplanung, Follow-Up-Checks, Deadline-Monitoring -- alles zeitgesteuert.
- **Push Notifications:** Versand muss asynchron erfolgen.
- **Content Ingestion:** URL-Scraping und Datei-Parsing sind lang laufende Operationen.
- **Calendar Sync:** Periodischer Sync mit Google Calendar.

**Entscheidung:**
Wir verwenden Celery als Task Queue mit Redis als Message Broker, und APScheduler fuer zeitgesteuerte Jobs die Celery Tasks dispatchen.

**Begruendung:**
1. **Celery:** Der De-facto-Standard fuer Python Background Jobs. Robustes Task-Queue-System mit Retry, Priority, Rate Limiting, und Monitoring.
2. **Redis als Broker:** Redis ist bereits Teil unseres Stacks (Token Blacklist, Cache). Kein zusaetzlicher Service noetig. Performant genug fuer unsere Anforderungen.
3. **APScheduler:** Leichtgewichtiger Scheduler der in-process laeuft und Celery Tasks zu konfigurierten Zeiten dispatcht. Einfacher als ein separater Cron-Service.
4. **Skalierbarkeit:** Celery Worker koennen horizontal skaliert werden. Mehr Worker = mehr Durchsatz. Unabhaengig von der API-Skalierung.
5. **Monitoring:** Celery Flower bietet ein Web-Dashboard fuer Job-Monitoring. Alternativ Redis-basiertes Monitoring.
6. **Retry-Mechanismen:** Celery bietet eingebaute Retry-Logik mit Exponential Backoff. Kritisch fuer LLM-API-Aufrufe die fehlschlagen koennen.

**Alternativen:**
- **asyncio.create_task():** Verworfen. Funktioniert fuer einfache Fire-and-Forget Tasks, aber keine Retry-Logik, kein Monitoring, keine Persistenz, kein Scheduling.
- **Dramatiq:** Verworfen. Gute Alternative zu Celery, aber kleinere Community und weniger Battle-Tested.
- **RQ (Redis Queue):** Verworfen. Simpler als Celery, aber weniger Features (kein eingebautes Scheduling, weniger Retry-Optionen).
- **ARQ:** Verworfen. Async-native, aber kleinere Community und weniger Dokumentation.

**Konsequenzen:**
- Celery Worker laeuft als separater Docker Container. Erhoehter Ressourcenverbrauch.
- APScheduler muss als Singleton laufen (genau 1 Instanz). Bei mehreren API-Instanzen muss der Scheduler in einem separaten Container laufen.
- Redis muss persistent konfiguriert sein (RDB Snapshots) damit keine Jobs bei Redis-Restart verloren gehen.
- Celery Tasks muessen idempotent sein (Retry-sicher).
- Monitoring via Celery Flower oder Redis-basierte Dashboards.
