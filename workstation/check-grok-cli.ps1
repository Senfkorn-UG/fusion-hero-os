# check-grok-cli.ps1 - Grok CLI Version + Skill Health (Fusion Hero OS)
param(
    [switch]$Quiet
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$GrokSkill = Join-Path $env:USERPROFILE ".grok\skills\fusion-hero-os"
$SkillFile = Join-Path $GrokSkill "SKILL.md"
$StatusDir = Join-Path $env:USERPROFILE ".fusion"
$StatusFile = Join-Path $StatusDir "grok-cli.status.json"
$ApiUrl = "http://127.0.0.1:8000"

function Get-GrokCliInfo {
    $candidates = @(
        @{ Name = "grok"; Args = @("--version") },
        @{ Name = "agent"; Args = @("--version") },
        @{ Name = "grok"; Args = @("version") }
    )
    $grokBin = Join-Path $env:USERPROFILE ".grok\bin\grok.exe"
    if (Test-Path $grokBin) {
        $candidates = @(
            @{ Name = $grokBin; Args = @("--version") }
        ) + $candidates
    }

    foreach ($c in $candidates) {
        try {
            $out = & $c.Name @($c.Args) 2>&1 | Out-String
            $out = $out.Trim()
            if (-not $out) { continue }
            $ver = $null
            if ($out -match 'v?(\d+\.\d+\.\d+)') {
                $ver = $Matches[1]
            }
            return @{
                found    = $true
                command  = $c.Name
                raw      = $out
                version  = $ver
            }
        } catch {
            continue
        }
    }
    return @{ found = $false; command = $null; raw = $null; version = $null }
}

function Get-PreviousGrokVersion {
    if (-not (Test-Path $StatusFile)) { return $null }
    try {
        $prev = Get-Content $StatusFile -Raw | ConvertFrom-Json
        return $prev.version
    } catch {
        return $null
    }
}

$cli = Get-GrokCliInfo
$skillOk = Test-Path $SkillFile
$previousVersion = Get-PreviousGrokVersion

$bridgeOk = $false
$bridgeDetail = $null
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/api/health?light=true" -TimeoutSec 3
    if ($health.grok_bridge) {
        $bridgeDetail = $health.grok_bridge
        $bridgeOk = [bool]$health.grok_bridge.skill_loaded
    } elseif ($health.modules) {
        $bridgeDetail = @{ note = "grok_bridge field not in health" }
    }
} catch {
    $bridgeDetail = @{ error = "dashboard_offline" }
}

$ok = $cli.found -and $skillOk
$status = [ordered]@{
    checked_at       = (Get-Date).ToString("o")
    ok               = $ok
    version          = $cli.version
    cli_command      = $cli.command
    cli_raw          = $cli.raw
    cli_found        = $cli.found
    skill_path       = $GrokSkill
    skill_file       = $SkillFile
    skill_ok         = $skillOk
    previous_version = $previousVersion
    version_changed  = ($previousVersion -and $cli.version -and ($previousVersion -ne $cli.version))
    bridge_online    = ($null -ne $bridgeDetail -and -not $bridgeDetail.error)
    bridge_skill_loaded = $bridgeOk
    bridge_detail    = $bridgeDetail
}

if (-not (Test-Path $StatusDir)) {
    New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
}
$status | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusFile -Encoding UTF8

if (-not $Quiet) {
    Write-Host "=== Grok CLI Check ===" -ForegroundColor Cyan
    if ($cli.found) {
        Write-Host "  CLI:     $($cli.command) -> $($cli.version) ($($cli.raw))" -ForegroundColor Green
    } else {
        Write-Host "  CLI:     nicht gefunden (grok/agent --version)" -ForegroundColor Red
    }
    if ($skillOk) {
        Write-Host "  Skill:   OK ($SkillFile)" -ForegroundColor Green
    } else {
        Write-Host "  Skill:   FEHLT ($SkillFile)" -ForegroundColor Yellow
    }
    if ($status.version_changed) {
        Write-Host "  Update:  $previousVersion -> $($cli.version)" -ForegroundColor Magenta
    }
    if ($bridgeDetail -and -not $bridgeDetail.error) {
        Write-Host "  Bridge:  skill_loaded=$bridgeOk" -ForegroundColor $(if ($bridgeOk) { "Green" } else { "DarkGray" })
    } else {
        Write-Host "  Bridge:  Dashboard offline (optional)" -ForegroundColor DarkGray
    }
    Write-Host "  Status:  $StatusFile" -ForegroundColor DarkGray
}

if ($ok) { exit 0 } else { exit 1 }
