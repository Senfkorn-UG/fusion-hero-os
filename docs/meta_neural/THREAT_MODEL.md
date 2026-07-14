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
   `ConsentError` (HTTP 403). Denials are themselves audited. A grant-id
   mismatch produces exactly one `denied` audit event (never a misleading
   `granted`→`denied` pair).
3. **Subject identity.** `SubjectRef.derive` hashes the raw identifier (sha256)
   into a stable, opaque `subj_*` ID; the raw value is not recoverable from it.
4. **Audit read scope.** `audit_trail` is subject-scoped by default: a subject
   with `AUDIT_READ` sees only its own events (`AuditLog.events_for`).
   Cross-subject (global) reads are a distinct administrative capability that
   requires both `include_all=True` and a matching `admin_token` configured
   out-of-band; the capability is disabled when no token is set and is **never**
   plumbed through the HTTP API.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Covert profiling / surveillance | No connector auto-runs; ingest requires explicit purpose-scoped consent. No keylogging/screen/mic capture in this slice. |
| Private data leaking into public artifacts | Vault boundary + opaque IDs + synthetic fixtures + CI PII/secret scanner. A private, git-ignored denylist (`scripts/pii_denylist.local.yaml` or `$FUSION_PII_DENYLIST`) additionally blocks bare device identifiers, legal names and company names without embedding any real value in the committed scanner; denylist hits are blocking, never allowlist-exempt, and fail closed. |
| Silent consent expiry bypass | `ConsentGrant.is_active` checks retention window; expired/revoked grants fail closed. Detected expiry also purges derived state (see below). |
| Cross-subject audit disclosure | `audit_trail` is subject-scoped by default; global reads require a distinct, off-by-default admin token that is never exposed via HTTP. |
| Stale data after revocation/expiry | `revoke_consent` and `_purge_if_expired` deterministically drop the graph, snapshot, working memory and Hebbian caches and emit a non-PII `subject.purge` tombstone. |
| Concurrent mutation of shared service state | Per-subject state maps on the process-wide singleton are guarded by an `RLock`. |
| Audit tampering | Hash-chained `AuditLog` (`prev_hash`→`event_hash`); `verify()` detects any edit. |
| Non-reproducible optimization | Seeded RNG, recorded backend/seed/trace, brute-force cross-check for small problems. |
| Overstated capability claims | Honesty ledger + proof registry gate (BEWIESEN claims must cite passing tests). |

## GDPR-oriented properties

- **Data minimization:** only opaque IDs and declared dimensions are stored.
- **Purpose limitation:** `Purpose` enum; a grant authorizes exactly one purpose.
- **Explicit, revocable consent:** `grant()` / `revoke()`; default is denial.
- **Retention:** grants carry a retention window and expire.
- **Right to erasure:** `revoke_consent` (explicit) and `_purge_if_expired` /
  `sweep_expired` (retention expiry) deterministically remove the subject's
  graph, snapshot, working-memory space and Hebbian association memory
  (secondary indexes/caches). A minimal, non-PII `subject.purge` tombstone is
  appended as lawful evidence of deletion; no subject content is retained.
- **Privacy by default:** local-only, fail-closed vault, no covert connectors.

## Archive anchor key derivation (v10, archiv_version 2.0)

`scripts/archiv_anchor_uncommitted.py` derives its GPG passphrase with a
versioned, memory-hard **scrypt** KDF — not a fast `sha256(salt)`.

- **Key derivation (KDF):** `passphrase = base64(scrypt(secret, salt, n=16384,
  r=8, p=1, dklen=32))`. The `secret` is an explicit
  `FUSION_ARCHIV_GPG_PASSPHRASE` or the neutral, identifier-free default
  (`fusion-hero-os|archiv|v10`). A fresh random 16-byte `salt` is generated per
  archive and stored — **non-secret** — in the `manifest.json` `kdf` block
  alongside the parameters so recovery is self-describing. Neither the secret
  nor the derived passphrase is ever logged or persisted.
- **Integrity hashing is separate:** SHA256 over the (non-secret) file bytes is
  used only for integrity and lives in a distinctly named helper
  (`_content_digest`) and the manifest `sha256`/`manifest_sha256` fields. It is
  never applied to secret/credential material.
- **Pre-v10 archives** were anchored with a historical salt that embedded a
  device/tailnet identifier and a weak `sha256(salt)` derivation. That value
  has been removed from the public tree and is **not** reproduced anywhere in
  the repository.
- **Legacy migration:** the former `--legacy-salt` write/derivation path and the
  `FUSION_ARCHIVE_LEGACY_SALT` variable have been removed. Existing v1 archives
  remain recoverable read-only via their own bundled `RECOVER.sh`; no new v1
  archive is ever written.

## Out of scope for Stage-1 (planned)

- Durable encrypted persistence and vault transport.
- Per-field cryptographic deletion proofs.
- Rate-limiting / auth on the HTTP surface (currently local-only).
