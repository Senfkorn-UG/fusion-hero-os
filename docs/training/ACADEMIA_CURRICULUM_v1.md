# Academia-aligned Training Curriculum v1

**Stand:** 2026-07-15 (Profil **operator-confirmed**)  
**Account-Signal (Gmail):** Academia Premium → **Stephan Urban** (`stephan95g@…`)  
**Profil (bestätigt):** [independent.academia.edu/StephanUrban1](https://independent.academia.edu/StephanUrban1)  
**Parallel track:** läuft neben Mesh-Service-Coordination + optional GKE inventory  

## Identity gate (bestätigt 2026-07-15)

| Quelle | Befund | Nutzung für Training |
|--------|--------|----------------------|
| Gmail `academia-mail.com` | Anrede **Stephan Urban**, Premium, Mentions, Reading-Recommendations | **primär** — Lesespur |
| Öffentliches Profil [StephanUrban1](https://independent.academia.edu/StephanUrban1) | **Operator bestätigt: eigenes Profil** · 5 Followers · Interests + HBV/HDV-Uploads | **kanonisch** für Autoren-/Domain-Korpus |
| Phone filedrops | leer; `phone_peer: null` | optionaler Export-Kanal |
| Inhouse `docs/Heroismus/`, Fusion Hero OS | Axiome I–IV, Sisyphos, CEC, Eudaimonia | **operativer** Heroismus-Anker |

**Regel:** Drei parallele Lernschichten — (1) Profil-Papers/Interests, (2) Gmail-Lesespur, (3) Inhouse-Heroismus. Keine Keypass-Auth; nur öffentliche Profilseiten + Mail-Metadaten + Repo.

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

### C — Antike Philosophie (Profil-Interests, bestätigt)
- Body and Soul
- Aristotle's Metaphysics
- Hellenistic Philosophy
- Plato and Platonism
- Ancient Greek Philosophy

### D — HBV / HDV Virologie (Profil-Uploads, bestätigt als Profil-Korpus)
Öffentliche Uploads u. a.:
- *Binding of Duck Carboxypeptidase D to Duck Hepatitis B Virus* (2004)
- *Infection of a human hepatoma cell line by hepatitis B virus* (PNAS 2002) — HepaRG-Modell
- *Liver capsule: Entry and entry inhibition of HBV/HDV* (Hepatology 2016) — NTCP
- *HDV replication sensed by MDA5 / IFN-β/λ* (J. Hepatology 2018)
- *Medical Advances in Hepatitis D Therapy: Molecular Targets* (IJMS) — Hepcludex/entry inhibitors
- *Delta cure meeting 2022* report; RNA-based HBV replication system (Science Advances 2023)
- *cccDNA quantification guidelines* (Gut); *VIR-3434* neutralizing antibody; animal NTCP variants; mitosis → uninfected daughters; fusion-inhibitor PK; cccDNA PCR assays

### E — Historisch / Nebenstränge (Empfehlungen)
- Artemision / Ephesos (antike Religion) — an Cluster C gekoppelt

## Mapping → Fusion Hero OS (Training-Targets)

| Academia-Cluster | Inhouse-Modul / Axiom | Trainingsziel |
|------------------|----------------------|---------------|
| Sisyphos / Camus / Absurd | Axiom IV CEC, PersistentSisyphosCycle | „Zufriedener Sisyphos“ = methodische Stabilität, nicht Tragödie |
| Existenz / Jaspers / Sartre | Axiom I 1st-Tier, Axiom III Psycholyse | Existenz als Integration, nicht Flucht in Transzendenz |
| Embodiment / Angst verkörpert | Axiom II Somatic | Körper als Hardware-Horkrux |
| Body & Soul / Aristotle / Plato | Axiom II + formal math / QUBO structure | Metaphysik als Struktur, nicht Flucht |
| Latour Existenzweisen | Layer-Registry / mesh segments | Jeder Connector = eigenes Existenzsegment im Mesh |
| Trustworthy agentic AI | Multi-Agent-Orchestration, Consent, Tarnkappe | Safety/privacy als Placement-Constraint L1 vs L3 |
| Meta-reasoning agents | heroic_core_orchestrator, PeerReview | Supervisor/Worker + 5-Dimensions-Review |
| Edge / YOLO | L0 phone + L3 cluster routing | schwere Inference nicht auf Mainframe |
| HBV/HDV entry, NTCP, cccDNA, IFN | domain knowledge pack (L3 batch later) | wissenschaftliche Domäne des Operators; getrennte Epistemik von Heroismus-Theorie |

## Trainings-Modus (parallel)

1. **L1 Mainframe (jetzt):** Curriculum + State JSON + Alignment mit Heroismus-Axiomen  
2. **L3 Cluster (wenn kubectl live):** batch re-rank / embedding der Curriculum-Liste neben `fusion-training`  
3. **Phone:** sobald Android-Filedrop einen Profil-Export oder Leseliste ablegt → merge in State  

## Was bewusst *nicht* trainiert wird

- Mentions-Spam ohne Kontext (Name-Mentions von Dritten)  
- Keypass-/Auth-Links aus Mails (nie persistieren)  
- Vermischung: Virologie-Fakten ≠ Heroismus-Axiome (getrennte Epistemik-Layer)

## Operator-Status

1. ~~Profil bestätigen~~ → **bestätigt** StephanUrban1  
2. Optional: Handy-Export Leseliste → `inbound/android/`  
3. Optional: PDF-Volltexte priorisierter Papers für L3-Deep-Ingest

## Dateien

- State: `~/.fusion/mesh/coordination/academia_training_state.json`  
- Engine-Hook: `scripts/academia_curriculum_train.py`  
- Catalog: `mesh_service_coordination.yaml` → external `academia`
