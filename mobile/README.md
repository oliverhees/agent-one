# ALICE Mobile App

React Native App für den ALICE ADHS Coach mit Expo.

## Tech Stack

- **React Native + Expo SDK 54** (managed workflow)
- **Expo Router** (file-based navigation)
- **NativeWind v4** (Tailwind CSS für React Native)
- **Zustand** (Client State Management)
- **TanStack Query v5** (Server State / Caching)
- **React Hook Form + Zod** (Formulare + Validierung)
- **TypeScript** (strict mode)
- **Expo SecureStore** (Token Storage)

## Entwicklung starten

```bash
# Dependencies installieren
npm install

# Expo Dev Server starten
npm start

# Android
npm run android

# iOS (nur auf macOS)
npm run ios

# Web
npm run web
```

## Projektstruktur

```
mobile/
├── app/                    # Expo Router (file-based navigation)
│   ├── (auth)/            # Auth-Screens (Login, Register)
│   └── (tabs)/            # Tab-Navigation (Chat, Tasks, Brain, Dashboard, Settings)
├── components/
│   ├── ui/                # Reusable UI Komponenten
│   └── auth/              # Auth-spezifische Komponenten
├── hooks/                 # Custom Hooks
├── stores/                # Zustand Stores
├── services/              # API Services
├── types/                 # TypeScript Types
├── utils/                 # Utilities
└── constants/             # Config & Konstanten
```

## Features (Phase 1)

- ✅ Login & Registrierung
- ✅ Token-basierte Authentifizierung (JWT)
- ✅ Auto-Refresh Token
- ✅ SecureStore für Token-Speicherung
- ✅ Tab-Navigation mit 5 Tabs
- ⏳ Chat (Placeholder)
- ⏳ Task Management (Placeholder)
- ⏳ Brain/Knowledge Base (Placeholder)
- ⏳ Dashboard (Placeholder)

## Auth Flow

1. User öffnet App
2. `_layout.tsx` lädt gespeicherte Tokens aus SecureStore
3. Falls Tokens vorhanden → `/me` Endpoint aufrufen → User-Daten laden
4. Falls Tokens ungültig oder nicht vorhanden → Login Screen
5. Nach Login/Register → Tokens in SecureStore speichern → Redirect zu Chat

## API Integration

Die App kommuniziert mit dem FastAPI Backend unter `http://localhost:8000/api/v1`.

### Endpoints

- `POST /auth/login` - Login
- `POST /auth/register` - Registrierung
- `POST /auth/refresh` - Token Refresh
- `GET /auth/me` - User-Daten

### Error Handling

- 401 Unauthorized → Auto-Refresh Token
- Falls Refresh fehlschlägt → Logout & Redirect zu Login

## Environment Variables

Konfiguration in `constants/config.ts`:

```typescript
const ENV = {
  dev: { apiUrl: "http://localhost:8000/api/v1" },
  staging: { apiUrl: "https://staging-api.alice.example.com/api/v1" },
  prod: { apiUrl: "https://api.alice.example.com/api/v1" },
};
```

## Scripts

```bash
# Starten
npm start

# Type Check
npx tsc --noEmit

# Linting (falls ESLint konfiguriert)
npm run lint
```

## Nächste Schritte

1. Chat-Feature implementieren (WebSocket + Messages)
2. Task-Management implementieren
3. Knowledge Base (Brain) implementieren
4. Push Notifications
5. Offline-Support
6. E2E Tests mit Detox
