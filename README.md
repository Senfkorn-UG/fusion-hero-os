# normalOS

**Practical AI Agent Orchestration Framework**

Clean, production-oriented implementation of multi-LLM routing, QUBO-based task optimization and a modern monitoring dashboard.

Written like a senior Python developer would have done it in March 2026.

## Features

- Clean multi-provider LLM router (OpenAI, Anthropic, Grok, local models via Ollama)
- QUBO optimization layer for task prioritization and resource allocation
- FastAPI-based dashboard with real-time status
- Strong typing with Pydantic v2
- Simple but extensible agent system
- Good defaults + full configurability

## Quick Start

```bash
git clone https://github.com/95guknow/normalOS.git
cd normalOS
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run dashboard
python -m normal_os.dashboard.app
```

Then open http://localhost:8000

## Architecture (March 2026 style)

```
normal_os/
├── core/           # Config, models, orchestrator
├── llm/            # Multi-provider router + clients
├── optimization/   # QUBO solver + task optimizer
├── agents/         # Agent definitions & registry
├── dashboard/      # FastAPI + simple frontend
└── utils/
```

## Tech Stack

- Python 3.12+
- Pydantic v2 + FastAPI
- httpx (async HTTP)
- dimod (QUBO modeling) + optional D-Wave
- pytest + ruff

## Configuration

All configuration via environment variables or `.env` file (Pydantic Settings).

## License
MIT