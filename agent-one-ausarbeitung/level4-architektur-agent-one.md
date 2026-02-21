# Agent One Level 4: Die Zero-Data-Architektur — Daten gehören dem Kunden, immer.

## Die Antwort auf die wichtigste Frage: Woher kommen die Daten, und wohin gehen sie?

Level 1-3 haben definiert WAS der Agent kann. **Level 4 beantwortet die Frage die über Erfolg oder Scheitern entscheidet:** Wie fließen die Daten, wem gehören sie, und wie wird das System deployed?

Die Kurzantwort: **Der Agent ist reine Intelligenz-Middleware. Er VERARBEITET Daten, aber er SPEICHERT keine Kundendaten permanent.** Die Daten bleiben dort wo sie hingehören — beim Kunden.

---

## 1. Das Grundprinzip: Zero-Data-Retention Agent

### 1.1 Was bedeutet "Agent als Middleware"?

Stell dir den Agent vor wie einen brillanten Mitarbeiter der jeden Tag ins Büro kommt, die Post durcharbeitet, Anrufe beantwortet, Termine organisiert — aber am Ende des Tages nichts mit nach Hause nimmt. Die Akten bleiben im Schrank des Kunden.

```
KUNDENDATEN                    AGENT ONE                    KUNDENSYSTEME
(bleiben hier)              (reine Intelligenz)            (bleiben hier)
                                    
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│ E-Mails      │───lesen───▶│              │───senden──▶│ E-Mail       │
│ (Gmail/O365) │            │   Reasoning  │            │ Ausgang      │
└──────────────┘            │   Engine     │            └──────────────┘
                            │              │
┌──────────────┐            │  Entscheidet │            ┌──────────────┐
│ Kalender     │───lesen───▶│  was zu tun  │───buchen──▶│ Kalender     │
│ (Google/MS)  │            │  ist         │            │ Einträge     │
└──────────────┘            │              │            └──────────────┘
                            │  Speichert   │
┌──────────────┐            │  KEINE       │            ┌──────────────┐
│ CRM/DMS      │───lesen───▶│  Kundendaten │───update──▶│ CRM/DMS      │
│ (Kundencloud)│            │  permanent   │            │ (Kundencloud)│
└──────────────┘            │              │            └──────────────┘
                            └──────┬───────┘
                                   │
                          WAS der Agent speichert:
                          ✓ Wie er arbeiten soll (Prompts, Workflows)
                          ✓ Was er gelernt hat (Graphiti Knowledge Graph)
                          ✓ Trust Scores + Audit Logs
                          ✗ KEINE E-Mail-Inhalte
                          ✗ KEINE Dokumente
                          ✗ KEINE Mandantendaten
                          ✗ KEINE persönlichen Dateien
```

### 1.2 Was der Agent speichert vs. was er nicht speichert

| Kategorie | Speichert Agent? | Wo liegt es? | Warum? |
|-----------|-----------------|-------------|--------|
| **E-Mail-Inhalte** | ✗ NEIN | Gmail/Outlook des Kunden | Kein Grund Kopien zu halten |
| **Dokumente/Dateien** | ✗ NEIN | Cloud-Speicher des Kunden | Originale bleiben beim Kunden |
| **Kalender-Daten** | ✗ NEIN | Google/Outlook Kalender | Live-Zugriff via API |
| **Mandanten-Stammdaten** | ✗ NEIN | CRM/DMS des Kunden | System of Record beim Kunden |
| **Telefon-Aufnahmen** | ✗ NEIN | Vapi/Kunden-Telefonie | DSGVO-sensibel |
| **Knowledge Graph** | ✓ JA | Agent One Infrastruktur | Gelernte Beziehungen + Fakten |
| **Trust Scores** | ✓ JA | Agent One Infrastruktur | Autonomie-Steuerung |
| **Audit Logs** | ✓ JA | Agent One Infrastruktur | Compliance-Nachweis |
| **Workflow-Konfiguration** | ✓ JA | Agent One Infrastruktur | Wie der Agent arbeitet |
| **Agent-Prompts** | ✓ JA | Agent One Infrastruktur | Anweisungen für den Agent |

### 1.3 Der Knowledge Graph — Die clevere Grauzone

Graphiti speichert **abstrahierte Beziehungen und Fakten** — keine Rohdaten:

```
Was Graphiti speichert:
  Entity: "Mandant Müller"
  Fact: "Bevorzugt informellen E-Mail-Ton"
  Fact: "Steuererklärung fällig am 31.03.2026"
  Relation: "Müller → ist_mandant_von → Steuerberater Schmidt"

Was Graphiti NICHT speichert:
  ✗ Den vollständigen Text der E-Mail an Müller
  ✗ Die Steuererklärung selbst
  ✗ Bankkontodaten von Müller
  ✗ Persönliche Gesundheitsdaten
```

Das ist ein entscheidender Unterschied für die DSGVO: Der Knowledge Graph enthält **Metadaten und Beziehungswissen** — nicht die Primärdaten selbst. Wie das Gedächtnis eines guten Mitarbeiters: Er weiß dass Herr Müller informelle Ansprache bevorzugt, aber er hat nicht die komplette Kundenakte im Kopf gespeichert.

**PII-Handling im Knowledge Graph:**

Für §203 StGB-Berufe (Steuerberater, Anwälte, Ärzte) kann das zu eng sein. Deshalb: **Microsoft Presidio** als PII-Filter BEVOR Daten in Graphiti landen:

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def sanitize_for_knowledge_graph(text: str) -> str:
    """Entfernt PII bevor Fakten in Graphiti gespeichert werden"""
    results = analyzer.analyze(
        text=text,
        entities=["PHONE_NUMBER", "IBAN", "EMAIL_ADDRESS", 
                  "CREDIT_CARD", "MEDICAL_LICENSE"],
        language="de"
    )
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text

# Beispiel:
# Input: "Müller hat IBAN DE89370400440532013000"
# Output: "Müller hat IBAN <IBAN>"
# → Graphiti speichert: "Müller hat eine IBAN hinterlegt"
```

---

## 2. Die Drei Deployment-Modelle

### 2.1 Die Matrix — Welches Modell für wen?

Das ist DIE Entscheidung. Und die Antwort ist: **Es gibt nicht EIN Modell — es gibt drei, und jeder Kunde wählt seins:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    MODELL A              MODELL B             MODELL C      │
│    "Full Cloud"          "Hybrid"             "On-Premise"  │
│    (SaaS)                (Best of Both)       (Self-Hosted) │
│                                                             │
│    Agent ONE             Agent ONE             Agent ONE    │
│    hostet alles          hostet Intelligenz    läuft beim   │
│                          Daten beim Kunden     Kunden       │
│                                                             │
│    €149-299/Mo           €299-499/Mo          €999+/Mo      │
│                                                             │
│    Für:                  Für:                 Für:          │
│    Coaches, Berater,     Steuerberater,       Kliniken,     │
│    kleine Agenturen      Anwälte, Ärzte       Behörden,     │
│    Freelancer            (§203 StGB)          Konzerne      │
│                                                             │
│    Setup: Minuten        Setup: Stunden       Setup: Tage   │
│    Wartung: Zero         Wartung: Minimal     Wartung: Hoch │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Modell A: Full Cloud SaaS — "Einfach nutzen"

```
┌──────────────────────────────────────────────────────┐
│                HETZNER CLOUD (DE)                     │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         Agent One Plattform (Multi-Tenant)      │  │
│  │                                                  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │  │
│  │  │LangGraph│ │Graphiti │ │ PostgreSQL        │  │  │
│  │  │Engine   │ │+ Falkor │ │ (Tenants, Auth,   │  │  │
│  │  │         │ │DB       │ │  Audit, Trust)    │  │  │
│  │  └─────────┘ └─────────┘ └──────────────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │  │
│  │  │Redis    │ │LiteLLM  │ │ Langfuse          │  │  │
│  │  │Cache    │ │Gateway  │ │ Observability     │  │  │
│  │  └─────────┘ └─────────┘ └──────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Multi-Tenant Isolation via Graphiti group_id         │
│  + Row-Level Security in PostgreSQL                   │
│  + Envelope Encryption pro Tenant                     │
└──────────────────────────────────────────────────────┘
         │                          │
    MCP Connectors            Expo App + Dashboard
    (OAuth 2.0)               (HTTPS/WSS)
         │
    ┌────┴──────────────────────────┐
    │  Kundensysteme (NICHT kopiert) │
    │  • Gmail/Outlook (IMAP/API)   │
    │  • Google Calendar             │
    │  • CRM (HubSpot, Pipedrive)   │
    │  • Cloud-Speicher              │
    └───────────────────────────────┘
```

**Vorteile:** Sofort einsatzbereit. Zero Wartung. Automatische Updates. Skaliert ohne Kundenzutun. Perfekt für 80% aller KMUs die keine Geheimhaltungspflicht nach §203 StGB haben.

**Datenfluss:** Agent greift via OAuth 2.0 auf Kundensysteme zu. Verarbeitet Daten in Echtzeit. Speichert nur abstrahierte Fakten im Knowledge Graph. E-Mail-Inhalte, Dokumente, Kalenderdaten werden NICHT in Agent One gespeichert — sie bleiben in Gmail/Outlook/etc.

**DSGVO-Konformität:** Auftragsverarbeitungsvertrag (AVV) nach Art. 28 DSGVO. Daten bleiben in Deutschland (Hetzner). Löschung auf Anfrage. Standard-Datenschutzklauseln.

**Hosting empfohlen:** Hetzner Cloud in Falkenstein oder Nürnberg. Für wen VPS reicht: Hostinger KVM 2 oder größer (https://hostinger.com/kiheroes mit Code KIHEROES für 5% Rabatt).

### 2.3 Modell B: Hybrid — "Intelligenz von uns, Daten bei dir"

```
┌──────────────────────────────────────┐
│     HETZNER CLOUD (DE)               │
│     Agent One Intelligence Layer     │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ LangGraph + LiteLLM + Redis │    │
│  │ (Reasoning, Routing, Cache)  │    │
│  └──────────────┬───────────────┘    │
│                 │ API Calls           │
│  ┌──────────────┴───────────────┐    │
│  │ Langfuse + Audit Logs        │    │
│  │ (anonymisiert)                │    │
│  └──────────────────────────────┘    │
└──────────────────┬───────────────────┘
                   │
          Verschlüsselte API
          (mTLS + API Keys)
                   │
┌──────────────────┴───────────────────┐
│     KUNDEN-INFRASTRUKTUR             │
│     (VPS, eigener Server, oder       │
│      Private Cloud)                   │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ Graphiti + FalkorDB           │    │
│  │ (Knowledge Graph mit ALLEN    │    │
│  │  Mandantendaten)              │    │
│  └──────────────────────────────┘    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ PostgreSQL                    │    │
│  │ (Trust Scores, Konfiguration) │    │
│  └──────────────────────────────┘    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ Data Connector Layer          │    │
│  │ MCP Server (lokal)            │    │
│  │ → Gmail, Kalender, CRM, DMS  │    │
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

**Der Clou:** Die LLM-Reasoning-Engine (die teuren API-Calls) läuft zentral bei uns. Aber der Knowledge Graph und alle Datenverbindungen laufen beim Kunden. Das bedeutet:

- **Mandantendaten verlassen nie die Kunden-Infrastruktur**
- Der Agent sendet nur **anonymisierte Reasoning-Anfragen** an die Cloud
- Beispiel: Statt "Schreib eine E-Mail an Müller, IBAN DE89..." sendet er "Schreib eine höfliche Zahlungserinnerung an [MANDANT_ID_47]"
- Die Antwort kommt zurück, wird lokal mit den echten Daten angereichert und erst dann versendet

**Für wen:** Steuerberater, Anwälte, Ärzte — alle mit §203 StGB Berufsgeheimnis. Die Mandantendaten verlassen nie den Kunden-Server. Die KI-Intelligenz wird trotzdem zentral genutzt und ständig verbessert.

**Setup-Aufwand:** Ein Docker-Compose Stack beim Kunden deployen. Wir liefern ein vorkonfiguriertes Image. Einmalige Einrichtung ~2-4 Stunden. Danach automatische Updates des lokalen Stacks.

### 2.4 Modell C: Full On-Premise — "Alles bei mir"

```
┌──────────────────────────────────────────────┐
│     KUNDEN-SERVER / PRIVATE CLOUD            │
│     (Alles läuft hier)                       │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │         Agent One (Self-Hosted)         │  │
│  │                                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ │  │
│  │  │LangGraph│ │Graphiti │ │PostgreSQL│ │  │
│  │  │Engine   │ │+ Falkor │ │          │ │  │
│  │  └─────────┘ └─────────┘ └──────────┘ │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ │  │
│  │  │Redis    │ │LiteLLM  │ │Langfuse  │ │  │
│  │  │Cache    │ │Gateway  │ │          │ │  │
│  │  └─────────┘ └─────────┘ └──────────┘ │  │
│  │  ┌─────────────────────────────────────┐│ │
│  │  │ Optional: Lokales LLM (Llama/Mistral)││ │
│  │  │ für maximale Datensouveränität       ││ │
│  │  └─────────────────────────────────────┘│ │
│  └────────────────────────────────────────┘  │
│                                              │
│  Ausgehende Verbindungen nur zu LLM-APIs     │
│  (oder komplett air-gapped mit lokalem LLM)  │
└──────────────────────────────────────────────┘
```

**Für wen:** Kliniken, Behörden, Konzerne mit eigenem Rechenzentrum. Maximale Kontrolle, maximaler Aufwand.

**Unser Beitrag:** Lizenzgebühr + Support-Vertrag. Wir liefern das Docker-Image, der Kunde betreibt es. Optional: Managed Service wo wir den Server betreuen.

### 2.5 Entscheidungsmatrix

| Kriterium | Modell A (SaaS) | Modell B (Hybrid) | Modell C (On-Prem) |
|-----------|----------------|-------------------|-------------------|
| **Datensouveränität** | ★★★☆☆ Gut (DE) | ★★★★★ Maximal | ★★★★★ Maximal |
| **Setup-Geschwindigkeit** | ★★★★★ Minuten | ★★★☆☆ Stunden | ★★☆☆☆ Tage |
| **Wartungsaufwand** | ★★★★★ Zero | ★★★★☆ Minimal | ★★☆☆☆ Hoch |
| **Kosten** | ★★★★★ Niedrig | ★★★☆☆ Mittel | ★★☆☆☆ Hoch |
| **§203 StGB-tauglich** | ✗ Nein | ✓ Ja | ✓ Ja |
| **Offline-fähig** | ✗ Nein | ✗ Nein | ✓ Mit lokalem LLM |
| **Skalierbarkeit** | ★★★★★ Auto | ★★★☆☆ Manuell | ★★☆☆☆ Manuell |
| **Zielgruppe** | 80% aller KMUs | §203-Berufe | Enterprise/Behörden |
| **Preis** | €149-299/Mo | €299-499/Mo | €999+/Mo |

**Die strategische Empfehlung:**

Starte mit **Modell A** — schnellster Weg zum Markt, niedrigste Kosten, höchste Marge. Baue Modell B als zweite Stufe wenn die ersten §203-Kunden (Benjamin Arras!) unterschriftsreif sind. Modell C ist Zukunftsmusik für Enterprise-Kunden ab Jahr 2.

---

## 3. Die Connector-Architektur — MCP als universeller USB-C

### 3.1 Warum MCP die Antwort auf "Wie binde ich neue Tools an?" ist

Die Frage "wie bindet man neue Tools an am besten und auch hier so einfach wie nur möglich" hat seit November 2024 eine definitive Antwort: **Model Context Protocol (MCP)**.

MCP ist für KI-Agents was USB-C für Geräte ist — ein universeller Standard der alles mit allem verbindet. Statt für jede Integration eigenen Code zu schreiben, nutzt jeder Agent denselben Standard.

```
VORHER (ohne MCP):                    NACHHER (mit MCP):

Agent ──custom code──▶ Gmail          Agent ──MCP──▶ Gmail MCP Server
Agent ──custom code──▶ Calendar       Agent ──MCP──▶ Calendar MCP Server
Agent ──custom code──▶ CRM            Agent ──MCP──▶ CRM MCP Server
Agent ──custom code──▶ DMS            Agent ──MCP──▶ DMS MCP Server

4 Integrationen = 4x custom Code      4 Integrationen = 1x MCP Standard
Jede bricht anders                     Alle funktionieren gleich
```

**Der aktuelle Stand (Feb 2026):**
- **1.000+ Open-Source MCP Server** auf GitHub verfügbar
- Adoptiert von **Anthropic, OpenAI, Google DeepMind, Microsoft**
- **Linux Foundation** hostet das Projekt seit Dezember 2025
- Anthropic hat im September 2025 eine offizielle Registry gelauncht
- **Anthropic selbst empfiehlt** Code-Execution mit MCP für effizientere Token-Nutzung

### 3.2 Die Dreischicht-Connector-Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    SCHICHT 3: AGENT LAYER               │
│                                                         │
│    LangGraph Supervisor + Sub-Agents                    │
│    Nutzt MCP Tools wie ein Mensch Tools nutzt           │
│    "Ich brauche die letzten E-Mails" → MCP Call         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    SCHICHT 2: MCP GATEWAY               │
│                    (Security + Routing)                  │
│                                                         │
│    ┌──────────────────────────────────────────────────┐ │
│    │  MCP Gateway (inspiriert von Lasso/Peta)         │ │
│    │                                                   │ │
│    │  • OAuth 2.1 Authentication pro Connector        │ │
│    │  • Rate Limiting pro Tenant + Tool               │ │
│    │  • PII-Filter (Presidio) auf ein-/ausgehende     │ │
│    │    Daten                                          │ │
│    │  • Audit Logging: Jeder MCP Call wird geloggt    │ │
│    │  • Permission Scopes: Agent darf nur was erlaubt │ │
│    │  • Schema Validation: Typ-Prüfung auf Requests   │ │
│    └──────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    SCHICHT 1: MCP SERVER                 │
│                    (Connector Layer)                     │
│                                                         │
│    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐  │
│    │Gmail  │ │Google │ │Hub-   │ │DATEV  │ │Custom │  │
│    │MCP    │ │Cal    │ │Spot   │ │MCP    │ │MCP    │  │
│    │Server │ │MCP    │ │MCP    │ │Server │ │Server │  │
│    └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘  │
│        │         │         │         │         │       │
│    OAuth2     OAuth2    OAuth2    OAuth2    API Key     │
│        │         │         │         │         │       │
│    ┌───┴───┐ ┌───┴───┐ ┌───┴───┐ ┌───┴───┐ ┌───┴───┐ │
│    │Gmail  │ │Google │ │Hub-   │ │DATEV  │ │Kunden │  │
│    │API    │ │Cal API│ │Spot   │ │API    │ │System │  │
│    │       │ │       │ │API    │ │       │ │       │  │
│    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Wie ein neuer Connector in 30 Minuten entsteht

Das ist der Killer: **Ein neuer MCP Server ist trivial zu bauen.** Jeder MCP Server ist ein kleines Programm das "Tools" exponiert die der Agent nutzen kann.

**Beispiel: DATEV-Connector für Steuerberater**

```python
# datev_mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("datev-connector")

@server.tool()
async def get_mandant_fristen(mandant_id: str) -> list[TextContent]:
    """Ruft offene Fristen für einen Mandanten aus DATEV ab"""
    fristen = await datev_api.get_fristen(mandant_id)
    return [TextContent(
        type="text",
        text=json.dumps(fristen, ensure_ascii=False)
    )]

@server.tool()
async def get_mandant_ustva(mandant_id: str, monat: str) -> list[TextContent]:
    """Ruft USt-VA Daten für einen Mandanten und Monat ab"""
    ustva = await datev_api.get_ustva(mandant_id, monat)
    return [TextContent(
        type="text", 
        text=json.dumps(ustva, ensure_ascii=False)
    )]

@server.tool()
async def create_buchung(
    mandant_id: str, 
    betrag: float, 
    konto_soll: str, 
    konto_haben: str,
    text: str
) -> list[TextContent]:
    """Erstellt eine Buchung in DATEV (benötigt Review-Genehmigung)"""
    # Agent One's Trust System entscheidet ob Auto oder Review
    buchung = await datev_api.create_buchung(
        mandant_id, betrag, konto_soll, konto_haben, text
    )
    return [TextContent(type="text", text=f"Buchung {buchung.id} erstellt")]

# Start
server.run()
```

Das war's. **30 Zeilen Code** und der Agent kann mit DATEV sprechen. Der Agent entdeckt automatisch welche Tools verfügbar sind (Capability Discovery) und nutzt sie intelligent.

### 3.4 Der MCP Connector Marketplace

Für das Ökosystem bauen wir einen **Connector-Marktplatz** — aber im Gegensatz zu OpenClaws unsicherem Skill-Store mit abgesicherter Architektur (Level 2):

```
┌────────────────────────────────────────────────────────┐
│              AGENT ONE CONNECTOR MARKETPLACE            │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  OFFIZIELLE CONNECTORS (von uns gewartet)       │   │
│  │                                                   │   │
│  │  📧 E-Mail: Gmail, Outlook, IMAP                │   │
│  │  📅 Kalender: Google Calendar, Outlook Calendar  │   │
│  │  📞 Telefonie: Vapi, Sipgate, Placetel          │   │
│  │  💼 CRM: HubSpot, Pipedrive, Salesforce         │   │
│  │  📁 Cloud: Google Drive, OneDrive, Nextcloud    │   │
│  │  💰 Buchhaltung: DATEV, Lexoffice, sevDesk      │   │
│  │  📋 Projektmanagement: Asana, Trello, Notion    │   │
│  │  💬 Kommunikation: Slack, Teams, WhatsApp Bus.  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  COMMUNITY CONNECTORS (geprüft + signiert)      │   │
│  │                                                   │   │
│  │  Branchenspezifisch:                              │   │
│  │  🏥 Praxis-Software (Medistar, TurboMed, ...)   │   │
│  │  ⚖️ Anwaltssoftware (RA-Micro, Advoware, ...)  │   │
│  │  🏗️ Handwerker-Tools (Craftview, openHandwerk)  │   │
│  │  🏨 Hotel-PMS (Apaleo, Mews, Protel)            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CUSTOM CONNECTORS (vom Kunden selbst)          │   │
│  │                                                   │   │
│  │  HTTP/REST → Universeller MCP-Wrapper            │   │
│  │  "Verbinde dich mit meiner API"                   │   │
│  │  Konfiguration über Dashboard (kein Code nötig)  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

**Der HTTP-Universal-Connector — Jede API in 5 Minuten:**

Für Systeme wo kein spezifischer MCP Server existiert, bieten wir einen universellen HTTP-Connector:

```
Dashboard UI:
┌─────────────────────────────────────────┐
│  Neuen Connector erstellen              │
│                                         │
│  Name: [Meine Praxissoftware        ]  │
│  Base URL: [https://api.praxis.de   ]  │
│  Auth: [OAuth 2.0 ▼]                   │
│                                         │
│  Tools:                                 │
│  ┌─────────────────────────────────────┐│
│  │ + Tool hinzufügen                   ││
│  │                                      ││
│  │ Tool 1: "Patienten suchen"          ││
│  │ Methode: GET                         ││
│  │ Pfad: /api/v1/patients?q={query}    ││
│  │ Beschreibung: "Sucht nach Patient   ││
│  │  mit Name oder Geburtsdatum"         ││
│  │                                      ││
│  │ Tool 2: "Termin erstellen"          ││
│  │ Methode: POST                        ││
│  │ Pfad: /api/v1/appointments           ││
│  │ Body: { patient_id, date, type }    ││
│  │ Beschreibung: "Erstellt einen neuen ││
│  │  Termin für einen Patienten"         ││
│  └─────────────────────────────────────┘│
│                                         │
│  [Testen] [Speichern & Aktivieren]      │
└─────────────────────────────────────────┘
```

**Kein Code. Kein Deployment. Sofort aktiv.** Der Agent erkennt die neuen Tools automatisch und kann sie sofort nutzen.

### 3.5 MCP + A2A = Die Zukunft: Agent-zu-Agent Kommunikation

Google hat im April 2025 das **Agent2Agent (A2A) Protocol** gelauncht — und es ergänzt MCP perfekt:

```
MCP = Wie der Agent mit TOOLS spricht (vertikal)
     "Hey Gmail-Tool, zeig mir die neuen E-Mails"

A2A = Wie AGENTS miteinander sprechen (horizontal)
     "Hey Buchhaltungs-Agent, ist die Rechnung bezahlt?"
```

**Warum das für Agent One wichtig ist:**

In einer Steuerkanzlei mit 5 Mitarbeitern könnte jeder seinen eigenen Agent haben. Der Agent des Chefs fragt den Agent der Buchhalterin: "Ist die USt-VA für Müller fertig?" — ohne dass der Chef selbst nachfragen muss.

Das ist Zukunft (Phase 3D in der Roadmap), aber die Architektur muss es von Anfang an unterstützen. Deshalb bauen wir auf MCP + A2A-kompatiblen Standards.

---

## 4. n8n als Orchestration-Bridge — Das Beste aus beiden Welten

### 4.1 Warum n8n perfekt in die Architektur passt

Du kennst n8n besser als die meisten. Und die Frage "SaaS oder beim Kunden?" hat n8n bereits beantwortet: **Beides.** n8n ist self-hosted mit voller Datensouveränität ODER als Cloud mit EU-Hosting in Frankfurt.

**n8n ist NICHT der Agent. n8n ist die Brücke zwischen Agent und Kundensystemen.**

```
Agent One (LangGraph)
     │
     │ "Sende E-Mail an Müller mit Anhang"
     │
     ▼
n8n Workflow (MCP Server)
     │
     ├──▶ Gmail: E-Mail senden
     ├──▶ Google Drive: Anhang runterladen
     ├──▶ DATEV: Buchung erstellen
     └──▶ Slack: Team benachrichtigen
```

**Warum nicht ALLES in LangGraph?** Weil LangGraph brillant im Reasoning ist, aber n8n brillant im Connecting ist. 1.200+ vorgefertigte Integrationen. Visueller Workflow-Builder. Error Handling. Retry-Logic. Queue Mode für Skalierung. Das alles selbst zu bauen wäre Wahnsinn.

### 4.2 n8n als MCP Server

Der Clou: **n8n Workflows WERDEN zu MCP Tools** die der Agent nutzen kann:

```python
# n8n-mcp-bridge.py
# Jeder n8n Workflow wird automatisch als MCP Tool exponiert

@server.tool()
async def trigger_n8n_workflow(
    workflow_id: str,
    input_data: dict
) -> list[TextContent]:
    """Triggert einen n8n Workflow und gibt das Ergebnis zurück"""
    result = await n8n_api.trigger_webhook(
        workflow_id=workflow_id,
        data=input_data
    )
    return [TextContent(type="text", text=json.dumps(result))]
```

Das bedeutet: Jeder n8n Workflow den du oder deine Kunden bauen, wird **automatisch ein Tool das der Agent nutzen kann**. Deine n8n-Expertise wird zum direkten Wettbewerbsvorteil.

### 4.3 Das n8n Deployment pro Modell

| Deployment | n8n Location | Datenfluss |
|-----------|-------------|-----------|
| **Modell A** (SaaS) | n8n Cloud (Frankfurt) oder unsere n8n-Instanz | Agent → n8n Cloud → Kundensysteme via OAuth |
| **Modell B** (Hybrid) | n8n Self-Hosted beim Kunden | Agent → API → Kunden-n8n → Kundensysteme (lokal) |
| **Modell C** (On-Prem) | n8n Self-Hosted beim Kunden | Alles lokal, keine externe Verbindung nötig |

---

## 5. Der Datenfluss in der Praxis — Ein komplettes Beispiel

### Szenario: Steuerberater Schmidt (Modell B: Hybrid)

**07:00 — Morgen-Briefing Cron Job feuert**

```
[Agent One Cloud — Hetzner]
LangGraph Cron: "Erstelle Morgen-Briefing für Tenant #42"
     │
     ▼
[Agent One Cloud]
Supervisor Agent: "Ich brauche: Neue E-Mails, heutige Termine, offene Fristen"
     │
     ▼ MCP Call (verschlüsselt, über API Gateway)
     │
[Schmidts VPS — Kunden-Infrastruktur]
MCP Gateway empfängt Anfrage, prüft Auth + Permissions
     │
     ├──▶ Gmail MCP Server (lokal):
     │    Liest 12 neue E-Mails aus Schmidts Gmail
     │    Sendet ZUSAMMENFASSUNG zurück (nicht Volltext!)
     │    "3 dringend, 7 Routine, 2 Spam"
     │
     ├──▶ Calendar MCP Server (lokal):
     │    "Heute: 10:00 Weber, 14:00 Koch, 16:00 frei"
     │
     └──▶ Fristen MCP Server (Graphiti-Query lokal):
          "Frist Mandant Schulz in 2 Tagen!"
     │
     ▼ Zusammengefasste Daten zurück (KEINE Rohdaten!)
     │
[Agent One Cloud]
LangGraph generiert Briefing-Text:
"Guten Morgen! 12 neue E-Mails (3 dringend)..."
     │
     ▼
[Expo Push Service]
Push Notification an Schmidts Handy:
"☀️ Dein Morgen-Briefing ist fertig"
```

**Beachte was NICHT passiert ist:**
- ✗ Kein E-Mail-Volltext hat die Cloud verlassen
- ✗ Keine Mandantennamen wurden in der Cloud gespeichert
- ✗ Keine DATEV-Daten haben den Kunden-Server verlassen
- ✓ Nur zusammengefasste, anonymisierte Metadaten für das Reasoning

### 07:15 — Schmidt prüft und genehmigt

```
[Schmidts Handy — Expo App]
Öffnet Morgen-Briefing → Sieht 7 vorbereitete E-Mail-Antworten
Wischt rechts auf 5 Antworten → Genehmigt
Tippt auf 1 Antwort → Bearbeitet Formulierung
Tippt auf 1 Antwort → Ablehnt (falsch kategorisiert)
     │
     ▼ Genehmigungen via API
     │
[Agent One Cloud]
Trust Score Update: E-Mail-Routine jetzt 89% (war 87%)
     │
     ▼ Sende-Befehl an Kunden-MCP
     │
[Schmidts VPS]
Gmail MCP Server: 5 E-Mails gesendet + 1 bearbeitete
     │
     ▼ Lokaler Graphiti Update
     │
Graphiti lernt: "E-Mail an Weber wurde bearbeitet:
Schmidt bevorzugt 'Mit freundlichen Grüßen'
statt 'Beste Grüße' bei Finanzamt-Korrespondenz"
```

---

## 6. Security Layer für den Datenfluss

### 6.1 Verschlüsselung auf jeder Ebene

```
App ←──TLS 1.3──▶ API Gateway ←──mTLS──▶ Kunden-MCP
                                              │
                                    ┌─────────┴──────────┐
                                    │ Envelope Encryption │
                                    │ Tenant-Key in Vault │
                                    │ Data-Key pro Objekt │
                                    └────────────────────┘
```

| Schicht | Verschlüsselung | Was es schützt |
|---------|-----------------|----------------|
| **Transport** | TLS 1.3 überall | Daten in Transit |
| **API Gateway** | mTLS (mutual TLS) | Nur autorisierte Kunden-Server können sich verbinden |
| **Storage** | AES-256 Envelope Encryption | Jeder Tenant hat eigenen Key in HashiCorp Vault |
| **Knowledge Graph** | Graphiti group_id + Encryption | Tenant-Isolation auf Datenebene |
| **App** | Biometrische Auth + Secure Storage | Gerätezugang |

### 6.2 OAuth 2.0 Token-Management

Der Agent braucht Zugang zu Gmail, Kalender, CRM etc. Das läuft über OAuth 2.0 — der Kunde autorisiert den Zugang einmal, der Token wird sicher gespeichert:

```
Kunde klickt "Gmail verbinden" im Dashboard
     │
     ▼
OAuth 2.0 Authorization Flow
(Redirect zu Google, Kunde stimmt zu)
     │
     ▼
Access Token + Refresh Token empfangen
     │
     ▼
Token verschlüsselt in HashiCorp Vault gespeichert
(NICHT in der Datenbank!)
     │
     ▼
MCP Server nutzt Token für API-Zugriff
Automatische Token-Erneuerung bei Ablauf
```

**Kritisch:** Tokens werden NIEMALS in Logs geschrieben, NIEMALS in Prompts an LLMs gesendet, NIEMALS außerhalb von Vault gespeichert.

### 6.3 Das Principle of Least Privilege für MCP Tools

Jeder MCP Connector bekommt nur die Rechte die er braucht:

```python
class MCPPermissions:
    """Deklarative Permissions pro MCP Server"""
    
    GMAIL_PERMISSIONS = {
        "read": True,       # E-Mails lesen
        "send": True,       # E-Mails senden (mit Trust/Approval)
        "delete": False,    # NIEMALS löschen
        "manage_labels": True,  # Labels verwalten
        "manage_filters": False,  # Keine Filter ändern
    }
    
    CALENDAR_PERMISSIONS = {
        "read": True,
        "create": True,      # Termine erstellen (mit Trust/Approval)
        "delete": False,     # NIEMALS löschen
        "modify_others": False,  # Keine fremden Termine ändern
    }
    
    DATEV_PERMISSIONS = {
        "read": True,        # Daten lesen
        "create_buchung": True,  # Buchungen erstellen (IMMER Review!)
        "delete": False,     # NIEMALS
        "export": False,     # NIEMALS Daten exportieren
    }
```

---

## 7. Skalierung — Von 1 bis 10.000 Kunden

### 7.1 Architektur-Skalierung pro Phase

**Phase 1: 1-50 Kunden (Modell A)**
```
Single Hetzner Server (CX41 — 16GB RAM, 4 vCPU)
├── Docker Compose
├── LangGraph + FastAPI
├── Graphiti + FalkorDB
├── PostgreSQL
├── Redis
└── ~€30/Monat Serverkosten
```

**Phase 2: 50-500 Kunden**
```
Hetzner Cloud — 3 Server
├── Server 1: LangGraph + FastAPI (Application)
├── Server 2: Graphiti + FalkorDB + PostgreSQL (Data)
├── Server 3: Redis + LiteLLM + Langfuse (Support Services)
└── ~€150/Monat Serverkosten
```

**Phase 3: 500-5.000 Kunden**
```
Kubernetes (k3s) auf Hetzner Cloud
├── Application Pods (horizontal skalierbar)
├── LangGraph Worker Pods (für Cron-Jobs und Background Tasks)
├── FalkorDB Cluster (Replicas für Lesegeschwindigkeit)
├── PostgreSQL mit pgBouncer (Connection Pooling)
├── Redis Cluster (Cache + Pub/Sub)
└── ~€500-2.000/Monat Serverkosten
```

### 7.2 Kosten pro Kunde (Modell A, SaaS)

| Kostenfaktor | Pro Kunde/Monat | Bei 100 Kunden | Bei 1.000 Kunden |
|-------------|----------------|-----------------|-------------------|
| LLM-API (mit Caching+Routing) | ~€15-30 | €1.500-3.000 | €15.000-30.000 |
| Infrastruktur anteilig | ~€1-3 | €100-300 | €500-2.000 |
| Expo Push Service | ~€0,50 | €50 | €500 |
| **Gesamtkosten** | **~€17-34** | **€1.650-3.350** | **€16.000-32.500** |
| **Preis (€249/Mo)** | €249 | €24.900 | €249.000 |
| **Bruttomarge** | **~87-93%** | | |

Die Marge ist brutal gut weil die teuerste Komponente (LLM-APIs) durch das Caching-System aus Level 2 um 75-95% reduziert wird.

---

## 8. Die Implementierungs-Roadmap Level 4

### Phase 4A — Data Architecture Foundation (parallel zu Level 3)

| Deliverable | Details |
|-------------|---------|
| **Zero-Data-Retention Policy** | Technische + juristische Umsetzung, AVV-Templates |
| **MCP Gateway** | OAuth 2.1, Rate Limiting, PII-Filter, Audit Logging |
| **Offizielle MCP Connectors** | Gmail, Google Calendar, HubSpot (die ersten 3) |
| **n8n MCP Bridge** | n8n Workflows als MCP Tools für den Agent |
| **Token Management** | HashiCorp Vault Integration für OAuth Tokens |
| **Multi-Tenant Data Isolation** | Graphiti group_id + PostgreSQL RLS + Encryption |

### Phase 4B — Hybrid Deployment

| Deliverable | Details |
|-------------|---------|
| **Kunden-Docker-Stack** | Vorkonfiguriertes Image für Modell B |
| **Anonymisierungs-Pipeline** | Presidio PII-Filter für Cloud-Reasoning-Requests |
| **mTLS Agent-Gateway** | Sichere Kommunikation zwischen Cloud und Kunden-Server |
| **Auto-Update System** | Kunden-Stack updated sich automatisch bei neuen Releases |
| **Setup-Wizard** | Dashboard-UI für One-Click Hybrid Setup |

### Phase 4C — Connector Marketplace

| Deliverable | Details |
|-------------|---------|
| **HTTP Universal Connector** | No-Code Konfiguration im Dashboard für beliebige APIs |
| **Connector SDK** | Python/TypeScript SDK für Community-Entwickler |
| **Marketplace UI** | Browse, Install, Configure im Dashboard |
| **DATEV Connector** | Offizieller Connector für Steuerberater |
| **Branchenspezifische Connectors** | Lexoffice, sevDesk, RA-Micro (basierend auf Kundennachfrage) |
| **A2A-Readiness** | Architektur-Vorbereitung für Agent-zu-Agent Kommunikation |

---

## 9. Die Gesamt-Architektur — Alle vier Level vereint

```
═══════════════════════════════════════════════════════════════════
                        LEVEL 1: FUNDAMENT
          Next.js + FastAPI + LangGraph + Graphiti + FalkorDB
═══════════════════════════════════════════════════════════════════
                              │
═══════════════════════════════════════════════════════════════════
                    LEVEL 2: SECURITY & INTELLIGENCE
          DSGVO + Multi-Tenant + Caching + RouteLLM + Dashboard
═══════════════════════════════════════════════════════════════════
                              │
═══════════════════════════════════════════════════════════════════
                   LEVEL 3: AMBIENT AGENT + APP
       Proaktivität + Progressive Autonomie + Expo App + Voice
═══════════════════════════════════════════════════════════════════
                              │
═══════════════════════════════════════════════════════════════════
              LEVEL 4: DATA SOVEREIGNTY & CONNECTORS
     Zero-Data-Retention + Hybrid Deploy + MCP Gateway + n8n Bridge
═══════════════════════════════════════════════════════════════════

Zusammen ergibt das:

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   Ein proaktiver KI-Mitarbeiter der:                │
    │                                                      │
    │   ✓ 24/7 im Hintergrund arbeitet (Ambient Agent)   │
    │   ✓ Sich Autonomie verdient (Trust Scores)          │
    │   ✓ Per App steuerbar ist (Expo)                    │
    │   ✓ DSGVO-konform ist (by Design)                   │
    │   ✓ Keine Kundendaten speichert (Zero Retention)    │
    │   ✓ Jedes Tool anbinden kann (MCP + n8n)            │
    │   ✓ 3 Deployment-Modelle bietet (SaaS/Hybrid/OnPrem)│
    │   ✓ Sich mit jedem System verbindet (1000+ Connector)│
    │   ✓ 75-95% günstiger als Konkurrenz ist (Caching)  │
    │   ✓ Temporal Memory hat das niemand sonst bietet    │
    │                                                      │
    │   Für den deutschen Mittelstand.                     │
    │   Von HR Code Labs.                                  │
    │                                                      │
    └──────────────────────────────────────────────────────┘
```

---

## 10. Die Kern-Erkenntnis von Level 4

**Level 3 fragte "Was kann der Agent?". Level 4 beantwortet "Wohin fließen die Daten?"**

Und die Antwort ist radikal einfach: **Nirgendwohin. Die Daten bleiben beim Kunden.**

Der Agent ist reine Intelligenz — ein Gehirn ohne Aktenschrank. Er denkt, entscheidet, handelt — aber die Akten, E-Mails, Dokumente und Mandantendaten bleiben dort wo sie hingehören: In den Systemen des Kunden.

**Die drei Innovations-Säulen von Level 4:**

1. **Zero-Data-Retention** — Agent verarbeitet, speichert nicht. Knowledge Graph enthält nur abstrahierte Fakten, keine Rohdaten. PII wird vor Speicherung gefiltert. Das ist das stärkste DSGVO-Argument am Markt.

2. **Drei Deployment-Modelle** — SaaS für die Masse (80%), Hybrid für §203-Berufe (Steuerberater, Anwälte, Ärzte), On-Premise für Enterprise. Jeder Kunde wählt sein Comfort-Level. Kein Zwang zur Cloud.

3. **MCP + n8n als Universal-Connector** — Jede API in 30 Minuten anbindbar. 1.200+ n8n-Integrationen sofort als Agent-Tools nutzbar. HTTP-Universal-Connector für alles andere — kein Code nötig. Deine n8n-Expertise wird zum unfairen Wettbewerbsvorteil.

**Das ist die vollständige Architektur von Agent One. Vier Level. Von der Datenbank bis zur Push-Notification. Vom Security-Layer bis zum Connector-Marketplace. Vom reaktiven Chatbot zum proaktiven KI-Mitarbeiter der keine Kundendaten speichert.**

**Kein Wettbewerber bietet das in dieser Kombination: Temporal Memory + DSGVO-by-Design + Zero-Data-Retention + Ambient Agent + Native App + Universal Connectors + Drei Deployment-Modelle.**

Und alles gebaut auf Open-Source-Technologien, gehostet in Deutschland, designed für den deutschen Mittelstand.

---

*Quellen: Anthropic MCP Specification (Nov 2025), Anthropic Code Execution with MCP Blog, Google A2A Protocol Announcement (Apr 2025), IBM A2A Documentation, Proofpoint MCP Security Analysis, Thoughtworks MCP Impact 2025, Agent Interoperability Protocols Survey (arXiv), Allganize Cloud vs On-Prem Guide, McKinsey Agentic AI Advantage, n8n Self-Hosting Documentation, Koyeb A2A vs MCP Analysis, Descope MCP Architecture Guide*
