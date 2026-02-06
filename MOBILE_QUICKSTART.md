# ALICE Mobile App - Quick Start

## Setup abgeschlossen!

Das React Native Mobile Frontend wurde erfolgreich aufgesetzt.

## Starten

```bash
# In das mobile-Verzeichnis wechseln
cd mobile

# Expo Dev Server starten
npm start

# Dann:
# - QR-Code mit Expo Go App scannen (iOS/Android)
# - Oder 'a' drücken für Android Emulator
# - Oder 'i' drücken für iOS Simulator (nur macOS)
# - Oder 'w' drücken für Web
```

## Voraussetzungen

Das Backend muss laufen unter: `http://localhost:8000/api/v1`

```bash
# Backend starten (in separatem Terminal)
cd backend
uvicorn app.main:app --reload
```

## Erste Schritte in der App

1. App startet auf Login Screen
2. Registrieren → Name, E-Mail, Passwort eingeben
3. Nach erfolgreicher Registrierung → automatischer Login
4. Tab-Navigation nutzen (5 Tabs):
   - Chat (Placeholder)
   - Aufgaben (Placeholder)
   - Brain (Placeholder)
   - Dashboard (Placeholder)
   - Einstellungen (mit Logout)

## Features

- JWT-basierte Authentifizierung
- Auto-Refresh Token
- Sichere Token-Speicherung (SecureStore)
- Tab-Navigation
- Dark Mode Support
- TypeScript + Zod Validierung
- Tailwind CSS (NativeWind)

## Status

- ✅ Projekt Setup komplett
- ✅ Auth Flow implementiert
- ✅ Navigation implementiert
- ✅ UI Components erstellt
- ✅ TypeScript ohne Fehler
- ⏳ Chat Feature (Phase 2)
- ⏳ Task Management (Phase 2)
- ⏳ Brain/Knowledge Base (Phase 2)

## Troubleshooting

### Backend nicht erreichbar
```
Error: Network request failed
```
→ Backend starten: `cd backend && uvicorn app.main:app --reload`

### Expo Cache Probleme
```bash
npx expo start -c  # Mit Cache Clear
```

### TypeScript Errors
```bash
npx tsc --noEmit  # Type Check
```

## Dokumentation

Weitere Details in:
- `/mobile/README.md` - Vollständige Dokumentation
- `/mobile/SETUP.md` - Setup-Checkliste

## Next Steps

1. Backend-Endpoints für Chat implementieren
2. WebSocket-Verbindung für Live-Chat
3. Task-Management-Features
4. Knowledge Base Integration
5. Push Notifications
