# Canonical Root Decision

**Decision:** the active/canonical package for the meta-neural slice and for
tests is `fusion_hero_os/` at the repository root.

## Evidence

- **Tests import it:** `tests/test_meta_neural.py` and
  `tests/test_meta_neural_api.py` import `fusion_hero_os.meta.*`.
- **Entrypoints:** existing runnable modules and CI reference `fusion_hero_os`.
- **Package presence:** `fusion_hero_os/` contains the live methodology,
  modules, and now the `meta` slice.

## Known stale artifacts (intentionally NOT changed in Stage-1)

- `src/normal_os/` is an older mirror/mesh tree; several files there duplicate
  root files (e.g. `mesh_connectors.yaml`). These were scrubbed for PII but not
  restructured.
- `pyproject.toml` uses `where=["src"]` and declares `normal_os.*` scripts.
  This does not match the canonical root but is left untouched to avoid breaking
  packaging/entrypoints for unrelated code. **Recommended Stage-2 fix:** align
  packaging to `fusion_hero_os/` (or make the layout explicit) in an isolated PR
  with full test coverage.

## Rationale

Changing packaging/layout is high-blast-radius and out of scope for a vertical
slice foundation. The slice is self-contained under `fusion_hero_os/meta` and is
fully importable/testable as-is.
