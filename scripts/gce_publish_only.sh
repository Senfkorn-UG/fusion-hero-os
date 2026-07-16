#!/bin/bash
set -euo pipefail
CORE=/home/Admin/fusion-hero-core
PUB=$CORE/docs/publish/v10
mkdir -p "$PUB" /home/Admin/.fusion/mesh/fractal/replicas /home/Admin/.fusion/mesh/coordination
cd "$PUB"
base=https://github.com/95guknow/fusion-hero-os/releases/download
for path in \
  dissertation-v1.0/Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf \
  geisteskrankheiten-4d-v10.0.0/Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf \
  heroische-mathematik-v10.0.0/Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf
do
  f=$(basename "$path")
  echo "GET $f"
  curl -fsSL -o "$f" "$base/$path"
done
cat > index.html <<'HTML'
<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>Fusion v10 Publish</title>
<style>body{font-family:system-ui;max-width:42rem;margin:2rem auto;padding:0 1rem;line-height:1.5}a{color:#0b5}</style>
</head><body>
<h1>Fusion Hero OS · GCE publish v10</h1>
<p>Host: fusion-mesh-exit (europe-west3-a) · via Tailscale</p>
<ul>
<li><a href="Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf">Dissertation PDF</a></li>
<li><a href="Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf">Geisteskrankheiten 4D v10 PDF</a></li>
<li><a href="Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf">Heroische Mathematik v10 PDF</a></li>
</ul>
</body></html>
HTML
ls -lah
# try git pull main (may be old mirror)
cd "$CORE"
git remote -v || true
git status -sb || true
echo DONE
