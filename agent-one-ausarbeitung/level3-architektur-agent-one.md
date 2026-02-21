# Agent One Level 3: Der Ambient Agent — Proaktiv, Autonom, Mobil

## Von "Antworte wenn gefragt" zu "Handle bevor du gefragt wirst"

Level 1 hat den Stack definiert. Level 2 hat Sicherheit, Intelligenz und das Dashboard gebaut. **Level 3 macht den fundamentalen Paradigmenwechsel: Der Agent wird vom passiven Antwortgeber zum proaktiven digitalen Mitarbeiter** — und die App wird zur Kommandozentrale die das alles in die Hosentasche bringt.

Der Unterschied ist gewaltig. Ein reaktiver Agent wartet auf "Schreib mir eine E-Mail an Herrn Müller." Ein proaktiver Ambient Agent erkennt, dass Herr Müllers Steuerbescheid seit 3 Tagen überfällig ist, entwirft eine Nachfrage-Mail, und schickt dir eine Push-Notification: "Soll ich das für dich absenden?" Du tippst auf Genehmigen — fertig. Unter der Dusche, an der Bushaltestelle, beim Spaziergang.

**Das ist kein Chat-Bot mehr. Das ist ein KI-Mitarbeiter der mitdenkt.**

---

## 1. Das Ambient Agent Framework — Proaktivität als Architektur

### 1.1 Was ist ein Ambient Agent?

Harrison Chase (CEO LangChain) hat Anfang 2025 das Konzept der **Ambient Agents** geprägt — und es verändert die gesamte Agent-Landschaft. Die Kernidee:

> "Ambient Agents reagieren auf Umgebungssignale und fordern menschlichen Input nur dann an, wenn sie wichtige Gelegenheiten erkennen oder Feedback brauchen. Statt Nutzer in neue Chat-Fenster zu zwingen, helfen diese Agenten, deine Aufmerksamkeit für das Wesentliche aufzusparen."

Der fundamentale Unterschied zu Chat-Agents:

| | Chat-Agent (Level 1-2) | Ambient Agent (Level 3) |
|---|---|---|
| **Auslöser** | Mensch initiiert Gespräch | Agent reagiert auf Ereignisse |
| **Modus** | Pull — Nutzer fragt | Push — Agent informiert/handelt |
| **Threads** | Einer gleichzeitig | Dutzende parallel im Hintergrund |
| **Latenz-Toleranz** | Nutzer wartet auf Antwort | Im Hintergrund → höhere Toleranz |
| **Skalierung** | 1 Mensch = 1 Gespräch | 1 Mensch = viele Agenten parallel |

Das Entscheidende: **Ambient Agents ersetzen Chat nicht — sie ergänzen ihn.** Der Nutzer kann jederzeit in den Chat wechseln und direkt mit dem Agenten sprechen. Aber der Hauptwert entsteht durch das, was der Agent tut, OHNE dass man ihn fragt.

### 1.2 Die Vier Schichten proaktiver Intelligenz

```
┌─────────────────────────────────────────────────┐
│            SCHICHT 4: ANTIZIPATION               │
│   Agent sagt voraus was du brauchen wirst        │
│   "Nächste Woche ist USt-VA fällig — ich         │
│    bereite die Unterlagen schon mal vor"          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│            SCHICHT 3: PROAKTIVITÄT               │
│   Agent erkennt Situation und handelt            │
│   "Neue E-Mail von Finanzamt → Frist             │
│    extrahiert → Kalender-Eintrag erstellt"        │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│            SCHICHT 2: MONITORING                 │
│   Agent überwacht und benachrichtigt             │
│   "3 dringende E-Mails in den letzten            │
│    2 Stunden → Push-Notification"                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│            SCHICHT 1: REAKTION                   │
│   Agent antwortet auf direkte Anfragen           │
│   "Schreib eine Mail an Herrn Müller"            │
└─────────────────────────────────────────────────┘
```

Level 1-2 operiert auf Schicht 1. **Level 3 aktiviert alle vier Schichten.**

### 1.3 LangGraph Cron Jobs — Das Heartbeat-System das funktioniert

OpenClaw hat ein Heartbeat-System — aber es ist kaputt. Ein aktueller GitHub-Bug (#3589) zeigt: Wenn Cron-Jobs System-Events feuern, wird der Heartbeat-Prompt an ALLE Events angehängt, der Agent antwortet auf alles mit "HEARTBEAT_OK" und ignoriert die eigentliche Aufgabe.

**LangGraph hat natives Cron-Job-Support** das tatsächlich funktioniert:

```python
from langgraph_sdk import get_client

client = get_client(url=DEPLOYMENT_URL)

# Morgen-Briefing jeden Tag um 7:00 UTC
morgen_briefing = await client.crons.create(
    assistant_id="agent-one",
    schedule="0 7 * * *",  # Standard Cron-Syntax
    input={
        "messages": [{
            "role": "user",
            "content": "Erstelle das Morgen-Briefing: "
                       "Prüfe neue E-Mails, anstehende Termine, "
                       "offene Fristen, und dringende Aufgaben."
        }]
    }
)

# E-Mail-Monitoring alle 5 Minuten
email_monitor = await client.crons.create(
    assistant_id="email-agent",
    schedule="*/5 * * * *",
    input={
        "messages": [{
            "role": "user",
            "content": "Prüfe Posteingang auf neue E-Mails. "
                       "Kategorisiere nach Dringlichkeit. "
                       "Entwirfe Antworten für Routine-Anfragen."
        }]
    }
)

# Fristen-Wächter täglich um 8:00
fristen_waechter = await client.crons.create(
    assistant_id="fristen-agent",
    schedule="0 8 * * *",
    input={
        "messages": [{
            "role": "user",
            "content": "Prüfe alle Fristen in den nächsten 7 Tagen. "
                       "Erstelle Erinnerungen für jede Frist die "
                       "in weniger als 3 Tagen abläuft."
        }]
    }
)
```

Jeder Cron-Job erzeugt einen eigenen Thread. Mit `on_run_completed="keep"` bleiben die Ergebnisse für spätere Abfrage erhalten. LangGraphs eingebautes Checkpointing stellt sicher, dass bei einem Fehler der Job beim letzten erfolgreichen Checkpoint fortsetzt.

### 1.4 Event-Driven Triggers — Über Cron hinaus

Cron ist nur der Anfang. Der wirkliche Wert entsteht durch **Event-Driven Triggers** — der Agent reagiert auf reale Ereignisse in Echtzeit:

| Trigger | Event Source | Agent-Aktion |
|---------|-------------|--------------|
| **Neue E-Mail** | IMAP Webhook / Gmail Push API | Kategorisieren, Frist extrahieren, Antwort entwerfen |
| **Verpasster Anruf** | Vapi Call Event | Rückruf planen, Voicemail zusammenfassen, Follow-up entwerfen |
| **Kalendererinnerung** | Google Calendar Webhook | Vorbereitung zusammenstellen, relevante Dokumente finden |
| **Frist nähert sich** | Graphiti temporal query | Erinnerung an Mandant, Unterlagen-Checkliste erstellen |
| **Neuer Mandant** | CRM Webhook | Willkommens-Workflow starten, Onboarding-Checklist erstellen |
| **Dokument eingegangen** | Cloud Storage Event | OCR, Klassifizierung, Ablage, relevante Frist extrahieren |
| **Zahlungseingang** | Buchhaltungs-Webhook | Rechnung als bezahlt markieren, Bestätigung senden |

Die Architektur:

```
Event Sources (E-Mail, Kalender, Telefon, CRM, ...)
         │
         ▼
   Event Router (FastAPI + Redis Pub/Sub)
         │
    ┌────┼────┬────┐
    ▼    ▼    ▼    ▼
  Email  Cal  Tel  Fristen
  Agent  Agent Agent Wächter
    │    │    │    │
    ▼    ▼    ▼    ▼
     Graphiti Knowledge Graph
         │
         ▼
   Entscheidung: Autonom handeln ODER Mensch fragen
         │
    ┌────┴────┐
    ▼         ▼
Auto-Execute  Push an App → Agent Inbox
```

### 1.5 Die Drei HITL-Patterns für Ambient Agents

LangChain hat drei Human-in-the-Loop Patterns für Ambient Agents definiert die perfekt mit unserer Approval-Gate-Architektur zusammenspielen:

**1. Notify (Benachrichtigen):** Der Agent flaggt etwas Wichtiges, handelt aber NICHT. *Beispiel:* "Ein Einschreiben vom Finanzamt ist eingegangen. Ich kann das nicht öffnen — bitte prüfe es."

**2. Question (Fragen):** Der Agent braucht Input um weiterzumachen. *Beispiel:* "Herr Schmidt fragt ob er am Donnerstag oder Freitag kommen kann. Welcher Tag passt dir besser?" Der Nutzer antwortet in der App, der Agent schickt die Antwort.

**3. Review (Prüfen):** Der Agent hat etwas vorbereitet und braucht Freigabe. *Beispiel:* "Ich habe eine Antwort an das Finanzamt entworfen. Bitte prüfe und genehmige." Die App zeigt den vollständigen E-Mail-Entwurf mit Genehmigen/Ablehnen/Bearbeiten.

---

## 2. Progressive Autonomie — Der Agent der Vertrauen verdient

### 2.1 Das Trust-Score-System

Das revolutionärste Konzept in Level 3: **Der Agent verdient sich Autonomie schrittweise.** Nicht der Entwickler entscheidet was der Agent darf — sondern die Historie von Genehmigungen und Ablehnungen.

```
Trust Score pro Aktionstyp:

[E-Mail an bestehende Mandanten senden]
  Genehmigt: 47x | Abgelehnt: 2x | Bearbeitet: 5x
  → Trust Score: 87% → AUTO-GENEHMIGT (Schwellenwert: 85%)

[E-Mail an unbekannte Kontakte senden]
  Genehmigt: 3x | Abgelehnt: 4x | Bearbeitet: 6x
  → Trust Score: 23% → IMMER GENEHMIGUNG ERFORDERLICH

[Kalender-Termin erstellen]
  Genehmigt: 89x | Abgelehnt: 0x | Bearbeitet: 3x
  → Trust Score: 97% → AUTO-GENEHMIGT

[Telefonat initiieren]
  Genehmigt: 12x | Abgelehnt: 8x
  → Trust Score: 60% → GENEHMIGUNG ERFORDERLICH (Schwellenwert: 85%)
```

Das Trust-Score-Modell:

```python
class TrustScore:
    def __init__(self, action_type: str, tenant_id: str):
        self.action_type = action_type
        self.tenant_id = tenant_id
    
    def calculate(self) -> float:
        """Gewichteter Score basierend auf letzten 100 Interaktionen"""
        history = get_approval_history(
            self.action_type, self.tenant_id, limit=100
        )
        
        approved = sum(1 for h in history if h.status == "approved")
        rejected = sum(1 for h in history if h.status == "rejected")
        edited = sum(1 for h in history if h.status == "edited")
        
        # Bearbeitungen zählen halb — Agent war auf richtigem Weg
        score = (approved + edited * 0.5) / len(history)
        
        # Recency Bias — jüngere Entscheidungen wiegen schwerer
        recency_weighted = apply_exponential_decay(history, score)
        
        return recency_weighted
    
    def should_auto_approve(self) -> bool:
        score = self.calculate()
        threshold = get_tenant_threshold(self.tenant_id)
        return score >= threshold  # Default: 0.85 (85%)
```

### 2.2 Kontext-Sensitive Autonomie

Der Trust Score allein reicht nicht. Der Agent muss den **Kontext** verstehen:

| Situation | Gleiche Aktion, anderer Kontext | Verhalten |
|-----------|----------------------------------|-----------|
| E-Mail an Mandant Müller | Routine-Frage beantworten | Auto-genehmigt (Trust: 92%) |
| E-Mail an Mandant Müller | Steuerrechtliche Auskunft | **Review erforderlich** (sensibel) |
| Kalender-Eintrag | Routine-Termin buchen | Auto-genehmigt |
| Kalender-Eintrag | Termin im Namen des Chefs buchen | **Review erforderlich** (Delegation) |
| Telefon-Anruf | Terminerinnerung | Auto-genehmigt nach Trust-Aufbau |
| Telefon-Anruf | Erstgespräch mit Neukunde | **Immer Review** (hoher Impact) |

Der Agent erkennt den Kontext durch Graphiti: Wenn eine Aktion Entitäten betrifft die als "sensibel" markiert sind (z.B. Finanzdaten, Gesundheitsdaten), wird automatisch auf Review geschaltet — unabhängig vom Trust Score.

### 2.3 Lernende Autonomie — Der Agent verbessert sich selbst

Jedes Mal wenn der Nutzer eine Agent-Aktion **bearbeitet** (nicht nur genehmigt/abgelehnt), lernt der Agent WARUM:

```
Nutzer bearbeitet E-Mail-Entwurf:
  Vorher: "Sehr geehrter Herr Müller, anbei die Unterlagen."
  Nachher: "Lieber Herr Müller, wie besprochen die Unterlagen."

→ Agent speichert in Graphiti:
  Entity: Mandant Müller
  Learned: "Bevorzugt informellen Ton ('Lieber' statt 'Sehr geehrter')"
  Learned: "Bezugnahme auf vorherige Kommunikation gewünscht"

→ Nächstes Mal an Müller: Automatisch informeller Ton + Bezug
```

Das wird möglich durch die Kombination von:
- **Graphiti Reflexion** (Level 2) — strukturierte Lektionen aus Fehlern
- **Trust Score** — quantitatives Maß des Vertrauens
- **Edit-Diff-Analyse** — Was hat der Mensch geändert und warum?

---

## 3. Die App — Deine Kommandozentrale in der Hosentasche

### 3.1 Warum die App alles verändert

Das Dashboard (Level 2) ist für den Desktop. Aber deutsche KMU-Chefs sitzen nicht den ganzen Tag am Computer. Sie sind unterwegs, bei Mandanten, im Auto, beim Mittagessen. **Die App macht den Ambient Agent erst möglich** — ohne sie gibt es keine Push-Notifications, keine Schnell-Genehmigungen, keine Echtzeit-Kontrolle.

Die App ist NICHT einfach ein responsives Dashboard. Die App nutzt Fähigkeiten die ein Browser nicht hat:

| Fähigkeit | Was es ermöglicht | Expo-Modul |
|-----------|-------------------|------------|
| **Push Notifications** | Agent-Alerts, Genehmigungsanfragen | `expo-notifications` |
| **Biometrische Auth** | FaceID/Fingerprint für sensible Aktionen | `expo-local-authentication` |
| **Kamera/Scanner** | Dokumente scannen, direkt an Agent übergeben | `expo-camera` |
| **Spracheingabe** | "Hey Agent, ruf Müller an" | `expo-speech` + STT |
| **Background Tasks** | Agent-Updates auch bei geschlossener App | `expo-background-fetch` |
| **Offline-Modus** | Grundfunktionen ohne Internet | On-Device AI |
| **Haptic Feedback** | Taktile Bestätigung bei Genehmigungen | `expo-haptics` |
| **Deep Links** | Direkt zur Genehmigung aus Notification | Expo Router |
| **Widgets** | Agent-Status auf Homescreen (iOS/Android) | Native Module |
| **Secure Storage** | Tokens/Keys im Secure Enclave | `expo-secure-store` |

### 3.2 Tech-Stack: Expo + React Native

```
Expo SDK 52+ (Managed Workflow mit Custom Dev Client)
├── expo-router (File-based Navigation)
├── expo-notifications (Push Notifications)
├── expo-local-authentication (Biometrie)
├── expo-camera (Dokumenten-Scan)
├── expo-secure-store (Sichere Key-Speicherung)
├── expo-background-fetch (Hintergrund-Updates)
├── @ai-sdk/react (Vercel AI SDK für Streaming Chat)
├── react-native-executorch (On-Device AI — optional)
├── TanStack Query (Server-State Management)
├── Zustand (Client-State)
├── NativeWind (Tailwind für React Native)
└── react-native-reanimated (Flüssige Animationen)
```

**Warum Expo?** SOC 2 Type 2 und GDPR-konform. Over-the-Air Updates ohne App Store Review. Eine Codebase für iOS + Android. Mistral, v0, Replit und Bluesky setzen alle auf React Native/Expo. Die New Architecture (TurboModules, Fabric) ist seit 2025 Standard mit 60fps und 40% schnellerer Startup-Zeit.

### 3.3 Die Fünf App-Screens die alles abdecken

**Screen 1: Agent Inbox (Startscreen)**

Der wichtigste Screen. Inspiriert von LangChains Agent Inbox — aber mobile-native:

```
┌─────────────────────────────────┐
│  Agent One          🔔 ⚙️      │
│─────────────────────────────────│
│                                 │
│  🔴 DRINGEND (2)                │
│  ┌─────────────────────────────┐│
│  │ ✉️ Finanzamt-Bescheid       ││
│  │ Frist: 14.02.2026           ││
│  │ Agent: "Einspruch nötig?"   ││
│  │ [Prüfen] [Später]           ││
│  └─────────────────────────────┘│
│  ┌─────────────────────────────┐│
│  │ 📞 Verpasster Anruf Müller ││
│  │ Agent hat Rückruf geplant   ││
│  │ [Genehmigen ✓] [Ändern ✏️] ││
│  └─────────────────────────────┘│
│                                 │
│  🟡 REVIEW (5)                  │
│  ┌─────────────────────────────┐│
│  │ ✉️ E-Mail-Entwurf an Schmidt││
│  │ "Lieber Herr Schmidt..."    ││
│  │ [✓ Senden] [✏️] [✗]         ││
│  └─────────────────────────────┘│
│  ... 4 weitere                  │
│                                 │
│  🟢 ERLEDIGT HEUTE (12)        │
│  Agent hat 12 Aktionen          │
│  automatisch ausgeführt         │
│  [Details anzeigen →]           │
│                                 │
│─────────────────────────────────│
│  💬 Chat  📥 Inbox  📊 Stats   │
└─────────────────────────────────┘
```

**Swipe-Gesten** für schnelle Aktionen: Rechts wischen = Genehmigen. Links wischen = Ablehnen. Lange drücken = Bearbeiten. Biometrische Authentifizierung für sensible Genehmigungen (E-Mail senden, Anruf initiieren).

**Screen 2: Chat-Interface**

Für direkte Kommunikation mit dem Agenten. Streaming-Antworten via Vercel AI SDK (`expo/fetch` für SSE-Streaming ab Expo 52+). Voice-Input via Mikrofon-Button. Kontext aus Graphiti wird automatisch geladen — der Agent kennt dich und deine Mandanten.

**Screen 3: Agent-Activity (Live-Feed)**

Echtzeit-Ansicht was der Agent gerade tut:

```
10:23  📧 E-Mail von Frau Weber gescannt → Routine
10:22  📅 Termin mit Herrn Braun bestätigt (Auto)
10:20  🔍 Fristenprüfung abgeschlossen → Alles OK
10:15  📧 Antwort an Mandant Koch gesendet (Auto)
10:12  ⏸️ E-Mail an Finanzamt wartet auf Genehmigung
10:10  📞 Anruf-Zusammenfassung: Fr. Lehmann gespeichert
```

Tippe auf jeden Eintrag für volle Details, Trace-Waterfall und die Möglichkeit, die Aktion rückgängig zu machen (innerhalb eines konfigurierbaren Zeitfensters).

**Screen 4: Knowledge Graph Browser**

Interaktive Visualisierung der Mandanten-Beziehungen. Suche nach einer Person → Expandiere Verbindungen. Zeigt was der Agent über jeden Mandanten weiß. Mandanten können fehlerhafte Fakten direkt korrigieren ("Das stimmt nicht mehr — ich bin jetzt bei Firma X").

**Screen 5: Einstellungen & Autonomie-Control**

Pro-Agent Autonomie-Regler. Trust-Score-Schwellenwerte anpassen. Benachrichtigungs-Präferenzen (welche Agents dürfen pushen, wann). White-Label-Theming.

### 3.4 Push Notifications — Die Brücke zwischen Agent und Mensch

Push Notifications sind der **kritischste Kanal** für Ambient Agents. Ohne sie weiß der Mensch nicht, dass der Agent etwas braucht.

**Intelligentes Notification-Routing:**

```python
class NotificationRouter:
    """Entscheidet WIE und WANN der Mensch benachrichtigt wird"""
    
    def route(self, event: AgentEvent, user: User):
        urgency = self.classify_urgency(event)
        
        if urgency == "CRITICAL":
            # Sofortige Push + Sound + Vibration
            send_push(user, event, 
                      sound="alert", priority="high",
                      badge_count=increment)
        
        elif urgency == "REVIEW_NEEDED":
            # Stille Push mit Badge-Update
            if user.is_within_work_hours():
                send_push(user, event, 
                          sound="subtle", priority="normal")
            else:
                # Außerhalb Arbeitszeit → Sammeln für Morgen-Briefing
                queue_for_morning_brief(event)
        
        elif urgency == "INFO":
            # Nur Badge-Update, kein Sound
            update_badge(user, increment=1)
        
        elif urgency == "COMPLETED":
            # Nur In-App Activity Feed
            # KEINE Push — der Mensch soll nicht gestört werden
            log_to_activity_feed(event)
```

**Actionable Notifications** — Genehmigen direkt aus der Notification:

Expo + iOS/Android unterstützen interaktive Notification-Actions. Der Nutzer sieht "E-Mail-Entwurf an Müller: 'Lieber Herr Müller...'" und kann direkt aus der Notification **Senden**, **Ablehnen** oder **In App öffnen** wählen — ohne die App zu öffnen.

**Batching für nicht-dringende Reviews:**

Statt 20 einzelne Notifications am Tag → "Du hast 5 Aktionen zum Prüfen" mit einem zusammenfassenden Screen der alle auf einmal abarbeiten lässt.

### 3.5 Dokumenten-Scanner — KI trifft Kamera

Ein Killer-Feature für Steuerberater, Anwälte und Ärzte:

```
Nutzer fotografiert Dokument mit App
         │
         ▼
   On-Device OCR (expo-camera + ML Kit)
         │
         ▼
   Agent klassifiziert Dokument
   "Steuerbescheid für Mandant Müller,
    Einspruchsfrist: 28.02.2026"
         │
    ┌────┴────┐
    ▼         ▼
  Frist in    Dokument in
  Kalender    Mandantenakte
  eingetragen abgelegt
         │
         ▼
   Push: "Steuerbescheid für Müller erfasst.
          Frist 28.02. im Kalender. Alles OK?"
   [✓ Bestätigen] [✏️ Korrigieren]
```

Vom Foto zum vollständig verarbeiteten Dokument in Sekunden. Das spart Steuerberatern STUNDEN pro Woche.

### 3.6 Voice-First Interaktion

Für Momente wo Tippen nicht geht — Autofahrt, Hände voll:

```
Nutzer: *drückt Voice-Button in App*
"Hey Agent, was steht heute an?"

Agent (via TTS in der App):
"Guten Morgen! Du hast heute 3 Termine.
 Um 10 kommt Frau Weber zur Beratung —
 ich habe ihre Steuerunterlagen vorbereitet.
 Um 14 Uhr Telefonat mit Herrn Koch.
 Und um 16 Uhr hast du einen Slot frei —
 soll ich den für Rückrufe nutzen?"

Nutzer: "Ja, ruf Herrn Müller zurück
         wegen dem Bescheid."

Agent: "OK, ich plane einen Rückruf an
        Herrn Müller um 16 Uhr zum Thema
        Steuerbescheid. Genehmigst du das?"

Nutzer: "Ja."

→ Agent plant Anruf, erstellt Gesprächsnotiz mit Kontext
```

Technischer Stack für In-App Voice: **Deepgram** (STT, exzellente deutsche Unterstützung) → LangGraph Agent → **ElevenLabs** (TTS mit natürlichem deutschen Klang). Latenz ~600ms — schnell genug für natürliches Gespräch.

### 3.7 On-Device AI — Intelligenz ohne Internet

**React Native ExecuTorch** ermöglicht das Ausführen von KI-Modellen direkt auf dem Gerät:

```javascript
import { useLLM, LLAMA3_2_1B } from 'react-native-executorch';

function OfflineAssistant() {
    const llm = useLLM({ model: LLAMA3_2_1B });
    
    // Funktioniert komplett offline:
    // - E-Mail-Entwürfe prüfen/korrigieren
    // - Dokumente zusammenfassen
    // - Einfache Fragen beantworten
    // - Text-Klassifikation
}
```

**Was On-Device AI für die Plattform bedeutet:**

| Fähigkeit | Cloud (Standard) | On-Device (Offline-Fallback) |
|-----------|-------------------|------------------------------|
| Komplexes Reasoning | Claude/GPT-4o | ✗ Nicht möglich |
| Einfache Text-Generierung | Schnell + teuer | Langsam + kostenlos |
| Dokument-Zusammenfassung | ✓ Beste Qualität | ✓ Akzeptable Qualität |
| E-Mail-Klassifikation | Nicht nötig | ✓ On-Device perfekt |
| OCR + Text-Erkennung | ✓ Cloud APIs | ✓ Whisper on-device |
| Offline-Verfügbarkeit | ✗ Kein Internet = keine KI | ✓ Grundfunktionen bleiben |

**Der strategische Wert:** DSGVO-kritische Mandanten (Ärzte, Anwälte) können einfache KI-Funktionen nutzen OHNE dass Daten das Gerät verlassen. Llama 3.2 1B läuft auf modernen Smartphones mit akzeptabler Geschwindigkeit. Das ist ein massives Verkaufsargument.

---

## 4. Das Morgen-Briefing — Proaktivität die man sofort fühlt

### 4.1 Das Killer-Feature für KMU-Chefs

Jeden Morgen um 7:00 (konfigurierbar) erhält der Nutzer eine Push-Notification:

> "☀️ Guten Morgen! Dein Agent-Briefing ist fertig."

In der App öffnet sich eine personalisierte Zusammenfassung:

```
┌─────────────────────────────────┐
│  ☀️ Morgen-Briefing              │
│  Mittwoch, 12. Februar 2026     │
│─────────────────────────────────│
│                                 │
│  📊 ZUSAMMENFASSUNG              │
│  Gestern: 47 Aktionen erledigt  │
│  (39 automatisch, 8 genehmigt)  │
│  Eingesparte Zeit: ~2,5 Std.    │
│                                 │
│  📅 HEUTE                        │
│  • 10:00 Frau Weber (Beratung)  │
│    → Unterlagen vorbereitet ✓   │
│  • 14:00 Herr Koch (Telefonat)  │
│    → Gesprächsnotiz erstellt ✓  │
│  • 16:00 Frei → 3 Rückrufe     │
│    vorgeschlagen                 │
│                                 │
│  ⚠️ ACHTUNG                     │
│  • Frist Mandant Schulz in 2T   │
│  • 3 unbeantwortete E-Mails     │
│    (seit >24h)                   │
│  • USt-VA Abgabe in 5 Tagen     │
│                                 │
│  📧 ÜBER NACHT                   │
│  12 neue E-Mails eingegangen    │
│  • 3 dringend (rot markiert)    │
│  • 7 Routine (Antworten fertig) │
│  • 2 Spam (archiviert)          │
│                                 │
│  [7 Antworten prüfen & senden →]│
│                                 │
└─────────────────────────────────┘
```

**Technische Umsetzung:** LangGraph Cron-Job → Supervisor Agent sammelt Daten von allen Sub-Agenten → Graphiti-Query für Fristen und Kontext → Kompakte Zusammenfassung generiert → Push-Notification → App zeigt Briefing.

### 4.2 Das Abend-Wrap-Up

Gegenstück zum Morgen-Briefing:

```
🌙 Tages-Zusammenfassung

Erledigt: 52 Aktionen
  - 41 automatisch (keine Störung)
  - 11 mit deiner Genehmigung

Gelernt heute:
  - Mandant Weber bevorzugt E-Mail über Telefon
  - Finanzamt Hamburg: Bearbeitungszeit ~14 Tage
  - Neue Mandantin Frau Lehmann erfasst

Morgen anstehend:
  - 2 Termine, 1 Fristablauf
  - Morgen-Briefing kommt um 7:00 ☀️
```

Das Abend-Wrap-Up ist auch ein Trust-Builder — der Nutzer sieht konkret was der Agent geleistet hat und wieviel Zeit gespart wurde.

---

## 5. Agent-Workflows — Komplexe Aufgabenketten autonom

### 5.1 Vordefinierte Workflows für KMU-Branchen

Ambient Agents werden richtig mächtig wenn sie **Multi-Step-Workflows** autonom ausführen:

**Workflow: Neuen Mandanten onboarden (Steuerberater)**

```
Trigger: Neuer Kontakt im CRM erstellt
                    │
Step 1: Willkommens-E-Mail senden
        (Template + Personalisierung via Graphiti)
        → Auto-genehmigt nach Trust-Aufbau
                    │
Step 2: Onboarding-Checkliste erstellen
        (Steuer-ID, Vollmacht, Unterlagen-Liste)
        → Auto-genehmigt
                    │
Step 3: Termin für Erstgespräch vorschlagen
        (Kalender-Verfügbarkeit prüfen,
         3 Optionen per E-Mail senden)
        → Review erforderlich (Erstgespräch = hoher Impact)
                    │
Step 4: Nach Erstgespräch → Gesprächsnotiz
        automatisch in Mandantenakte speichern
        + Follow-up Tasks erstellen
        → Auto-genehmigt
                    │
Step 5: 7 Tage später → Follow-up
        "Haben Sie die Unterlagen bereits?"
        → Konfigurierbar (Auto oder Review)
```

**Workflow: Fristüberwachung (Anwälte)**

```
Trigger: Graphiti erkennt Frist < 7 Tage
                    │
Step 1: Relevante Dokumente zusammenstellen
                    │
Step 2: Prüfen ob alle Unterlagen komplett
                    │
Step 3: Falls Unterlagen fehlen →
        Mandant automatisch kontaktieren
        (E-Mail mit konkreter Liste)
                    │
Step 4: Falls < 3 Tage → Dringlichkeits-Eskalation
        Push an Anwalt + Büroleiterin
                    │
Step 5: Falls < 1 Tag → Roter Alarm
        Anruf-Vorschlag an Mandant
```

### 5.2 Workflow-Builder im Dashboard

Für Power-User: Ein visueller Workflow-Builder im Dashboard (nicht App — zu komplex für Mobilscreen) mit dem Mandanten eigene Automatisierungen erstellen können:

```
WENN [Trigger auswählen]
  → DANN [Aktion auswählen]
  → MIT [Bedingung: Auto/Review]
  → BEI FEHLER [Fallback-Aktion]
```

Das unterscheidet sich von n8n dadurch, dass der KI-Agent die **Entscheidungen innerhalb des Workflows** trifft — nicht statische if/then-Logik. Der Workflow definiert die Struktur, der Agent füllt sie intelligent aus.

---

## 6. Sicherheit für Proaktivität — Weil Autonomie Vertrauen braucht

### 6.1 Action-Budget pro Agent und Zeitraum

Proaktive Agenten brauchen Grenzen. Ohne Budgets könnte ein Bug dazu führen, dass der Agent 1.000 E-Mails in einer Stunde sendet.

```python
class ActionBudget:
    """Limitiert Agent-Aktionen pro Zeitraum"""
    
    DEFAULTS = {
        "email_send": {"per_hour": 10, "per_day": 50},
        "phone_call": {"per_hour": 3, "per_day": 10},
        "calendar_create": {"per_hour": 5, "per_day": 20},
        "knowledge_write": {"per_hour": 100, "per_day": 1000},
    }
    
    def check_budget(self, action_type: str, tenant_id: str) -> bool:
        """Prüft ob Budget für diese Aktion noch verfügbar"""
        used = get_action_count(action_type, tenant_id, period="1h")
        limit = self.get_limit(action_type, tenant_id, "per_hour")
        
        if used >= limit:
            alert_admin(f"Budget erschöpft: {action_type} für {tenant_id}")
            return False
        return True
```

### 6.2 Undo-Fenster — Jede Aktion ist umkehrbar

Für jede auto-genehmigte Aktion gibt es ein **konfigurierbares Undo-Fenster**:

- E-Mails: 30 Sekunden Verzögerung vor tatsächlichem Senden (wie Gmail's "Undo Send")
- Kalender-Einträge: Jederzeit löschbar
- Telefonate: Können bis zum Verbindungsaufbau abgebrochen werden
- Daten-Änderungen: Graphitis bi-temporales Modell ermöglicht vollständiges Rollback

In der App: "Agent hat E-Mail an Müller gesendet. [Rückgängig — noch 25 Sek.]"

### 6.3 Kill Switch — Sofort alles stoppen

Jeder Mandant hat einen **Not-Aus-Knopf** in der App:

```
[🔴 ALLE AGENTEN STOPPEN]
```

Ein Tap (+ biometrische Bestätigung) pausiert sofort ALLE aktiven Agenten für diesen Mandanten. Alle laufenden Aktionen werden nach Möglichkeit abgebrochen. Alle geplanten Cron-Jobs werden suspendiert. Ein Notification geht an den Admin (dich).

Reaktivierung nur durch den Mandanten ODER nach einem konfigurierbaren Timeout mit manueller Bestätigung.

---

## 7. Der technische Gesamtüberblick — Level 3 Architektur

```
┌────────────────────────────────────────────────────────────────┐
│                     EXPO APP (iOS + Android)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │Agent     │  │Chat      │  │Activity  │  │Knowledge     │  │
│  │Inbox     │  │Interface │  │Feed      │  │Graph Browser │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │              │               │          │
│  ┌────┴──────────────┴──────────────┴───────────────┴───────┐  │
│  │  On-Device AI (ExecuTorch) — Offline-Fallback            │  │
│  │  Biometrie (expo-local-auth) — Sensible Genehmigungen    │  │
│  │  Push Notifications — Agent-zu-Mensch Kommunikation      │  │
│  │  Camera/OCR — Dokumenten-Scanner                          │  │
│  │  Voice I/O — Sprachsteuerung                              │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │ HTTPS/WSS + SSE Streaming
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                    NEXT.JS FRONTEND (Web Dashboard)             │
│  Admin Dashboard + Kunden Dashboard + Workflow Builder          │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                    FASTAPI + LANGGRAPH BACKEND                  │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────────────────────────┐ │
│  │ Event Router    │  │ LangGraph Orchestrator               │ │
│  │ (Redis Pub/Sub) │  │                                      │ │
│  │                 │  │  Supervisor Agent (Plan-and-Execute)  │ │
│  │ Sources:        │  │       │                               │ │
│  │ • IMAP/Gmail    │  │  ┌────┼────┬────┬────┐               │ │
│  │ • Vapi Webhooks │  │  ▼    ▼    ▼    ▼    ▼               │ │
│  │ • Calendar API  │  │ Email Cal  Tel  Res  Fristen         │ │
│  │ • CRM Webhooks  │  │ Agent Agent Agent Agent Wächter      │ │
│  │ • FS Events     │  │                                      │ │
│  └────────┬────────┘  └──────────────┬───────────────────────┘ │
│           │                          │                          │
│  ┌────────┴──────────────────────────┴───────────────────────┐ │
│  │              CRON JOB ENGINE (LangGraph native)            │ │
│  │  • Morgen-Briefing (07:00)    • E-Mail-Monitor (*/5min)   │ │
│  │  • Fristen-Check (08:00)      • Abend-Wrap-Up (18:00)    │ │
│  │  • Inbox-Triage (*/15min)     • Weekly Report (Mo 09:00)  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │              TRUST & AUTONOMIE ENGINE                      │ │
│  │  • Trust Scores pro Aktion + Mandant                      │ │
│  │  • Action Budgets + Rate Limiting                          │ │
│  │  • Undo-Windows + Kill Switch                              │ │
│  │  • Approval Queue → App Push / Slack / Email               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │              NOTIFICATION ENGINE                           │ │
│  │  • Expo Push Service (iOS + Android)                      │ │
│  │  • Urgency Classification + Smart Routing                  │ │
│  │  • Batch-Notifications + Morgen-Briefing                   │ │
│  │  • Slack Integration (optional)                            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│               DATEN & MEMORY LAYER (Hetzner DE)                │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Graphiti +      │  │ PostgreSQL       │  │ Redis        │  │
│  │ FalkorDB        │  │ (Auth, Tenants,  │  │ (Caching,    │  │
│  │ (Knowledge      │  │  Audit Logs,     │  │  Pub/Sub,    │  │
│  │  Graph Memory)  │  │  Trust Scores)   │  │  Semantic    │  │
│  │                 │  │                  │  │  Cache)      │  │
│  └─────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ HashiCorp Vault │  │ LiteLLM Gateway  │  │ Langfuse     │  │
│  │ (Secrets)       │  │ (Multi-Provider  │  │ (Observ-     │  │
│  │                 │  │  + Failover)     │  │  ability)    │  │
│  └─────────────────┘  └──────────────────┘  └──────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementierungs-Roadmap Level 3

### Phase 3A — Ambient Foundation (Wochen 9-14, nach Level 2)

| Deliverable | Details |
|-------------|---------|
| **LangGraph Cron Engine** | Morgen-Briefing, Abend-Wrap-Up, Fristen-Wächter |
| **Event Router** | Redis Pub/Sub, Gmail Push API, Calendar Webhooks |
| **Notification Engine** | Expo Push Service Integration, Urgency-Routing |
| **Expo App v1** | Agent Inbox, Chat, Activity Feed (Grundgerüst) |
| **Trust Score System** | Basis-Implementierung mit Approval-Tracking |
| **Action Budgets** | Rate Limiting pro Agent und Mandant |

### Phase 3B — Progressive Autonomie (Wochen 15-20)

| Deliverable | Details |
|-------------|---------|
| **Trust Score Engine** | Vollständig mit Recency-Bias und Kontext-Sensitivität |
| **Auto-Approval System** | Trust-basierte automatische Genehmigungen |
| **Edit-Diff-Learning** | Agent lernt aus menschlichen Korrekturen |
| **Undo-Windows** | Verzögertes Senden, Rollback-Fähigkeit |
| **Kill Switch** | Not-Aus pro Mandant mit biometrischer Auth |
| **Workflow Engine** | Vordefinierte Branchen-Workflows (Steuerberater, Anwalt) |

### Phase 3C — App-Superkräfte (Wochen 21-26)

| Deliverable | Details |
|-------------|---------|
| **Dokumenten-Scanner** | Kamera → OCR → Agent → Ablage |
| **Voice I/O** | Deepgram STT + ElevenLabs TTS in der App |
| **On-Device AI** | ExecuTorch mit Llama 3.2 1B für Offline-Fallback |
| **Actionable Notifications** | Genehmigen/Ablehnen direkt aus Notification |
| **Batch-Review Screen** | Alle offenen Reviews auf einen Blick |
| **Widget** | Homescreen-Widget mit Agent-Status |
| **Biometrische Approval** | FaceID/Fingerprint für sensible Aktionen |

### Phase 3D — Intelligence Amplification (Wochen 27-32)

| Deliverable | Details |
|-------------|---------|
| **Antizipations-Engine** | Agent sagt voraus was du brauchen wirst |
| **Workflow-Builder** | Visueller Builder im Dashboard |
| **Multi-Agent-Koordination** | Agenten kommunizieren untereinander |
| **Mandanten-Self-Service** | Mandanten konfigurieren eigene Agent-Präferenzen |
| **Analytics Dashboard** | ROI-Tracking: Eingesparte Stunden, Kosten pro Mandant |
| **White-Label App** | Mandanten bekommen eigene App-Version |

---

## 9. Der Business Case — Warum Level 3 alles verändert

### Eingesparte Zeit pro KMU-Chef (konservativ geschätzt)

| Aufgabe | Ohne Agent | Mit Ambient Agent | Ersparnis |
|---------|-----------|-------------------|-----------|
| E-Mail-Triage (Morgen) | 45 Min. | 5 Min. (Briefing prüfen) | 40 Min. |
| Routine-Antworten | 60 Min./Tag | 10 Min. (Reviews) | 50 Min. |
| Fristen-Management | 30 Min./Tag | 0 Min. (automatisch) | 30 Min. |
| Termin-Koordination | 20 Min./Tag | 5 Min. (Genehmigungen) | 15 Min. |
| Dokumenten-Ablage | 30 Min./Tag | 5 Min. (Scanner + Auto) | 25 Min. |
| **GESAMT** | **~3 Std./Tag** | **~25 Min./Tag** | **~2,5 Std./Tag** |

**2,5 Stunden pro Tag × 220 Arbeitstage = 550 Stunden pro Jahr** eingesparte Produktivzeit für EINEN KMU-Chef. Bei einem Stundensatz von 150€ (Steuerberater/Anwalt) ist das ein Wert von **82.500€ pro Jahr**.

### Pricing-Implikation

Bei diesem Wert sind monatliche Preise von **€299-499/Monat** für die volle Ambient-Agent-Suite absolut gerechtfertigt — das ist weniger als eine Teilzeit-Bürokraft und liefert 24/7-Verfügbarkeit.

---

## 10. Die Kern-Erkenntnis von Level 3

**Level 2 hat einen besseren OpenClaw gebaut. Level 3 baut etwas was OpenClaw niemals sein kann.**

OpenClaw ist ein Chat-Bot auf Steroiden — du musst ihm sagen was er tun soll. Agent One Level 3 ist ein **digitaler Mitarbeiter der mitdenkt** — er überwacht, antizipiert, handelt und fragt nur wenn nötig.

Die drei Säulen die das ermöglichen:

1. **Ambient Agent Framework** — LangGraph Cron Jobs + Event-Driven Triggers + Intelligentes Notification-Routing = Der Agent arbeitet 24/7 im Hintergrund

2. **Progressive Autonomie** — Trust Scores + Kontext-Sensitivität + Lernende Korrekturen = Der Agent verdient sich Freiheit durch bewiesene Zuverlässigkeit

3. **Die App als Kommandozentrale** — Push Notifications + Biometrie + Scanner + Voice + On-Device AI = Die Brücke zwischen Mensch und Agent, überall und jederzeit

**Das ist die Zukunft von KI im deutschen Mittelstand: Nicht "Frag die KI" — sondern "Die KI arbeitet für dich."**

---

*Quellen: LangChain Ambient Agents Blog (Jan 2025), LangChain UX for Agents Part 2, LangGraph Cron Jobs Docs, VentureBeat Ambient Agents Interview, McKinsey Agentic AI Advantage (Jun 2025), Expo SDK 52 Docs, React Native ExecuTorch (Software Mansion), Vercel AI SDK for Expo, CIO Taming AI Agents (Sep 2025), Proactive AI Agent Survey (IJCESEN 2025)*
