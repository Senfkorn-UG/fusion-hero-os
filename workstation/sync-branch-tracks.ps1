# sync-branch-tracks.ps1 - main in develop/ascension mergen (Tracks aktualisieren)
param(
    [switch]$PlanOnly,
    [string[]]$Branches = @("develop", "ascension")
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$StatusFile = Join-Path $env:USERPROFILE ".fusion\sync-branch-tracks.status.json"

function Write-Status([string]$State, [string]$Message, [hashtable]$Extra = @{}) {
    $dir = Split-Path $StatusFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $obj = [ordered]@{
        state   = $State
        message = $Message
        updated = (Get-Date).ToString("o")
    }
    foreach ($k in $Extra.Keys) { $obj[$k] = $Extra[$k] }
    $obj | ConvertTo-Json -Depth 4 | Set-Content $StatusFile -Encoding UTF8
}

Push-Location $Root
try {
    Write-Host "=== Sync Branch Tracks (main -> develop/ascension) ===" -ForegroundColor Cyan
    git fetch origin 2>&1 | ForEach-Object { Write-Host $_ }

    $mainHead = (git rev-parse origin/main).Trim()
    Write-Host "origin/main: $mainHead" -ForegroundColor DarkGray

    $results = @()
    $savedBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    $hadChanges = [bool](git status --porcelain)

    foreach ($branch in $Branches) {
        $remote = "origin/$branch"
        if (-not (git rev-parse --verify $remote 2>$null)) {
            Write-Host "  SKIP: $remote nicht gefunden" -ForegroundColor Yellow
            continue
        }

        $behind = (git rev-list --count "$remote..origin/main" 2>$null).Trim()
        $ahead = (git rev-list --count "origin/main..$remote" 2>$null).Trim()
        Write-Host ""
        Write-Host "$branch : behind=$behind ahead=$ahead" -ForegroundColor Yellow

        if ([int]$behind -eq 0) {
            Write-Host "  Bereits aktuell" -ForegroundColor Green
            $results += @{ branch = $branch; action = "already-synced" }
            continue
        }

        if ($PlanOnly) {
            Write-Host "  PlanOnly: wuerde main in $branch mergen" -ForegroundColor DarkGray
            $results += @{ branch = $branch; action = "planned"; behind = $behind }
            continue
        }

        if ($hadChanges -and -not $PlanOnly) {
            Write-Host "  Stash lokale Aenderungen vor Branch-Wechsel..." -ForegroundColor DarkGray
            git stash push -u -m "sync-branch-tracks pre-checkout" 2>&1 | Out-Null
            $hadChanges = $false
        }

        git checkout $branch 2>&1 | ForEach-Object { Write-Host "  $_" }
        git pull origin $branch --no-rebase --no-edit 2>&1 | ForEach-Object { Write-Host "  $_" }
        git merge origin/main -m "Merge origin/main into $branch (track sync)" --no-edit 2>&1 | ForEach-Object { Write-Host "  $_" }

        if ($LASTEXITCODE -ne 0) {
            Write-Status "failed" "Merge-Konflikt in $branch"
            throw "Merge fehlgeschlagen fuer $branch"
        }

        git push origin $branch 2>&1 | ForEach-Object { Write-Host "  $_" }
        $newHead = (git rev-parse HEAD).Trim()
        Write-Host "  OK: $branch @ $newHead" -ForegroundColor Green
        $results += @{ branch = $branch; action = "merged"; head = $newHead }
    }

    git checkout $savedBranch 2>&1 | Out-Null

    Write-Status "success" "Branch-Tracks synchronisiert" @{ branches = $results }
    Write-Host ""
    Write-Host "Status: $StatusFile" -ForegroundColor Green
} catch {
    Write-Status "failed" $_.Exception.Message
    throw
} finally {
    Pop-Location
}
