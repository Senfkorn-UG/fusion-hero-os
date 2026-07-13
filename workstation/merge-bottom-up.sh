#!/usr/bin/env bash
# merge-bottom-up.sh - Bifurcierter Bottom-Up-Merge: WSL -> Windows -> GitHub -> WSL
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PLAN_ONLY=false
NO_PUSH=false
FORCE=false
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan-only) PLAN_ONLY=true ;;
    --no-push)   NO_PUSH=true ;;
    --force)     FORCE=true ;;
    --message)   MESSAGE="$2"; shift ;;
    -h|--help)
      echo "Usage: merge-bottom-up.sh [--plan-only] [--no-push] [--force] [--message MSG]"
      exit 0
      ;;
    *) echo "Unbekannt: $1" >&2; exit 1 ;;
  esac
  shift
done

STATUS_DIR="${HOME}/.fusion"
STATUS_FILE="${STATUS_DIR}/merge-bottom-up.status.json"
mkdir -p "$STATUS_DIR"

write_status() {
  local state="$1" msg="$2"
  python3 -c "
import json, datetime, os
print(json.dumps({
    'state': '$state',
    'message': '''$msg''',
    'policy_id': 'bottom_up_merge',
    'updated': datetime.datetime.now().astimezone().isoformat(),
    'layer': 'wsl'
}, indent=2))
" > "$STATUS_FILE"
}

echo "=== Bottom-Up Merge (WSL) ==="

# Phase 1: WSL vorbereiten - Junk nicht committen
JUNK=(
  "src/normal_os/llm/router.py.b64"
  "src/normal_os/llm/test.txt"
  "src/normal_os/llm/test_write.py"
)
for j in "${JUNK[@]}"; do
  if git status --porcelain -- "$j" 2>/dev/null | grep -q .; then
    git reset HEAD -- "$j" 2>/dev/null || true
  fi
done

if [[ -n "$MESSAGE" ]] && [[ "$PLAN_ONLY" == false ]]; then
  CHANGES=$(git status --porcelain | grep -v -E 'router\.py\.b64|test\.txt|test_write\.py' || true)
  if [[ -n "$CHANGES" ]]; then
    git add -A
    for j in "${JUNK[@]}"; do git reset HEAD -- "$j" 2>/dev/null || true; done
    if git diff --cached --quiet; then
      echo "  Keine committbaren Aenderungen nach Junk-Filter"
    else
      git commit -m "$MESSAGE" --no-verify
      echo "  WSL commit: $MESSAGE"
    fi
  fi
fi

# Phase 2+3: Windows merge + GitHub push
if ! command -v powershell.exe >/dev/null 2>&1; then
  write_status "failed" "powershell.exe nicht verfuegbar"
  echo "FEHLER: powershell.exe nicht verfuegbar" >&2
  exit 1
fi

PS_ARGS=(-NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/merge-bottom-up.ps1")
[[ "$PLAN_ONLY" == true ]] && PS_ARGS+=(-PlanOnly)
[[ "$NO_PUSH" == true ]] && PS_ARGS+=(-NoPush)
[[ "$FORCE" == true ]] && PS_ARGS+=(-Force)
[[ -n "$MESSAGE" ]] && PS_ARGS+=(-CommitMessage "$MESSAGE")

powershell.exe "${PS_ARGS[@]}"

# Phase 4: WSL zuruecksyncen von Windows
if [[ "$PLAN_ONLY" == false ]] && [[ "$NO_PUSH" == false ]]; then
  WIN_REPO="/mnt/c/Users/Admin/fusion-hero-os"
  if [[ -d "$WIN_REPO/.git" ]]; then
    echo ""
    echo "Phase 4: WSL <- Windows sync..."
    git fetch "$WIN_REPO" main 2>/dev/null || true
    if git merge FETCH_HEAD --ff-only 2>/dev/null; then
      echo "  Fast-forward OK"
    else
      git reset --hard FETCH_HEAD 2>/dev/null || true
      echo "  Hard reset auf Windows HEAD"
    fi
    git update-ref refs/remotes/origin/main FETCH_HEAD 2>/dev/null || true
    echo "  WSL HEAD: $(git rev-parse --short HEAD)"
  fi
fi

write_status "success" "Bottom-Up Merge WSL abgeschlossen"
echo ""
echo "=== Bottom-Up Merge abgeschlossen ==="
echo "Status: $STATUS_FILE"
