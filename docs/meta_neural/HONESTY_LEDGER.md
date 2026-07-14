# Meta-Neural Vertical Slice — Honesty Ledger

This ledger states plainly what is built, what is partial, and what is planned.
It exists so that no capability is overstated.

## Framing (read first)

- **"Fractal" / "meta-neural" are metaphors.** The implementation is a typed
  property graph with simple activation and association dynamics. It is **not**
  consciousness, sentience, or biological cognition.
- **Not quantum.** The QUBO/Ising bridge uses classical simulated annealing (and
  optional classical Rust/`qb_qubo` backends). No quantum hardware or claim.
- **"J-space"** is used as an analogy for a bounded activation vector space; see
  `working_memory.py`.

## Capability status

| Capability | Status | Evidence / Notes |
|---|---|---|
| Typed, versioned property graph + immutable snapshots | **Implemented** | `graph.py`; `test_meta_neural.py::test_snapshot_is_immutable_and_content_addressed`, `::test_deterministic_serialization_ignores_timestamp_and_order` |
| Deterministic, content-addressed serialization | **Implemented** | `GraphSnapshot.to_canonical_json` / `content_hash` |
| Consent: purpose-scoped, revocable, retention, fail-closed | **Implemented** | `consent.py`; `::test_consent_grant_authorize_revoke_expiry`, `::test_purpose_limitation` |
| Append-only, tamper-evident audit log | **Implemented** | `AuditLog` hash chain; `::test_audit_chain_tamper_detection` |
| Public/private vault boundary, opaque subject IDs, fail-closed | **Implemented** | `vault.py`; `::test_null_vault_fails_closed`, `::test_subject_ref_is_opaque_and_stable` |
| Working memory: capacity clamp + geometric decay + reportability | **Implemented** | `working_memory.py`; `::test_working_memory_*` |
| Hebbian association memory (learn/decay/clamp/delete/reproducible) | **Implemented** | `hebbian.py`; `::test_hebbian_update_forget_delete_reproducible` |
| Coupling: finite-diff Jacobian, spectral radius, contraction test | **Implemented** | `coupling.py`; `::test_jacobian_dimensions_and_fd_agreement`, `::test_banach_contraction_detection` |
| Fixed-point convergence (contraction case only) | **Implemented (bounded claim)** | `::test_fixed_point_iteration_converges_for_contraction`. We claim convergence **only** under a sufficient local contraction condition — **no** general nonlinear convergence guarantee. |
| QUBO/Ising bridge with classical fallback + provenance | **Implemented** | `qubo_bridge.py`; `::test_qubo_bridge_determinism_and_provenance`, `::test_qubo_bridge_matches_brute_force_small` |
| One API/CLI vertical slice (consent→…→audit) | **Implemented** | `api.py`, `cli.py`; `test_meta_neural_api.py`, `::test_pipeline_happy_path` |
| CI PII/secret scanning gate + allowlist | **Implemented** | `scripts/check_pii_scanner.py`; `test_pii_scanner.py`; `.github/workflows/pii-scan.yml` |
| TS contract alignment | **Partial** | `src/lib/meta/contracts.ts` mirrors pydantic by hand. Generated OpenAPI types are **planned**. |
| Rust / `qb_qubo` / numba accelerated backends | **Partial** | Wired as optional backends with classical fallback; not exercised locally (numba/numba-deps unavailable on the local Python 3.14). Verified on CI Python 3.11/3.12 environment. |
| Durable/encrypted persistence + vault transport | **Planned** | Stage-1 is in-memory only. |
| HTTP auth / rate-limiting | **Planned** | Local-only surface for now. |
| Persona package rename (`alte_frau_95g`) | **Planned (Stage-2)** | Import-breaking; deferred. Allowlisted + non-blocking warning in Stage-1. |

## Proof registry

Nine `META-*` claims were added to `proof_registry.yaml`, each marked `BEWIESEN`
and citing the passing pytest node IDs above. Any claim without a passing test
must be `OFFEN` (open) or `WIDERLEGT` (refuted), never `BEWIESEN`.
