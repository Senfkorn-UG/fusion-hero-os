#!/usr/bin/env bash
# Refresh mesh file manifest for phone mirror (Tailscale MagicDNS URLs)
set -euo pipefail
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
python mesh_file_share.py sync
$base = python -c "from mesh_file_share import resolve_mainframe_base_url; print(resolve_mainframe_base_url())"
Write-Host ""
Write-Host "Phone portal: $base/mesh/files/phone" -ForegroundColor Green
Write-Host "Manifest:     $base/mesh/files/manifest" -ForegroundColor Green
