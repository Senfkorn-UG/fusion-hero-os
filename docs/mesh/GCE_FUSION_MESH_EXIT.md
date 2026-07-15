# GCE fusion-mesh-exit in use

**Dissertation-as-OS:** L2 publish mirror is an **empirical expression** of the dissertation (OS = work; text = one form). Ontology: `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md`.

- Project: project-bbf0e6db-52e1-462b-8e3
- Zone: europe-west3-a
- External: YOUR_GCE_EXTERNAL_IP
- Tailscale: 100.103.188.54
- Service: hero-docs-server.py :8088
- Publish: /home/Admin/fusion-hero-core/docs/publish/v10
- Repo HEAD (2026-07-15): `a5c7dae` (ff-only pull from origin/main)

## Mesh URLs (Tailscale)
- http://100.103.188.54:8088/docs/publish/v10/
- http://fusion-mesh-exit:8088/docs/publish/v10/  (if MagicDNS)

## SSH
```powershell
gcloud compute ssh fusion-mesh-exit --zone=europe-west3-a
```

## 1) Git pull
- Local WIP stashed: `gce-wip-before-pull-*`
- Fast-forward to `origin/main`
- `docs/publish/v10` restored/backed up under `~/.fusion/publish/v10-backup-*`

## 2) Exit node
- Advertised routes: `0.0.0.0/0`, `::/0`, `10.156.0.0/20`
- **Approve** in Tailscale admin if `ExitNodeOption` still false:  
  https://login.tailscale.com/admin/machines → fusion-mesh-exit → Edit route settings → **Use as exit node**
- On Windows client:
  ```powershell
  tailscale set --exit-node=fusion-mesh-exit
  # off again:
  tailscale set --exit-node=
  ```

## 3) Coordinator cron
- Crontab: `*/30 * * * * /home/Admin/bin/fusion-coord.sh`
- Log: `~/.fusion/logs/coordinator.log`
- Output: `~/.fusion/mesh/coordination/latest.json`
- Manual run: `bash /home/Admin/bin/fusion-coord.sh`

## Scripts
- `scripts/gce_all3_setup.sh`
- `scripts/gce_fix_coord_cron.sh`
- `scripts/gce_publish_only.sh`
