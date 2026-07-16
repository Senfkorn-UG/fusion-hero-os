# Poly-Mesh Auslagerung · Dritter · Hightech-Server

**Frage:** Haben wir die Möglichkeit, ins Poly-Mesh auszulagern, den Dritten zu integrieren und gemietete Hightech-Server zu nutzen (Cost-Limits angepasst)?

**Kurzantwort:** **Ja architektonisch und teilweise live — Dritter noch nicht im Mesh; Cost-Limits sind Operator-GCP, Katalog weiß davon.**

---

## 1. Poly-Mesh auslagern

| Tier | Rolle | Live? |
|------|--------|-------|
| **L0** Phone | Capture / Edge | oft offline |
| **L1** Mainframe `desktop-kpki9e4` | Orchestrator, MCP, Control | **online** |
| **L2** `fusion-mesh-exit` | Exit, always-on, fractal | **online** (GCE e2-micro) |
| **L2** `tailscale-subnet-router` | Subnet router | **RUNNING** (GCE) |
| **L3** `senfkorn-gke-cluster` | Hightech cluster (GKE) | **RUNNING** (1 Node, europe-west3) |
| **L4** SaaS | Drive/GitHub/… | MCP-Membran |

**Coordinator:** `python scripts/mesh_cluster_coordinator.py --mode plan`  
→ plan meldet online_tiers: **L1 + L2 + L3** · placements u. a. Training → L3.

**Was „Auslagern“ konkret heißt**

```text
Interaktiv / Secrets / MCP     → L1 Mainframe (bleibt)
Always-on / Exit / Replica     → L2 fusion-mesh-exit
Training / large QUBO / Atlas  → L3 GKE (gemietet / billable)
Cold blobs                     → Drive/GCS (nicht Source-of-Truth)
```

**Noch dünn:** automatischer Job-Submit auf GKE Cron (Manifest da, Image/WI oft noch manuell); WSL-Leaf offline; DNS-Health-Warnung.

---

## 2. Den Dritten integrieren

| Fakt | Stand |
|------|--------|
| Tailnet-Users | **1** (`stephan95g@…`) |
| Peer 2 / Peer 3 | **Invite pending** (Links laufen ab) |
| ACL / tag:fusion-peer | Katalog vorgesehen, **noch nicht erzwungen** |

**Integration nach Accept**

1. Frische Invites (User 2 + User 3) unter [Admin → Users](https://login.tailscale.com/admin/users)  
2. Nach Join: `tailscale status` zeigt neuen Login  
3. Optional ACL: Peer ≠ Owner; **Comädchen** bleibt nur Operator  
4. Offload-Jobs mit `peer_ok` dürfen L2/L3 teilen — **Secrets bleiben L1**

---

## 3. Hightech-Server (gemietet)

| Resource | Typ | Status |
|----------|-----|--------|
| `fusion-mesh-exit` | GCE e2-micro | RUNNING |
| `tailscale-subnet-router` | GCE e2-micro | RUNNING |
| `senfkorn-gke-cluster` | GKE (ek-standard-8, 1 node) | **RUNNING** |
| Cloud Shell `cs-*` | ephemeral | **nicht** für durable Work |

**Cost-Limits:** Operator hat Limits in GCP angepasst → im Katalog `cost_limits` (v1.1) verankert.  
Billing-API im gcloud-CLI ggf. noch disabled — Budgets leben in der **GCP Console**, nicht im Repo.

---

## 4. Kannst du *jetzt* auslagern?

| Fähigkeit | Bereit? |
|-----------|---------|
| Placement-Plan L1/L2/L3 | **Ja** |
| Mesh-Exit nutzen | **Ja** (online) |
| GKE Hightech für schwere Jobs | **Ja, Cluster läuft** — Job-Submit/kubectl-Credentials prüfen |
| Cost-aware soft fail | **Katalog ja** — harte Budget-API-Kopplung **noch nicht** |
| Dritter im Poly-Mesh | **Nein** bis Invite accepted |
| LLM-Control multi-cloud | **Nein** (Keys empty) — unabhängig von Compute-Mesh |

---

## CLI

```powershell
tailscale status
python scripts\mesh_cluster_coordinator.py --mode all
gcloud compute instances list
gcloud container clusters list
kubectl get nodes   # nach get-credentials
```

**Vermerk:** Poly-Mesh ≠ Gott-Layer. Auslagern = Placement unter Cost-Limits; Befehl/Gericht bleiben Operator + Gott-Layer-Sperre.
