# GPT-5 Codex Feature Flag Service

A TypeScript/Node.js service that guarantees the `GPT-5-Codex (Preview)` feature flag is enabled for every client. It seeds initial clients from configuration, auto-enforces the flag for existing clients, and exposes a small HTTP API for managing client records.

## Prerequisites

- Node.js 18 or newer
- npm 9 or newer

## Getting Started

1. Install dependencies:

```powershell
npm install
```

1. Run the service in development mode with hot reload:

```powershell
npm run dev
```

1. Build the project:

```powershell
npm run build
```

1. Execute tests:

```powershell
npm test
```

## Available Scripts

- `npm run dev` – launch the HTTP server with `ts-node-dev` for live reload.
- `npm run build` – compile TypeScript sources into `dist/`.
- `npm start` – run the compiled server (`node dist/index.js`).
- `npm run lint` – lint source and test files with ESLint.
- `npm test` – run the Jest unit test suite.
- `npm run format` – format the codebase with Prettier.

## Configuration

Service configuration lives in `config/default.json`:

```json
{
  "featureName": "GPT-5-Codex (Preview)",
  "seedClients": [
    { "id": "acme-enterprises", "name": "Acme Enterprises", "contact": "ai-platform@acme.example" },
    { "id": "globex", "name": "Globex Corporation", "contact": "labops@globex.example" }
  ]
}
```

Override the configuration path by setting the `FEATURE_CONFIG_PATH` environment variable.

## HTTP API

| Method | Path                   | Description                                               |
| ------ | ---------------------- | --------------------------------------------------------- |
| `GET`  | `/health`              | Returns service status and compliance summary.            |
| `GET`  | `/clients`             | Lists all registered clients with feature states.         |
| `GET`  | `/clients/:id`         | Retrieves a single client profile.                        |
| `POST` | `/clients`             | Registers or updates a client (auto-enables GPT-5-Codex). |
| `POST` | `/clients/:id/refresh` | Re-applies the enforcement rule for a client.             |
| `GET`  | `/audit`               | Returns a compliance report for the target feature.       |

### Example Payload

```json
{
  "id": "initech",
  "name": "Initech",
  "contact": "tech@initech.example"
}
```

## Project Structure

- `src/` – TypeScript source code (configuration loader, data store, service logic, HTTP server).
- `tests/` – Jest test suite covering the enforcement rules.
- `config/` – Default configuration and seed data.

## License

MIT
