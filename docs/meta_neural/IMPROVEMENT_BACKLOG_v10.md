# Fusion Hero OS — Improvement Backlog (engineering assessment)

> **Stand:** v10.0.0 · 2026-07-17
> **Author:** Claude Fable 5 (engineering review)
> **Honesty note:** This was requested as "ask Fable 5 *and* Mythos." Claude
> Mythos 5 runs on the *same underlying model* as Fable 5 — it is not an
> independent second reviewer, so a genuine "Mythos said X vs Fable said Y"
> split would be fabricated. This list is therefore a single honest
> assessment, grounded in problems actually observed while working the repo
> (CI logs, test failures, scanner output), not invented findings.

The repo has genuinely good bones — the "honest status" culture, the
Proof-Registry ↔ pytest binding, the Dependency-Atlas gate, the operator
identity/PII membranes. The items below are where reality currently
diverges from the intent those systems encode.

---

## P0 — CI gates that don't actually gate

These are the highest-leverage fixes: several "gates" are green-theatre or
permanently red, so they no longer protect `main`.

1. **`pyright` gate is non-enforcing (`|| true`) yet still fails loudly.**
   `fusion-hero-build.yml` runs `python -m pyright` which reports real errors
   in `mugen_tsuky_chan.py`, `schwerkraftserver.py`, `universal_llm_router.py`
   ("Object of type str is not callable", return-type mismatches). Either fix
   the ~4 real type errors and make the gate enforcing, or drop the gate. A
   gate that's always red trains everyone to ignore it.

2. **Four tests fail on every run and merges proceed anyway.**
   `test_asset_persona_paths`, `test_operator_identity`,
   `test_persona_scanner`, `test_registry::test_stub_modules_are_marked_as_stub_not_loaded`.
   These encode the Stage-B depersonalisation contract and the stub/loaded
   registry contract — both currently violated in `main`. They should be made
   green (by finishing the refactor) or explicitly `xfail` with a tracking
   issue, not left as permanent red noise.

3. **`pii-scan` fails on real findings but never blocks a merge.**
   Legal name (now fixed), real Supabase project refs and a real Tailscale
   MagicDNS host were sitting in public source for the entire session because
   the scan is advisory. For a *public* repo this is the most important gate to
   make enforcing.

4. **`check_doc_versions` red on two `mainframe-laden/SKILL.md` files.**
   Same two files also trip the persona scanner — they're duplicated at
   `.grok/skills/…` and `01_Framework/skills/…`. Version-stamp them or exclude
   the mirror copy.

## P1 — architecture debt that keeps re-breaking CI

5. **Finish (or formally pause) the Stage-B depersonalisation.**
   `comaedchen_identity.py` — a module *about* a persona — lives inside
   `fusion_hero_os/`, the package declared persona-free, so the persona
   scanner flags it as a regression forever. Decide: move it out of the
   operative package, or adjust `PERSONA_BLOCKING_PATH_PREFIXES`. Right now
   it's neither, so the gate can never go green.

6. **`fusion_hero_os/` lives at the repo root, outside `src/`.**
   It's only importable via a `pythonpath=["."]` shim; bare `pytest` couldn't
   find it until that was added. Long-term, move it under `src/` with the rest
   or make the packaging intentional and documented.

7. **Orphaned submodule gitlink `03_Code/Rust_Prototype/alte_frau_rust`.**
   Removed from the tree once already, but `git submodule foreach` in CI still
   prints `fatal: No url found for submodule path …` on every checkout. There's
   a residual gitlink/`.gitmodules` mismatch to clean up for good.

8. **A dead duplicate `LLMRouter` in `legacy_sources/normalOS/`.**
   It shadows the real `src/normal_os/llm/router.py` and makes CodeQL raise a
   false "wrong argument name" alert. Either delete the legacy copy or exclude
   `legacy_sources/` from CodeQL's path filter.

## P2 — hygiene / smaller wins

9. **Ruff reports ~72 unused imports / unused locals / placeholder f-strings**
   across `x402_*`, `meta/*`, `providers/base.py`, `modules/*`. `ruff check
   --fix` clears ~58 automatically; do it in one sweep.

10. **Sandbox/runtime telemetry is committed and regenerates constantly.**
    `docs/**/*.summary.json`, `last_activation.summary.json`, etc. get rewritten
    on every run with fresh timestamps and machine-local paths (even leaking a
    `C:\Users\…` path once). These should be git-ignored generated artifacts,
    not tracked files.

11. **Mesh topology still in public source (non-blocking).**
    Bare node hostnames (`desktop-kpki9e4`) and the tailnet suffix
    (`tail391adb.ts.net`) remain in `mesh_service_coordination.yaml`,
    `mesh_os_port.yaml`, `dns_tor_stack.yaml`. If the public repo is meant to be
    a clean skeleton, these should be placeholder/env-driven too — but they're
    load-bearing config, so it's a deliberate refactor, not a redaction.

12. **Deprecation debt.** FastAPI `@app.on_event` (→ lifespan handlers) and the
    end-of-life `google.generativeai` package (→ `google.genai`) both warn on
    every test run. Cheap to modernise before they become breakage.

13. **Branch sprawl.** ~30 remote branches, most 0 commits ahead of `main`
    (fully merged). Prune the stale merged pointers; keep `archive/*` as the
    intentionally-preserved history the strategy doc describes.

## Kept as strengths (don't "fix" these)

- Proof-Registry ↔ pytest node binding (`check_proof_registry.py --run`).
- Dependency-Atlas import/cycle gate.
- The PLATZHALTER-STUB honesty convention — real stubs that say they're stubs.
- Operator-identity + god-layer-seal membranes keeping the legal name local.
- The multimodal extractor's honest `unsupported_container` status.

---

*Prioritise P0 first: making the existing gates actually enforce would catch
most of the P1/P2 items automatically going forward.*
