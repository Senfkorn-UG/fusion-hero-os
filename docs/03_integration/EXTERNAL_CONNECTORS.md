# External Connector Integration

Fusion Hero OS integrates the currently connected external services through a
single spec-driven adapter layer. All traffic is routed **server-side** through
the runtime `external-tool` CLI (and the authenticated `gh` CLI for GitHub), so
no credentials ever live in this repo or reach the frontend.

## Connectors

| Local key   | Source ID           | Transport      | Read-only health probe          |
|-------------|---------------------|----------------|---------------------------------|
| `slack`     | `slack_direct`      | external-tool  | `slack_search_channels`         |
| `jira`      | `jira_mcp_merge`    | external-tool  | `jira__get_current_user`        |
| `files`     | `files`             | external-tool  | `search_files_v2`               |
| `gcal`      | `gcal`              | external-tool  | `search_calendar`               |
| `github`    | `github_mcp_direct` | **gh CLI**     | `get_me` (`gh api user`)        |
| `finance`   | `finance`           | external-tool  | `finance_market_sentiment`      |
| `opticodds` | `opticodds`         | external-tool  | `opticodds GET /sports`         |

## Design

- **Registry / adapter layer** — `src/normal_os/connectors/`:
  - `specs.py` — declarative `ConnectorSpec`s: capabilities, required args, a
    `mutating` flag per tool, and one safe read-only `HealthProbe`.
  - `external_tool_client.py` — thin wrapper over the `external-tool` CLI;
    normalises failures into `ExternalToolError` (`auth_required`,
    `rate_limited`, `connector_error`, `transport_error`, `timeout`,
    `not_available`) and scrubs secrets from any surfaced message.
  - `external_connector.py` — `ExternalToolConnector`: validates inputs against
    the spec, refuses unknown tools, blocks mutating tools unless
    `allow_mutating=True`, and routes GitHub through `gh`.
  - `registry.py` — lazy `ConnectorRegistry` with `status()`, `capabilities()`,
    and concurrent `health_check_all()`. Construction does **no** network/CLI
    traffic, so startup is robust when a service is down.

- **Safety** — health checks and startup probes only ever call the read-only
  probe; no irreversible action runs on boot. Mutating tools (send message,
  create issue, send email, OpticOdds `POST`, …) require an explicit opt-in.

## HTTP API (dashboard)

Exposed by `03_Code/Dashboard/connectors_routes.py`:

- `GET  /api/connectors` — list + status of all connectors
- `GET  /api/connectors/{name}` — status + capability metadata
- `GET  /api/connectors/{name}/health` — run the safe read-only probe
- `POST /api/connectors/{name}/call` — `{ "tool", "arguments", "allow_mutating" }`

## Local startup

```bash
# One-off read-only health probe of every connector:
python start_fusion_hero.py --connectors-health

# Full launcher (bridge + dashboard); probes connectors after dashboard boot:
python start_fusion_hero.py --with-dashboard
# Dashboard: http://127.0.0.1:8000  → GET /api/connectors

# Or run the dashboard directly:
cd 03_Code/Dashboard && python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### Configuration

- No secrets required in `.env`; the `external-tool` CLI resolves connector auth
  on the server side.
- Optional override `FUSION_EXTERNAL_TOOL_BIN` — path to the `external-tool`
  binary if it is not on `PATH` (useful for tests / non-standard installs).

## Tests

- `tests/test_external_connectors.py` — registry, routing, validation,
  mutating-tool gating, and failure handling (mocked CLI, fully offline).
- Live smoke tests run only when `FUSION_LIVE_CONNECTOR_TESTS=1` and the
  `external-tool` binary is present.
