# Academia-aligned Training Curriculum v1

**Stand:** 2026-07-15  
**Account-Signal (Gmail):** Academia Premium → **Stephan Urban** (`stephan95g@…`)  
**Parallel track:** läuft neben Mesh-Service-Coordination + optional GKE inventory  

## Identity gate (wichtig)

| Quelle | Befund | Nutzung für Training |
|--------|--------|----------------------|
| Gmail `academia-mail.com` | Anrede **Stephan Urban**, Premium, Mentions, Reading-Recommendations | **primär** — Lesespur des Operators |
| Öffentliches Profil [independent.academia.edu/StephanUrban1](https://independent.academia.edu/StephanUrban1) | Interests: Body & Soul, Aristotle, Hellenistic, Plato, Ancient Greek; Uploads stark **HBV/HDV-Virologie** | **nur mit Vorbehalt** — hohe Wahrscheinlichkeit **Namenskollision** (andere „Stephan Urban“-Papers auto-geclaimt) |
| Phone filedrops (`~/.fusion/mesh/filedrops/inbound/android`) | leer; `phone_peer: null` | noch **kein** offener Profil-Export vom Handy |
| Inhouse `docs/Heroismus/`, Fusion Hero OS | Axiome I–IV, Sisyphos, CEC, Eudaimonia | **kanonischer** Trainings-Anker |

**Regel:** Gmail-Lesespur + Inhouse-Korpus steuern das Training. Virologie-Uploads auf dem öffentlichen Profil werden **nicht** als Eigenwerk des Operators übernommen, solange nicht manuell bestätigt.

## Lesespur-Cluster (aus Academia-Mails, Juli 2026)

### A — Existenzphilosophie / Bildung (dominant)
- Almut Furchert — *Das Stichwort: Existenz / Existieren*
- Michael Niehaus — *Existieren Sie bloß – oder leben Sie schon?*
- Diana Lohwasser — *Existenz bei Camus, Cioran und Lévinas*
- Csaba Olay — *Existenz bei Jaspers und Sartre*
- Thomas Wachtendorf — *Umriss einer existenzialistischen Ethik*
- Christian Tewes — *Existentielle Angst und ihre Verkörperung*
- Gianluca De Candia — *Pareyson / Jaspers*
- Andreas Cremonini — *schreibend sich selbst erfinden*
- Markus Wild — *Coetzee / Tiere / Existenzialismus* (bezogen auf Camus/Sisyphos)
- Marc Wittmann — *Zeit und Existenz*
- Peter Schüz, Matthias Wieser (Latour *Existenzweisen*), Benjamin Steiner

### B — Agentic AI / System security (sekundär, stark wachsend)
- *Towards trustworthy agentic AI* (safety, robustness, privacy, system security)
- *Meta-reasoning in autonomous agents*
- *Real-time … YOLOv11n on edge devices* (edge compute — Cluster-relevant)

### C — Historisch / Nebenstränge (Empfehlungen, nicht Fokus)
- Artemision / Ephesos (antike Religion) — schwächer gekoppelt an Heroismus-Kanon

## Mapping → Fusion Hero OS (Training-Targets)

| Academia-Cluster | Inhouse-Modul / Axiom | Trainingsziel |
|------------------|----------------------|---------------|
| Sisyphos / Camus / Absurd | Axiom IV CEC, PersistentSisyphosCycle | „Zufriedener Sisyphos“ = methodische Stabilität, nicht Tragödie |
| Existenz / Jaspers / Sartre | Axiom I 1st-Tier, Axiom III Psycholyse | Existenz als Integration, nicht Flucht in Transzendenz |
| Embodiment / Angst verkörpert | Axiom II Somatic | Körper als Hardware-Horkrux |
| Latour Existenzweisen | Layer-Registry / mesh segments | Jeder Connector = eigenes Existenzsegment im Mesh |
| Trustworthy agentic AI | Multi-Agent-Orchestration, Consent, Tarnkappe | Safety/privacy als Placement-Constraint L1 vs L3 |
| Meta-reasoning agents | heroic_core_orchestrator, PeerReview | Supervisor/Worker + 5-Dimensions-Review |
| Edge / YOLO | L0 phone + L3 cluster routing | schwere Inference nicht auf Mainframe |

## Trainings-Modus (parallel)

1. **L1 Mainframe (jetzt):** Curriculum + State JSON + Alignment mit Heroismus-Axiomen  
2. **L3 Cluster (wenn kubectl live):** batch re-rank / embedding der Curriculum-Liste neben `fusion-training`  
3. **Phone:** sobald Android-Filedrop einen Profil-Export oder Leseliste ablegt → merge in State  

## Was bewusst *nicht* trainiert wird

- Ungeclaimte HBV/HDV-Papers auf Namens-Profilen  
- Mentions-Spam ohne Kontext (Name-Mentions von Dritten)  
- Keypass-/Auth-Links aus Mails (nie persistieren)

## Nächster Operator-Schritt (optional)

1. Bestätigen, ob [StephanUrban1](https://independent.academia.edu/StephanUrban1) dein Profil ist — oder korrekte URL senden  
2. Vom Handy: Academia → Profil teilen / Leseliste export → Mesh filedrop `inbound/android/`  
3. Virologie-Claims ablehnen, falls fremd  

## Dateien

- State: `~/.fusion/mesh/coordination/academia_training_state.json`  
- Engine-Hook: `scripts/academia_curriculum_train.py`  
- Catalog: `mesh_service_coordination.yaml` → external `academia`
