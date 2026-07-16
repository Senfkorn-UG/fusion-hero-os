#!/usr/bin/env bash
# Full mesh sync: journal inbox, manifest, archives, filedrops, GDrive mirror
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 mesh_file_share.py sync
BASE=$(python3 -c "from mesh_file_share import resolve_mainframe_base_url; print(resolve_mainframe_base_url())")
echo ""
echo "Phone portal:  ${BASE}/mesh/files/phone"
echo "Manifest:      ${BASE}/mesh/files/manifest"
echo "Filedrop POST: ${BASE}/mesh/files/drop  (Header: X-Mesh-Drop-Token)"
