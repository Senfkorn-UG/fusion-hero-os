# Meta-Neural Vertical Slice — Threat Model & Privacy

Scope: the `fusion_hero_os.meta` package and its CI PII gate. Stage-1 is
local-only and in-memory; no network persistence is enabled by default.

## Assets

- Subject data (never stored in the public repo; only opaque `subj_*` IDs).
- Consent grants and the append-only audit log.
- Graph snapshots (must contain no private personal data).

## Trust boundaries

1. **Public repo vs. private vault** (`fusion-hero-os` vs `fusion-hero-vault`).
   The public repo ships interfaces, schemas, opaque IDs and synthetic fixtures
   only. `NullVaultResolver` is the default and **fails closed**
   (`VaultUnavailableError`) when no vault is configured. Private trait data must
   never enter graph snapshots or logs.
2. **Consent gate.** Every ingest / activation / association / optimization /
   persistence path calls `_require(...)`; a missing or mismatched grant raises
   `ConsentError` (HTTP 403). Denials are themselves audited.
3. **Subject identity.** `SubjectRef.derive` hashes the raw identifier (sha256)
   into a stable, opaque `subj_*` ID; the raw value is not recoverable from it.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Covert profiling / surveillance | No connector auto-runs; ingest requires explicit purpose-scoped consent. No keylogging/screen/mic capture in this slice. |
| Private data leaking into public artifacts | Vault boundary + opaque IDs + synthetic fixtures + CI PII/secret scanner. |
| Silent consent expiry bypass | `ConsentGrant.is_active` checks retention window; expired/revoked grants fail closed. |
| Audit tampering | Hash-chained `AuditLog` (`prev_hash`→`event_hash`); `verify()` detects any edit. |
| Non-reproducible optimization | Seeded RNG, recorded backend/seed/trace, brute-force cross-check for small problems. |
| Overstated capability claims | Honesty ledger + proof registry gate (BEWIESEN claims must cite passing tests). |

## GDPR-oriented properties

- **Data minimization:** only opaque IDs and declared dimensions are stored.
- **Purpose limitation:** `Purpose` enum; a grant authorizes exactly one purpose.
- **Explicit, revocable consent:** `grant()` / `revoke()`; default is denial.
- **Retention:** grants carry a retention window and expire.
- **Deletion hooks:** `HebbianAssociationMemory.delete` / `delete_slot`, graph is
  rebuildable from consented input; no hidden secondary copies in this slice.
- **Privacy by default:** local-only, fail-closed vault, no covert connectors.

## Out of scope for Stage-1 (planned)

- Durable encrypted persistence and vault transport.
- Per-field cryptographic deletion proofs.
- Rate-limiting / auth on the HTTP surface (currently local-only).
