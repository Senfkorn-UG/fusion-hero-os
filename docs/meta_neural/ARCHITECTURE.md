# Meta-Neural Vertical Slice — Architecture

Status: Stage-1 foundation. Local-only, in-memory, consent-gated.

## Naming and honesty

"Meta-neural network" and "fractal" are **metaphors** for a typed,
multidimensional property graph plus simple activation/association dynamics.
This system is **not** conscious, **not** biological cognition, and **not**
quantum computing. Where the code borrows terms from neuroscience or physics
(J-space, Hebbian, spectral radius, annealing) it does so as an **analogy** and
implements a plain, inspectable mathematical object.

## Components (package `fusion_hero_os.meta`)

| Module | Responsibility | Key types |
|---|---|---|
| `consent.py` | Purpose-scoped, revocable consent + append-only hash-chained audit | `Purpose`, `ConsentGrant`, `AuditLog`, `ConsentStore` |
| `vault.py` | Public/private boundary; opaque subject IDs; fail-closed resolvers | `SubjectRef`, `NullVaultResolver`, `InMemoryVaultResolver` |
| `graph.py` | Typed, versioned property graph + immutable content-addressed snapshots | `GraphSchema`, `PropertyGraph`, `GraphSnapshot`, `Provenance` |
| `working_memory.py` | Activation vectors with capacity clamp + geometric decay | `WorkingMemorySpace`, `ActivationReport` |
| `hebbian.py` | Consent-scoped sparse association weights | `HebbianConfig`, `HebbianAssociationMemory` |
| `coupling.py` | Jacobian (finite-diff), spectral radius, contraction test, fixed-point iteration | `is_contraction`, `iterate_to_fixed_point` |
| `qubo_bridge.py` | Bridge graph state to QUBO/Ising solver + classical fallback | `build_qubo`, `solve_qubo`, `QUBOResult` |
| `pipeline.py` | End-to-end orchestration, every step consent-gated | `MetaNeuralService` |
| `api.py` / `cli.py` | One minimal vertical-slice surface (FastAPI + argparse) | `create_app`, `run_demo` |
| `schemas.py` | pydantic v2 request/response contracts | — |
| `fixtures/` | Synthetic neutral fixture (no real personal data) | `load_neutral_fixture` |

## Data flow (vertical slice)

```
consent.grant(purpose)
   -> ingest(neutral fixture)        # -> immutable GraphSnapshot (sha256 content hash)
   -> activate(working memory)       # capacity-clamped, decaying activation vector
   -> associate()                    # Hebbian update from co-activations
   -> analyze_convergence()          # contraction test on J = decay*(I+A)
   -> optimize()                     # QUBO/Ising select-k, seeded, classical fallback
   -> audit_trail()                  # verify hash chain, return events
```

Each arrow calls `MetaNeuralService._require(...)`, which fails closed if no
active grant matches the `(subject, purpose, grant_id)` tuple.

## Determinism / provenance

- Snapshots are content-addressed via canonical JSON (sorted keys, tight
  separators, ASCII), and the hash **excludes** provenance timestamps and
  insertion order so identical logical graphs hash equally.
- QUBO results carry `source_snapshot` (the snapshot hash), `backend`, `seed`,
  `objective`, `constraints`, and a step trace — reproducible under a fixed seed.

## Canonical root

The active package is `fusion_hero_os/` (confirmed by CI workflows, entrypoints,
test imports). `src/normal_os/` and parts of `pyproject.toml` (`where=["src"]`,
`normal_os.*` scripts) are **stale** and intentionally left untouched in Stage-1
to avoid breaking unrelated code. See `CANONICAL_ROOT.md`.
