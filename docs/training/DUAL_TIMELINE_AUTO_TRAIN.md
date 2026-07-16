# Dual-Timeline Auto-Training — real t ∥ imaginary τ

**Platform:** Fusion Hero OS v10.0.0  
**Policy:** pseudo_inhouse_only · freemium=false  
**Config:** `training_dual_timeline.yaml`  
**Code:** `fusion_hero_os/core/dual_timeline_training.py`

## Principle

Auto-training scans **all available** knowledge files and places every sample on **two parallel timelines**:

| Axis | Symbol | Meaning |
|------|--------|---------|
| **Real time** | \(t\) | File mtime (UTC chronology) |
| **Imaginary time** | \(\tau \in [0,1]\) | Structural depth (layer, path, modality, Geltung markers) |

\(\tau\) is a **Modell** of Wick-parallel / structural time — not a physics proof of imaginary time.  
Consistency = the same corpus can be walked as **history** and as **architecture** without missing axes.

```
files ──scan──► events(t, τ)
                    │
                    ▼
              samples JSONL
              timeline_dual.json  (real_timeline ∥ imaginary_timeline)
              consistency_report.json
```

## Run

```powershell
python scripts/auto_train_dual_timeline.py
# or
python -m fusion_hero_os.core.dual_timeline_training
```

API (Dashboard :8000):

- `GET /api/training/dual-timeline/status`
- `POST /api/training/dual-timeline/run`
- `GET /api/training/dual-timeline/catalog`

## Outputs

| Path | Content |
|------|---------|
| `~/.fusion/training/dual_timeline/samples_dual_timeline.jsonl` | training pairs with t + τ |
| `~/.fusion/training/dual_timeline/timeline_dual.json` | dual indices |
| `~/.fusion/training/dual_timeline/consistency_report.json` | consistency heuristics |
| `docs/training/dual_timeline_training.latest.json` | repo-visible summary |

## Sample shape

```json
{
  "prompt": "[t=2026-07-15T… · τ=0.42 · L2] Erkläre aus …",
  "response": "…",
  "source": "docs/…",
  "t_real": 1784…,
  "tau": 0.42,
  "timeline": "dual",
  "layer": 2
}
```

## Honesty

- \(\tau\)-mapping is **Modell** (V3.3).  
- Does not claim physical imaginary-time identity with cosmology.  
- Parallelism is operational: two sort orders, one corpus, consistency checks.
