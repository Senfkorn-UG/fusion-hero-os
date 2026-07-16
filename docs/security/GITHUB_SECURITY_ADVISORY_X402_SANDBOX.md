# Security advisory (lab) — x402 control necessity

**Type:** Defensive security audit evidence (sandbox)  
**Scope:** Local mock only · **no** third-party systems · **no** exploit payloads  
**Budget frame:** ≤ €500 (lab used €0 on-chain; remainder for optional external human review)  
**Status:** Authorized local audit artifact for Fusion Hero OS

## Summary

We verified in a **closed sandbox** that missing x402-style controls enable grant-abuse *classes* (replay, pre-finality grant, binding swap, unverified payment, cacheable paid body, non-allowlisted resource). With controls enabled, the same mock **rejects** those paths.

This is **not** a claim that any specific live facilitator is compromised.

## Affected (lab model)

- Mock resource server implementing an HTTP-402-like payment handshake
- Configuration flags corresponding to gates `G_*` in `x402_hackability.yaml`

## Evidence

```powershell
python -m fusion_hero_os.core.x402_sandbox_audit --budget-eur 500
python -m fusion_hero_os.core.x402_hackability_audit --audit
```

Artifacts:

- `~/.fusion/alerts/x402_sandbox_evidence.json`
- `~/.fusion/alerts/X402_SANDBOX_AUDIT_PROOF.md`
- `docs/security/x402_sandbox_proof.summary.json`

## Severity (lab)

| Case | Severity | Control |
|------|----------|---------|
| Replay multi-grant | Critical | nonce/paymentId single-use |
| Grant before finality | High | finality before 200 |
| Payee/resource swap | Critical | server-side binding |
| Unverified header | High | facilitator verify required |
| Public cache paid body | High | Cache-Control no-store |
| Sybil/non-allowlisted URL | Medium | agent allowlist |

## Recommendation

Do not integrate x402 as source-of-truth for secrets/MasterSeed until gates are green. Keep Fusion policy: **monitor + warn**.

## References (public research)

- x402 Foundation / x402.org
- Five Attacks on x402 (arXiv 2026)
- Halborn / industry risk notes on 402 micropayments

## Propagation

GitHub: **documentation and evidence only** in this repository. No attack tooling is published.
