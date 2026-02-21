# AGENT ONE — Interne Projektbeschreibung & Strategie

**HR Code Labs GbR** | Oliver Hees & Alina Rosenbusch
**Version:** 1.0 | **Datum:** 13. Februar 2026
**Klassifikation:** Intern / Vertraulich

---

## EXECUTIVE SUMMARY

Agent One ist ein proaktiver KI-Mitarbeiter für den deutschen Mittelstand — der erste Agent der Welt, der sich selbst verbessert, mögliche Zukünfte simuliert und aktiv auf das Wohlbefinden seines Nutzers achtet.

Während der globale AI-Agent-Markt von $7,84 Mrd. (2025) auf $52,62 Mrd. (2030) explodiert (CAGR 46,3%), investiert der deutsche Mittelstand rund 30% weniger in KI als der Gesamtmarkt. Nicht aus Desinteresse — 82% der Unternehmen planen Budget-Erhöhungen — sondern weil kein Produkt existiert, das DSGVO-Konformität, §203-Berufsgeheimnis und deutsche Serverstandorte so ernst nimmt, dass ein Steuerberater, Anwalt oder Arzt es bedenkenlos einsetzen kann.

Diese Lücke ist unsere Chance. Agent One schließt sie — nicht mit einem weiteren Chatbot, sondern mit einem digitalen Partner, der 24/7 im Hintergrund arbeitet, sich mit jeder Interaktion verbessert, und dabei aufpasst, dass sein Nutzer nicht ausbrennt.

**Kernzahlen:**

- **Zielmarkt:** ~148.000 Berufsgeheimnisträger-Kanzleien/Praxen in Deutschland (53.800 Steuerberaterpraxen + 47.300 Anwaltskanzleien + ~47.000 Arztpraxen mit relevanter Größe)
- **Serviceable Obtainable Market (SOM, Jahr 1):** 100-200 Kunden → €300.000-600.000 ARR
- **Ziel Jahr 3:** 1.000-2.000 Kunden → €3-6 Mio. ARR
- **Brutto-Marge:** 87-93% (SaaS-typisch, durch Caching/Routing optimiert)
- **Investitionsbedarf:** Minimal — Bootstrapped, kein Venture Capital nötig
- **Team:** Zwei Gründer + Claude Code + Community als Multiplikator

---

## 1. WARUM JETZT — DIE MARKTCHANCE

### 1.1 Der deutsche KI-Markt explodiert — aber der Mittelstand hinkt hinterher

Der deutsche KI-Markt wächst von €10 Mrd. (2025) auf €32 Mrd. (2030). Gleichzeitig zeigen die Zahlen eine massive Adoptionslücke:

- Laut Bitkom nutzen nur 20% der deutschen Unternehmen aktiv KI (Stand Feb 2025, +5pp vs. 2024)
- Die OECD bestätigt: KI-Adoption bei KMUs liegt systematisch unter der von Großunternehmen — in allen G7-Ländern
- 75% der Steuerberaterkanzleien müssen Geschäft einschränken wegen Fachkräftemangel (ifo Institut 2023)
- Der Mittelstand investiert ~30% weniger in KI als der Gesamtmarkt (Horvath-Studie, Jan 2026)

Der Grund ist NICHT fehlendes Interesse. 82% planen Budget-Erhöhungen. Die Blocker sind:

1. **Datenschutz-Angst:** "Wo liegen meine Mandantendaten?" — Eine Frage die kein US-Anbieter befriedigend beantworten kann
2. **Regulatorische Unsicherheit:** DSGVO + EU AI Act + BSI Grundschutz++ → Komplexitätsschock
3. **Fehlende Branchenlösung:** ChatGPT ist generisch. Salesforce Agentforce ist Enterprise. Nichts ist für eine Steuerkanzlei mit 5-50 Mitarbeitern gebaut
4. **Berufsspezifische Hürden:** §203 StGB (Berufsgeheimnis) macht Cloud-Lösungen für Steuerberater, Anwälte und Ärzte zu einem rechtlichen Minenfeld

### 1.2 Die Wettbewerbslandschaft — Und warum niemand dieses Problem löst

**US-Hyperscaler (OpenAI Frontier, Anthropic Cowork, Salesforce Agentforce):**
Alle bauen Enterprise-Agenten — aber für Fortune-500-Unternehmen. Kein Fokus auf deutsche Compliance, deutsche Sprache, deutsches Berufsrecht. OpenAI Frontier (gerade erst gelauncht, Feb 2026) bedroht traditionelle SaaS-Anbieter, aber ein Steuerberater in Buxtehude wird kein "Agentic Enterprise License Agreement" für $250K/Jahr abschließen.

**Deutsche Legal-Tech / Tax-Tech:**
DATEV dominiert Steuerberater-Software, ist aber kein KI-Agent — sondern ein Buchhaltungssystem. Legal-Tech-Startups (Taxy.io, Accounto) fokussieren auf einzelne Funktionen (Belegerfassung, Mandatsmanagement), nicht auf einen ganzheitlichen KI-Mitarbeiter.

**No-Code/Low-Code Agent Builder (n8n, Make, StackAI):**
Gute Werkzeuge — aber Werkzeuge, keine Produkte. Ein Steuerberater will keinen Workflow bauen, er will morgens sein Handy aufmachen und sehen, was sein Agent über Nacht erledigt hat.

**Die Lücke:**
Kein Produkt am Markt kombiniert: Proaktiven KI-Agent + Deutsche Compliance (DSGVO/§203) + Branchenspezifisch + Mobile App + Selbstlernend + Bezahlbar für KMUs. Agent One besetzt exakt diese Lücke.

### 1.3 Timing ist alles

Gartner prognostiziert: Bis Ende 2026 werden 40% aller Enterprise-Anwendungen task-spezifische KI-Agenten integriert haben (von <5% Anfang 2025). Deloitte sagt voraus, dass 75% der Unternehmen in Agentic AI investieren werden. Das Fenster ist JETZT offen:

- Die Technologie ist reif: LangGraph, Graphiti, MCP sind alle production-ready seit 2025
- Die Nachfrage ist da: 82% planen KI-Budgets zu erhöhen
- Die Konkurrenz ist nicht da: Niemand baut spezifisch für deutsche §203-Berufe
- First-Mover-Vorteil + Wechselkosten: Ein Agent der 12 Monate gelernt hat, wird nicht einfach ersetzt

---

## 2. DIE VISION — WAS AGENT ONE IST

### 2.1 Nicht ein Tool. Ein digitaler Partner.

Jedes KI-Unternehmen verspricht "mehr Produktivität". Agent One verspricht etwas anderes:

> **"Wir sorgen dafür, dass du langfristig erfolgreich UND gesund bleibst. Dein Agent arbeitet FÜR dich — und passt AUF dich auf."**

Das ist keine Marketing-Floskel. Das ist eine Architekturentscheidung. Agent One hat drei Säulen die kein anderer Agent hat:

1. **Selbstevolution:** Der Agent wird jeden Tag besser, ohne dass jemand ihn manuell updaten muss. Nach 12 Monaten kennt er die Kanzlei besser als jeder neue Mitarbeiter.

2. **Weltmodell:** Der Agent simuliert "Was passiert wenn..." — bevor er handelt. "Wenn wir Mandant Schulz nicht heute an seine USt-VA erinnern, ist die Wahrscheinlichkeit 34%, dass die Unterlagen zu spät kommen."

3. **Guardian Angel:** Der Agent überwacht das Wohlbefinden seines Nutzers. "Du arbeitest seit 14 Tagen ohne freien Tag. Dein Wellbeing Score ist auf 4/10 gesunken. Soll ich diese Woche mehr automatisch erledigen?"

### 2.2 Der Alltag mit Agent One

**07:00 — Push-Notification:**
"☀️ Guten Morgen! Dein Agent-Briefing ist fertig."

**Das Briefing:**
"Kurz und knapp heute — du hattest eine lange Woche:
- 3 neue Mandanten-Mails → 2 automatisch beantwortet (Trust Score >90%), 1 braucht deine Freigabe
- USt-VA Schulz: Frist in 5 Tagen → Mein Weltmodell sagt: 72% Chance dass Unterlagen zu spät kommen. Erinnerung JETZT senden?
- Finanzamt-Bescheid Weber: Einspruchsfrist läuft in 8 Tagen → Entwurf vorbereitet
- 💚 Du hast diese Woche 12,5 Stunden durch mich gespart. Vorschlag: Freitagnachmittag frei?"

**Auf dem Handy:**
Ein Swipe nach rechts = Genehmigt. Ein Tap = Details ansehen. Ein Sprachbefehl = "Hey Agent, ruf Müller zurück wegen dem Bescheid."

**Im Hintergrund:**
Der Agent hat über Nacht seine eigenen Prompts verbessert (gestern hat der Nutzer eine E-Mail ans Finanzamt editiert → Agent hat gelernt: "Immer Aktenzeichen UND Steuernummer angeben"). Ab heute macht er das automatisch.

### 2.3 Die fünf Architektur-Level

Agent One ist in fünf aufeinander aufbauenden Leveln konzipiert:

**Level 1 — Das Fundament:**
LangGraph Multi-Agent-System + Graphiti temporaler Knowledge Graph + FalkorDB (Sub-10ms Queries). Der Agent hat ein Gedächtnis das nicht nur speichert WAS passiert ist, sondern WANN Fakten gültig und ungültig wurden. Kein anderer Agent hat das.

**Level 2 — Die Festung:**
DSGVO-by-Design, Multi-Tenant mit Row-Level-Security, 4-Schichten-Datenisolation, HashiCorp Vault für Secrets, Microsoft Presidio für PII-Filterung, Audit Trail (Write-Once), BSI Grundschutz++. Intelligentes Caching (75-95% Kostensenkung), RouteLLM (95% GPT-4-Qualität bei 14-26% der Kosten). Next.js Dashboard mit White-Labeling.

**Level 3 — Der Ambient Agent:**
Paradigmenwechsel von "Agent wartet auf Befehle" zu "Agent handelt proaktiv". Morgen-Briefing, Event-Driven Triggers (Gmail, Kalender, Telefon), progressives Trust-Score-System (Agent verdient sich Autonomie durch nachweisbare Zuverlässigkeit). Expo Mobile App mit Voice (Deepgram STT + ElevenLabs TTS, ~600ms Latenz), Push Notifications, Biometric Auth, Swipe-to-Approve. On-Device AI (Llama 3.2 1B) für Offline-Funktionen.

**Level 4 — Zero-Data-Architektur:**
Drei Deployment-Modelle: Full Cloud SaaS (80% der Kunden), Hybrid (Daten beim Kunden, Intelligenz bei uns — für §203-Berufe), Full On-Premise (Kliniken, Behörden). MCP Gateway als universelle Connector-Schicht mit 1.200+ Integrationen via n8n Bridge. HTTP Universal Connector (jede REST API in 5 Min via UI). OAuth Token Management in Vault.

**Level 5 — Der Lebendige Agent:**
Selbstevolution (Nightly Reflection, Skill Library, Prompt Evolution mit A/B-Testing), Business World Model (Counterfactual Reasoning auf Graphiti-Temporaldaten), Guardian Angel (Wellbeing Score aus 5 Signalen, Adaptive Load Balancer, Kalender-Schutz). Safety Rails: Agent darf nur Prompts ändern, niemals Code. Immutable Core Rules. Auto-Rollback bei Regression.

---

## 3. ZIELGRUPPEN & GO-TO-MARKET

### 3.1 Primäre Zielgruppe: Berufsgeheimnisträger nach §203 StGB

| Segment | Anzahl in DE | Ø Kanzleigröße | Pain Points | Agent One Fit |
|---------|-------------|---------------|-------------|--------------|
| **Steuerberater** | ~53.800 Praxen (104.845 Kammermitglieder) | 2-15 MA | Fachkräftemangel (75% eingeschränkt), Fristen-Management, Digitalisierungsdruck | ★★★★★ |
| **Rechtsanwälte** | ~47.300 Kanzleien (davon ~42.100 ohne Notariat) | 1-10 MA | Fristen (Verjährung!), Mandantenkommunikation, Research | ★★★★☆ |
| **Ärzte / Therapeuten** | ~47.000 Praxen mit >2 MA | 2-20 MA | Terminmanagement, Patientenkommunikation, Abrechnung | ★★★☆☆ |

**Warum Steuerberater zuerst?**
- Höchste Schmerzpunkte (Fachkräftemangel + Fristendruck + Digitalisierungszwang durch DATEV)
- Oliver hat direkten Zugang (Kunde Benjamin Arras, Netzwerk über Community)
- Gut abgrenzbarer Markt mit klaren Branchenverbänden (Bundessteuerberaterkammer)
- Recurring Revenue: Mandatsverhältnisse sind langfristig → Agent wird immer wertvoller
- Steuerberater haben Budget (Ø Jahresüberschuss ~€191.000 pro Inhaber)

### 3.2 Sekundäre Zielgruppen

| Segment | Warum | Wann |
|---------|-------|------|
| **Coaches & Berater** | Kein §203, aber Terminmanagement + Kommunikation. Günstigerer Einstieg (SaaS-Modell) | Ab Launch |
| **Freelancer / Solo-Unternehmer** | Kleinster Pain, aber größte Masse. Community-Multiplikator | Ab Launch |
| **Handwerksbetriebe** | Auftragsmanagement, Kundenkommunikation, Rechnungsstellung | Jahr 2 |
| **Agenturen** | Projektmanagement, Kundenkommunikation, Reporting | Jahr 2 |

### 3.3 Go-to-Market-Strategie

**Phase 1 (Monate 1-6): Community + Content + Erstskunden**

- YouTube-Kanal (~2.700 Subscriber) als Demo-Plattform: "Ich baue den Agenten live — schaut zu"
- TikTok (~3.000 Follower) für Viralität: Kurze Demos die zeigen was Agent One kann
- AI Automation Engineers Community (200+ Mitglieder) als Early Adopters + Feedback-Loop
- Benjamin Arras als Pilot-Kunde und Referenz
- 5-10 Beta-Kunden (Steuerberater aus Netzwerk) mit Rabatt + intensiver Betreuung
- Content: "Wie ein KI-Agent meinen Steuerberater-Alltag verändert hat" — aus Kundensicht

**Phase 2 (Monate 6-12): Referenzen + Partnerschaften**

- Case Studies von Beta-Kunden ("Agent hat mir 12h/Woche gespart")
- Partnerschaften mit Steuerberater-Verbänden / IHK
- Kooperation mit DATEV-Beratern (Agent One ALS Ergänzung zu DATEV, nicht Ersatz)
- Teilnahme an Steuerberater-Kongressen / -Messen
- Webinare: "DSGVO-konformer KI-Agent für Steuerkanzleien — so geht's"

**Phase 3 (Jahr 2+): Skalierung**

- White-Label für Steuerberater-Netzwerke (ETL, DATEV-Community)
- Connector Marketplace: Community baut branchenspezifische Connectors
- Internationalisierung: Österreich, Schweiz (gleiches Recht, gleiche Sprache)
- Content-Maschine: "AI Automation Engineers" Community als Multiplikator

### 3.4 Vertriebskanäle

| Kanal | Kosten | Erwartete Conversion | Priorität |
|-------|--------|---------------------|-----------|
| **Eigener Content** (YouTube, TikTok, Blog) | Nur Zeit | Langsam aber nachhaltig | ★★★★★ |
| **Community** (AI Automation Engineers) | Bereits aufgebaut | Hoch (Vertrauen vorhanden) | ★★★★★ |
| **Referral** (Zufriedene Kunden empfehlen) | €0 | Höchste Conversion Rate | ★★★★★ |
| **Steuerberater-Verbände / IHK** | Event-Kosten | Mittel, aber vertrauenswürdig | ★★★★☆ |
| **LinkedIn Outbound** | Minimal | Mittel | ★★★☆☆ |
| **Google Ads** | €€€ | Variabel | ★★☆☆☆ (erst ab Profitabilität) |

---

## 4. GESCHÄFTSMODELL & FINANZEN

### 4.1 Pricing

| Tier | Preis/Mo | Zielgruppe | Was ist drin |
|------|---------|-----------|-------------|
| **Starter** | €149 | Freelancer, Coaches, Solo-Berater | 1 Nutzer, Basis-Agents (E-Mail, Kalender), SaaS-Modell, 500 Agent-Aktionen/Mo |
| **Professional** | €299 | Kanzleien 2-10 MA, Berater | 5 Nutzer, Alle Agents, Voice, App, 2.000 Aktionen/Mo, White-Label |
| **Enterprise** | €499 | §203-Berufe, größere Kanzleien | 15 Nutzer, Hybrid-Deployment, Telefon-Agent, 5.000 Aktionen/Mo, DSGVO-Audit-Export |
| **Level 5 Premium** | +€200 | Alle Tiers | Selbstevolution, Weltmodell, Guardian Angel, Wellbeing Dashboard |
| **On-Premise** | €999+ | Kliniken, Behörden | Full On-Premise, eigene Server, SLA, dedizierter Support |

**Zusätzliche Revenue Streams:**

- **Connector Marketplace:** 20% Revenue Share auf Premium-Connectors (DATEV, HubSpot, etc.)
- **Setup-Fee für Hybrid/On-Premise:** €500-2.500 einmalig
- **Consulting / Custom Development:** €150/h für spezielle Anpassungen
- **White-Label-Lizenz:** €999/Mo für Steuerberater-Netzwerke die Agent One unter eigenem Brand anbieten

### 4.2 Unit Economics

```
Revenue pro Kunde (Durchschnitt):           €299/Mo (Professional-Tier)

Kosten pro Kunde:
├── LLM API (mit Caching + Routing):        €15-30/Mo
├── Infrastruktur (proportional):            €1-3/Mo
├── Expo Push Service:                       €0.50/Mo
├── Voice APIs (Deepgram + ElevenLabs):      €3-8/Mo
└── Support (anteilig):                      €5-10/Mo
                                             ─────────
Kosten gesamt:                               €25-52/Mo
Brutto-Marge:                                83-92%
Customer Acquisition Cost (CAC):             ~€200 (Content + Referral)
Payback Period:                              <1 Monat
Lifetime Value (LTV, 24 Mo Ø):              ~€7.176
LTV/CAC Ratio:                               ~36x
```

Die Unit Economics sind außergewöhnlich gut, weil:
1. **Content-Marketing** statt Paid Ads → niedriger CAC
2. **Caching + RouteLLM** → 75-95% LLM-Kostenersparnis
3. **Self-Service Onboarding** → minimale Support-Kosten
4. **Selbstevolution** → Agent wird besser ohne Entwickleraufwand
5. **Hohe Switching Costs** → Agent hat gelerntes Wissen (12 Mo. Lernkurve)

### 4.3 Finanzprognose (Konservativ)

| Metrik | Mo 6 | Mo 12 | Mo 24 | Mo 36 |
|--------|------|-------|-------|-------|
| **Kunden** | 20 | 80 | 400 | 1.200 |
| **MRR** | €4.000 | €20.000 | €108.000 | €360.000 |
| **ARR** | €48.000 | €240.000 | €1.296.000 | €4.320.000 |
| **Brutto-Marge** | 85% | 88% | 90% | 92% |
| **Churn/Mo** | 5% | 3% | 2% | 1.5% |
| **Team** | 2 (Gründer) | 2-3 | 4-6 | 8-12 |
| **Server-Kosten** | €100 | €300 | €2.000 | €8.000 |

**Annahmen:**
- Durchschnittlicher Kundenpreis: ~€270/Mo (Mix aus Starter + Professional)
- Churn sinkt über Zeit weil Selbstevolution Switching Costs erhöht
- Kein VC-Funding → organisches Wachstum, Profitabilität ab Monat ~8
- Marketing-Budget steigt erst wenn Product-Market-Fit bestätigt ist

### 4.4 Break-Even-Analyse

```
Fixkosten (Monat):
├── Server (Hetzner):                        €100-300
├── APIs (Langfuse, Vault, etc.):            €50-100
├── Tools (GitHub, Expo, etc.):              €50-100
├── Oliver Gehalt (ab Vollzeit, März 2026):  €3.000-5.000
└── Alina Vergütung:                         Variable
                                             ─────────
Fixkosten gesamt:                            ~€3.500-5.500/Mo

Break-Even bei €270 Ø-Preis und 90% Marge:
€5.000 / (€270 × 0.90) = ~21 Kunden

→ Break-Even bei ~21 zahlenden Kunden
```

Das ist erreichbar innerhalb von 3-6 Monaten nach Launch.

---

## 5. TECHNISCHE DIFFERENZIERUNG — WARUM WIR GEWINNEN

### 5.1 Der technische Burggraben

Agent One hat sieben technische Differenzierungen die einzeln stark und zusammen uneinholbar sind:

**1. Temporaler Knowledge Graph (Graphiti + FalkorDB)**
Kein anderer Agent am Markt hat ein Gedächtnis das trackt WANN Fakten gültig und ungültig werden. Graphiti übertrifft MemGPT im Deep Memory Retrieval Benchmark (94,8% vs. 93,4%). Das bedeutet: Agent One weiß nicht nur "Mandant Müller hat Telefonnummer X" — sondern "Müller hatte bis März 2025 Nummer X, seitdem Nummer Y". Das ermöglicht das Weltmodell (Level 5): Muster über Zeit erkennen und Zukünfte simulieren.

**2. Progressive Autonomie (Trust Score System)**
Statt starrer Berechtigungen verdient sich der Agent Autonomie durch nachweisbare Zuverlässigkeit. Nach 50 erfolgreich genehmigten E-Mails an bestehende Mandanten (Trust Score >85%) sendet er sie automatisch. Neue Aktionstypen beginnen immer bei 0%. Das gibt Nutzern Kontrolle UND spart ihnen über Zeit immer mehr Arbeit.

**3. Zero-Data-Retention**
Agent One speichert KEINE Kundendaten. Er LIEST Daten aus Kundensystemen (via MCP), DENKT, und SCHREIBT zurück. Im Knowledge Graph landen nur abstrahierte Fakten ("Mandant bevorzugt informellen Ton"), niemals Originaldaten. Für §203-Berufe: Hybrid-Modell wo die Datenbank beim Kunden steht.

**4. Selbstevolution (Level 5)**
Der Agent analysiert jede Nacht um 02:00 seine eigene Performance: Was wurde genehmigt, abgelehnt, editiert? Aus Edits extrahiert er Lektionen und verbessert seine eigenen Prompts. Mit A/B-Testing und Auto-Rollback bei Regression. Ergebnis: Monat 1 = 67% Auto-Approved. Monat 12 = 97% Auto-Approved. Ohne dass ein Entwickler eingreift.

**5. Guardian Angel (Level 5)**
Kein anderer Agent kümmert sich um das Wohlbefinden seines Nutzers. Agent One trackt Arbeitszeiten, Entscheidungslast, Pausen, freie Tage — und greift ein wenn der Wellbeing Score sinkt. Bei Überlastung: Agent übernimmt automatisch mehr Routine, schützt den Kalender, und schlägt Entlastung vor. Marketing-Narrativ: "Der Agent der auf dich aufpasst" — unangreifbar von der Konkurrenz.

**6. MCP + n8n = 1.200+ Integrationen**
MCP (Model Context Protocol, Anthropic) als standardisierte Connector-Schicht + n8n Bridge für 1.200+ Integrationen die n8n already hat. Plus HTTP Universal Connector für jede REST API in 5 Minuten via Dashboard-UI. Kein Code, kein Deployment.

**7. On-Device AI**
Llama 3.2 1B auf dem Smartphone via ExecuTorch. DSGVO-kritische Mandanten können einfache KI-Funktionen nutzen OHNE dass Daten das Gerät verlassen. Das ist ein Argument das kein Wettbewerber hat.

### 5.2 Warum das schwer zu kopieren ist

Die einzelnen Komponenten (LangGraph, Graphiti, MCP) sind Open Source. Aber die Kombination — temporales Gedächtnis + progressive Autonomie + Selbstevolution + Weltmodell + Guardian Angel + deutsche Compliance + Mobile App + Voice — das ist ein System das 12+ Monate Entwicklung erfordert und tiefes Domänenwissen voraussetzt. Und selbst wenn jemand es kopiert: Der Wissensvorsprung eines Agenten der 12 Monate bei einem Kunden gelernt hat, ist nicht kopierbar. Das sind echte Switching Costs.

---

## 6. TEAM & RESSOURCEN

### 6.1 Gründer

**Oliver Hees — Geschäftsführer, Technical Lead**
- 20 Jahre Software-Entwicklung (Full Stack, WordPress, Next.js)
- Spezialisierung: n8n Workflow-Automation, AI-Telefonagenten, Voice AI
- YouTube (~2.700 Subscriber) + TikTok (~3.000 Follower) = Content-Maschine
- AI Automation Engineers Community (200+ Mitglieder)
- Bestehende Kundenbeziehungen zu Steuerberatern und §203-Berufen
- Ab März 2026: Vollzeit Agent One (Exit von Conversion Junkies)

**Alina Rosenbusch — Geschäftsführerin, Business Development**
- Co-Founderin HR Code Labs GbR
- Business Development, Kundenbeziehungen, Projektmanagement

### 6.2 Die "Geheimwaffe": Claude Code als Entwickler

Agent One wird primär mit Claude Code entwickelt — Anthropics KI-gestütztem Coding-Tool. Das reduziert den Bedarf an zusätzlichen Entwicklern dramatisch. Das PRD (2.315 Zeilen, 90KB) ist so geschrieben, dass Claude Code jede Komponente daraus implementieren kann. Effektiv haben wir ein "Team" von 2 Gründern + einem KI-Entwickler der 24/7 arbeitet.

### 6.3 Skalierungsstrategie Team

| Phase | Zeitraum | Team | Kosten/Mo |
|-------|----------|------|-----------|
| **Bootstrap** | Mo 1-6 | 2 Gründer + Claude Code | €3.000-5.000 |
| **Erste Einnahmen** | Mo 6-12 | + 1 Werkstudent (Support/Testing) | €5.000-7.000 |
| **Wachstum** | Mo 12-24 | + 1 Senior Dev + 1 Customer Success | €12.000-18.000 |
| **Skalierung** | Mo 24-36 | + 2 Devs + 1 Sales + 1 Marketing | €30.000-45.000 |

Personalkosten werden IMMER aus Einnahmen finanziert — kein Venture Capital, kein Risiko.

---

## 7. RISIKEN & MITIGATIONSSTRATEGIEN

### 7.1 Technische Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| LLM API-Kosten steigen | Mittel | Hoch | RouteLLM + Caching + Multi-Provider (Anthropic, OpenAI, Open Source) |
| LLM-Qualität schwankt | Niedrig | Mittel | A/B-Testing, Langfuse Monitoring, Fallback-Modelle |
| Graphiti/FalkorDB hat Bugs | Niedrig | Hoch | Open Source = wir können selbst fixen. Aktive Community |
| App Store Rejection | Niedrig | Mittel | Expo Managed Workflow, Apple Guidelines frühzeitig checken |
| On-Device AI zu langsam | Mittel | Niedrig | Optional Feature, Cloud-Fallback immer verfügbar |

### 7.2 Business-Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| **Langsame Adoption** | Mittel | Hoch | Content-Marketing + Community + persönliche Demos statt kalte Akquise |
| **DATEV blockt Integration** | Niedrig | Mittel | Agent One ersetzt DATEV nicht — ergänzt es. n8n Bridge als Workaround |
| **Großer Player betritt Markt** | Mittel | Mittel | First-Mover + Switching Costs + Branchenfokus + deutsche Compliance |
| **DSGVO-Regulierung verschärft** | Niedrig | Mittel | Zero-Data + Hybrid-Modell = bereits maximal konservativ |
| **Gründer-Abhängigkeit** | Hoch | Hoch | Dokumentation (PRD!), Claude Code reduziert Bus-Faktor, Community als Support-Schicht |

### 7.3 Marktrisiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| **KI-Hype flaut ab** | Niedrig | Mittel | Agent One liefert messbaren ROI (Stunden gespart), nicht "KI weil KI" |
| **Kunden zahlen nicht** | Niedrig | Mittel | Freemium vermeiden, Free-Trial statt Free-Tier, ROI in Trial nachweisen |
| **Wirtschaftskrise trifft KMUs** | Mittel | Mittel | Agent One spart Geld (ersetzt Teilzeitkraft) → Contra-zyklisch attraktiv |

---

## 8. IMPLEMENTIERUNGS-ROADMAP

### 8.1 Übersicht

```
2026
├── Q1 (Feb-Apr): Foundation + MVP
│   ├── Monorepo Setup
│   ├── Backend (FastAPI + LangGraph + Graphiti)
│   ├── Dashboard v1 (Chat, Approvals, Overview)
│   ├── Mobile App v1 (Chat, Briefing, Push)
│   ├── Gmail + Calendar Connectors
│   └── 3-5 Alpha-Tester (Steuerberater)
│
├── Q2 (Mai-Jul): Security + Proaktivität
│   ├── Multi-Tenant + DSGVO + Audit Trail
│   ├── Trust Score System
│   ├── Morgen-Briefing + Cron Jobs
│   ├── Voice (Deepgram + ElevenLabs)
│   ├── Vapi Telefon-Agent
│   └── 10-20 Beta-Kunden
│
├── Q3 (Aug-Okt): Connectors + Scaling
│   ├── MCP Gateway + n8n Bridge
│   ├── DATEV + HubSpot Connectors
│   ├── Hybrid-Deployment (Model B)
│   ├── White-Label v1
│   └── 50-80 zahlende Kunden
│
├── Q4 (Nov-Dez): Level 5 + Growth
│   ├── Self-Evolution Engine (Nightly Reflection, Skill Library)
│   ├── Business World Model
│   ├── Guardian Angel
│   ├── App Store Launch (iOS + Android)
│   └── 80-150 zahlende Kunden
│
2027
├── Q1: Optimierung + Scale
│   ├── Prompt Evolution Engine (A/B Testing)
│   ├── Connector Marketplace
│   ├── On-Device AI
│   └── 200-400 Kunden → €100K+ MRR
│
└── Q2+: Wachstum
    ├── Österreich + Schweiz
    ├── White-Label für Netzwerke
    ├── Team-Aufbau
    └── Ziel: €300K+ MRR
```

### 8.2 Meilensteine

| Meilenstein | Zeitpunkt | Erfolgskriterium |
|-------------|-----------|-----------------|
| **MVP funktioniert** | Ende März 2026 | Agent beantwortet E-Mails, erstellt Briefing, App funktioniert |
| **Erster zahlender Kunde** | April 2026 | €249+/Mo, Steuerberater |
| **Product-Market-Fit** | Juli 2026 | NPS >50, Churn <5%, 20+ Kunden |
| **€25K MRR** | Oktober 2026 | ~90 Kunden, Team wächst |
| **Level 5 Live** | Dezember 2026 | Self-Evolution + Guardian Angel im Einsatz |
| **€100K MRR** | Q1 2027 | ~370 Kunden, profitabel, skalierbar |

---

## 9. WARUM DAS FUNKTIONIEREN WIRD — ZUSAMMENFASSUNG

### Die sechs Gründe

1. **Der Markt ist riesig und unterversorgt.** 148.000+ Kanzleien/Praxen in Deutschland allein bei §203-Berufen. Keiner baut für sie. Der deutsche KI-Markt wächst 26%+ jährlich.

2. **Die Technologie ist reif.** LangGraph, Graphiti, MCP, Expo — alles production-ready. Wir müssen nichts erfinden, nur intelligent kombinieren.

3. **Die Kosten sind minimal.** Bootstrapped, Claude Code als Entwickler, Content-Marketing statt Paid Ads, Hetzner statt AWS. Break-Even bei ~21 Kunden.

4. **Der Burggraben wächst mit der Zeit.** Jeder Monat den ein Kunde Agent One nutzt, erhöht die Switching Costs. Der Agent lernt, der Knowledge Graph wächst, die Prompts verbessern sich. Das ist kein SaaS das man einfach kündigt und ersetzt.

5. **Die Gründer haben Domänenwissen.** 20 Jahre Softwareentwicklung, bestehende Kundenbeziehungen zu §203-Berufen, n8n-Expertise, eine Content-Plattform und eine Community. Das ist kein kalter Start.

6. **Die Vision ist größer als die Konkurrenz.** Kein anderer Agent hat Selbstevolution + Weltmodell + Guardian Angel. Während alle "mehr Produktivität" versprechen, versprechen wir "langfristigen Erfolg UND Gesundheit". Das ist eine Positionierung die nicht kopierbar ist, weil sie eine philosophische Überzeugung erfordert.

---

## 10. NÄCHSTE SCHRITTE (DIE NÄCHSTEN 30 TAGE)

1. **PRD finalisieren und an Claude Code übergeben** → Monorepo-Setup starten
2. **Olivers Exit von Conversion Junkies** → Vollzeit Agent One ab März 2026
3. **Beta-Warteliste aufsetzen** → Landing Page mit E-Mail-Sammlung
4. **Benjamin Arras als Alpha-Tester gewinnen** → Direktes Feedback aus der Zielgruppe
5. **YouTube-Video: "Ich baue den ultimativen KI-Agenten"** → Content-Serie starten
6. **Community informieren** → AI Automation Engineers als Early-Feedback-Gruppe
7. **Domain + Branding** → agent-one.de sichern, Logo, CI

---

*Dieses Dokument ist der Nordstern für Agent One. Es wird regelmäßig aktualisiert wenn sich Marktbedingungen, Technologien oder strategische Prioritäten ändern.*

**Agent One. Nicht das klügste Tool. Der weiseste Partner. Built in Germany. Für Mittelstand. Von HR Code Labs.**
