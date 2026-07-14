# Fusion-Hero-OS v8 - Grok Intern Abgleich mit GitHub
# Synchronisiert lokalen Grok-Skill + Kilo-Workspace mit Repo-Stand

$ErrorActionPreference = "Continue"
$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$GrokSkill = Join-Path $env:USERPROFILE ".grok\skills\fusion-hero-os"
$KiloWs = Join-Path $env:USERPROFILE ".config\kilo\fusion-hero-os.code-workspace"
$GitRemote = "https://github.com/95guknow/fusion-hero-os"
$CheckScript = Join-Path $PSScriptRoot "check-grok-cli.ps1"

New-Item -ItemType Directory -Force -Path $GrokSkill | Out-Null

# Grok CLI Version (check-grok-cli.ps1 oder inline)
$grokVersion = $null
$previousGrokVersion = $null
$grokCheckedAt = (Get-Date).ToString("o")
if (Test-Path $CheckScript) {
    & $CheckScript -Quiet 2>$null | Out-Null
    $statusFile = Join-Path $env:USERPROFILE ".fusion\grok-cli.status.json"
    if (Test-Path $statusFile) {
        try {
            $st = Get-Content $statusFile -Raw | ConvertFrom-Json
            $grokVersion = $st.version
            $previousGrokVersion = $st.previous_version
        } catch {}
    }
}
if (-not $grokVersion) {
    try {
        $grokBin = Join-Path $env:USERPROFILE ".grok\bin\grok.exe"
        $raw = if (Test-Path $grokBin) {
            & $grokBin --version 2>&1 | Out-String
        } else {
            & grok --version 2>&1 | Out-String
        }
        if ($raw -match 'v?(\d+\.\d+\.\d+)') { $grokVersion = $Matches[1] }
    } catch {}
}

# GitHub-Stand ermitteln
$gitHead = "unknown"
$gitDate = "unknown"
try {
    Push-Location $Root
    $gitHead = (git rev-parse --short HEAD 2>$null)
    $gitDate = (git log -1 --format="%ci" 2>$null)
    Pop-Location
} catch {
    Pop-Location -ErrorAction SilentlyContinue
}

@{
    "folders" = @(
        @{ "path" = $Root },
        @{ "path" = "C:\Users\Admin\heroic-core-foundation" },
        @{ "path" = $GrokSkill }
    )
    "settings" = @{
        "FUSION_OS_VERSION" = "v8"
        "HEROIC_CORE_VERSION" = "v8"
        "GITHUB_REPO" = "95guknow/fusion-hero-os"
        "GITHUB_HEAD" = $gitHead
        "GITHUB_SYNCED" = $gitDate
        "FUSION_GROK_CLI_VERSION" = $grokVersion
    }
} | ConvertTo-Json -Depth 4 | Set-Content -Path $KiloWs -Encoding UTF8

Write-Host "[v8] Grok-intern Abgleich mit GitHub:" -ForegroundColor Cyan
Write-Host "  Repo:      $GitRemote"
Write-Host "  HEAD:      $gitHead ($gitDate)"
Write-Host "  Skill:     $GrokSkill"
Write-Host "  Workspace: $KiloWs"
Write-Host "  Version:   Fusion Hero OS v8 / Heroic Core v8"
if ($grokVersion) {
    Write-Host "  Grok CLI:  v$grokVersion" -ForegroundColor Green
    if ($previousGrokVersion -and ($previousGrokVersion -ne $grokVersion)) {
        Write-Host "  Grok Update: v$previousGrokVersion -> v$grokVersion" -ForegroundColor Magenta
    }
} else {
    Write-Host "  Grok CLI:  (nicht ermittelt)" -ForegroundColor Yellow
}

# Skill-Manifest aktualisieren
$manifest = Join-Path $GrokSkill "GITHUB_SYNC.json"
$manifestObj = [ordered]@{
    repo = "95guknow/fusion-hero-os"
    branch = "main"
    head = $gitHead
    synced_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    version = "v8"
    grok_cli_version = $grokVersion
    grok_cli_checked_at = $grokCheckedAt
    previous_grok_cli_version = $previousGrokVersion
    deployment_guide = "DEPLOYMENT_GUIDE.md"
    gui = "http://127.0.0.1:8000"
    gui_module = "03_Code/Dashboard/app.py"
    nicegui_legacy = "http://127.0.0.1:8080"
}
$manifestObj | ConvertTo-Json -Depth 3 | Set-Content -Path $manifest -Encoding UTF8

Write-Host "  Manifest:  $manifest" -ForegroundColor DarkGray
