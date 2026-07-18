#!/usr/bin/env bash
set -e

OUTPUT_FILE="resources-auto.txt"

echo "Scanning repository for URLs..." > "$OUTPUT_FILE"

# Finde URLs in Markdown-Dateien
grep -RhoE "(https?://[^ )\"]+)" -- *.md docs mesh hero-archive >> "$OUTPUT_FILE" || true

echo "Ressourcen-Scan abgeschlossen. Ergebnisse in $OUTPUT_FILE"
