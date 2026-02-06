# MCP Server Konfiguration

## Benötigte MCP Server

### 1. Linear (Projektmanagement)
```bash
claude mcp add linear -- npx -y @anthropic/linear-mcp-server
# Env: LINEAR_API_KEY=lin_api_IfJEy02O4PI6SqnqZMRav9UlhT6h4Cd5oZn86D3pxxx
```

### 2. GitHub (Code Repository)
```bash
claude mcp add github -- npx -y @modelcontextprotocol/server-github
# Env: GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxx
```

### 3. Playwright (E2E Testing)
```bash
claude mcp add playwright -- npx -y @anthropic/playwright-mcp-server
```

### 4. shadcn/ui (UI Komponenten)
```bash
claude mcp add shadcn -- npx -y shadcn-mcp-server
```

### 5. Coolify (Deployment)
```bash
claude mcp add coolify -- npx -y coolify-mcp-server
# Env: COOLIFY_API_TOKEN=xxxxx
# Env: COOLIFY_BASE_URL=https://coolify.deinedomain.de
```

## Prüfen ob MCPs aktiv sind
```bash
claude mcp list
```
