# appkit-analytics

A Databricks App powered by [AppKit](https://developers.databricks.com/docs/appkit/v0/), featuring React, TypeScript, and Tailwind CSS.

**Enabled plugins:**
- **Analytics** -- SQL query execution against Databricks SQL Warehouses
- **Server** -- Express HTTP server with static file serving and Vite dev mode

## Prerequisites

- Node.js v22+ and npm
- Databricks CLI (for deployment)
- Access to a Databricks workspace

## Databricks Authentication

### Local Development

For local development, configure your environment variables by creating a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set the environment variables you need:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_APP_PORT=8000
# ... other environment variables, depending on the plugins you use
```

### CLI Authentication

The Databricks CLI requires authentication to deploy and manage apps. Configure authentication using one of these methods:

#### OAuth U2M

Interactive browser-based authentication with short-lived tokens:

```bash
databricks auth login --host https://your-workspace.cloud.databricks.com
```

This will open your browser to complete authentication. The CLI saves credentials to `~/.databrickscfg`.

#### Configuration Profiles

Use multiple profiles for different workspaces:

```ini
[DEFAULT]
host = https://dev-workspace.cloud.databricks.com

[production]
host = https://prod-workspace.cloud.databricks.com
client_id = prod-client-id
client_secret = prod-client-secret
```

Deploy using a specific profile:

```bash
databricks bundle deploy --profile production
```

**Note:** Personal Access Tokens (PATs) are legacy authentication. OAuth is strongly recommended for better security.

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development

Run the app in development mode with hot reload:

```bash
npm run dev
```

The app will be available at the URL shown in the console output.

### Build

Build both client and server for production:

```bash
npm run build
```

This creates:

- `dist/server.js` - Compiled server bundle
- `client/dist/` - Bundled client assets

### Production

Run the production build:

```bash
npm start
```

## Code Quality

There are a few commands to help you with code quality:

```bash
# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix

# Formatting
npm run format
npm run format:fix
```

## Deployment with Databricks Asset Bundles

The workspace comes from your CLI profile; the warehouse is a bundle variable (no IDs are committed):

```bash
export BUNDLE_VAR_sql_warehouse_id=<WAREHOUSE_ID>
databricks apps deploy -t dev --profile <PROFILE>    # validate, deploy, start, print URL
databricks apps deploy -t prod --profile <PROFILE>   # prod: run from CI as a service principal
```

**Permissions.** The bundle grants the app's service principal `CAN_USE` on the warehouse and requests the `sql` user API scope. `config/queries/daily_trips.obo.sql` runs as the signed-in user (the `.obo.sql` suffix), so they need `SELECT` on `samples.nyctaxi.trips`. Name a query `*.sql` (no `.obo`) to run it as the service principal with a shared cache.

> **Restarting a stopped app:** apps stop after a period of inactivity. To start one again without redeploying, run `databricks apps start <APP_NAME>`.

## Project Structure

```
* client/          # React frontend
  * src/           # Source code
  * public/        # Static assets
* server/          # Express backend
  * server.ts      # Server entry point
  * routes/        # Routes
* shared/          # Shared types
* config/          # Configuration
  * queries/       # SQL query files
* databricks.yml   # Bundle configuration
* app.yaml         # App configuration
* .env.example     # Environment variables example
```

## Tech Stack

- **Backend**: Node.js, Express
- **Frontend**: React.js, TypeScript, Vite, Tailwind CSS, React Router
- **UI Components**: Radix UI, shadcn/ui
- **Databricks**: AppKit SDK

---

&copy; 2026 Databricks, Inc. All rights reserved. The source in this example is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below. Data: Databricks sample dataset `samples.nyctaxi.trips`.

| library | description | license | source |
|---|---|---|---|
| react, react-dom | UI library | MIT | https://github.com/facebook/react |
| react-router | Client-side routing | MIT | https://github.com/remix-run/react-router |
| lucide-react | Icons | ISC | https://github.com/lucide-icons/lucide |
| tailwind-merge, clsx | CSS class utilities | MIT | https://github.com/dcastil/tailwind-merge |
| zod | Schema validation | MIT | https://github.com/colinhacks/zod |
| next-themes, embla-carousel-react, react-resizable-panels, tw-animate-css, tailwindcss-animate | UI helpers used by AppKit UI | MIT | npm |
