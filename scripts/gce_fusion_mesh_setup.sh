#!/bin/bash
# Setup fusion-mesh-exit GCE as L2 publish + fractal host
set -euo pipefail
echo "=== GCE fusion-mesh-exit setup $(date -Iseconds) ==="
hostname
whoami

mkdir -p "$HOME/.fusion/mesh/fractal/replicas" \
         "$HOME/.fusion/mesh/coordination" \
         "$HOME/.fusion/publish/v10"

PUB="$HOME/.fusion/publish/v10"
cd "$PUB"
base="https://github.com/95guknow/fusion-hero-os/releases/download"

for path in \
  "dissertation-v1.0/Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf" \
  "geisteskrankheiten-4d-v10.0.0/Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf" \
  "heroische-mathematik-v10.0.0/Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf"
do
  f=$(basename "$path")
  if [[ ! -f "$f" ]]; then
    echo "GET $f"
    curl -fsSL -o "$f" "$base/$path" || echo "fail $f"
  else
    echo "have $f"
  fi
done

ls -lah "$PUB"

cat > "$PUB/index.html" <<'HTML'
<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>Fusion Hero OS — GCE Publish v10</title>
<style>body{font-family:system-ui;max-width:42rem;margin:2rem auto;padding:0 1rem;line-height:1.5}a{color:#0b5}code{background:#f4f4f4;padding:.1rem .3rem}</style></head>
<body>
<h1>Fusion Hero OS · GCE mesh-exit</h1>
<p>L2 always-on publish mirror · v10.0.0</p>
<ul>
<li><a href="Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf">Dissertation Autopoiesis/Autopolitik PDF</a></li>
<li><a href="Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf">Geisteskrankheiten 4D Matrix v10 PDF</a></li>
<li><a href="Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf">Heroische Mathematik v10 PDF</a></li>
</ul>
<p><code>fusion-mesh-exit</code> · Tailscale · europe-west3-a</p>
</body></html>
HTML

if ss -ltn 2>/dev/null | grep -q ':8088'; then
  echo "already_listening_8088"
else
  # stop prior by port if any (avoid pkill -f patterns)
  if command -v fuser >/dev/null 2>&1; then
    fuser -k 8088/tcp 2>/dev/null || true
  fi
  nohup python3 -m http.server 8088 --bind 0.0.0.0 \
    > "$HOME/.fusion/publish/http8088.log" 2>&1 &
  echo "started_pid=$!"
  sleep 1
fi

ss -ltn | grep 8088 || true
curl -fsS -o /dev/null -w "local_http=%{http_code}\n" http://127.0.0.1:8088/ || true
echo "TS_IP=$(tailscale ip -4 2>/dev/null || true)"
echo "DONE"
