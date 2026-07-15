# GCE fusion-mesh-exit in use

- Project: project-bbf0e6db-52e1-462b-8e3
- Zone: europe-west3-a
- External: 34.40.58.207
- Tailscale: 100.103.188.54
- Service: hero-docs-server.py :8088
- Publish: /home/Admin/fusion-hero-core/docs/publish/v10

## Mesh URLs (Tailscale)
- http://100.103.188.54:8088/docs/publish/v10/
- http://fusion-mesh-exit:8088/docs/publish/v10/  (if MagicDNS)

## SSH
gcloud compute ssh fusion-mesh-exit --zone=europe-west3-a
