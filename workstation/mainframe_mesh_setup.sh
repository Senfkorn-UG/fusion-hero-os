#!/usr/bin/env bash
# mainframe_mesh_setup.sh — Fractal mainframe save + virtual exit (Linux/WSL)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${REPO_ROOT}/fractal_mainframe_mesh.py"
EXIT_PROFILE="${EXIT_PROFILE:-direct}"
APPLY_EXIT=0
DRY_RUN=0
REPLICATE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --exit) EXIT_PROFILE="$2"; shift 2 ;;
    --apply-exit) APPLY_EXIT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --replicate) REPLICATE=1; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "=== Fusion Hero OS — Mainframe Mesh Setup ==="
echo "Repo: $REPO_ROOT"
echo "Exit profile: $EXIT_PROFILE"

ARGS=(setup --exit "$EXIT_PROFILE")
[[ $APPLY_EXIT -eq 1 ]] && ARGS+=(--apply-exit)
[[ $DRY_RUN -eq 1 ]] && ARGS+=(--dry-run)

python3 "$PY" "${ARGS[@]}"

if [[ $REPLICATE -eq 1 ]]; then
  echo ""
  echo "-> Replicating fractal manifest to mesh peers..."
  python3 "$PY" save --replicate
fi

echo ""
echo "-> Fractal status:"
python3 "$PY" status

echo ""
echo "Done. Manifest: ${HOME}/.fusion/mesh/fractal/manifest.json"