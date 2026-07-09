# normalOS v0.5.0

Clean, explicit, production-oriented orchestration and optimization platform.

Extracted and normalized from the Fusion Hero OS Horkrux — all implicit patterns made explicit.

## Architecture (explicit)

- **core/**: Configuration, domain models, orchestrator
- **agents/**: BaseAgent + explicit Registry
- **optimization/**: QUBO solver with caching
- **llm/**: Multi-provider router
- **persistence/**: Async task store
- **executor/**: Async task execution engine (planned v0.5.1)
- **dashboard/**: FastAPI + HTMX
- **cli/**: Typer CLI

## Quickstart

```bash
uv sync
normalos --help
```