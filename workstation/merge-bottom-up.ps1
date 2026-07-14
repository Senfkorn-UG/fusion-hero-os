# merge-bottom-up.ps1 - Bifurcierter Bottom-Up-Merge: WSL -> Windows -> GitHub
param(
    [switch]$PlanOnly,
    [switch]$NoPush,
    [switch]$Force,
    [string]$CommitMessage = ""
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

# Git safe.directory fuer WSL-Zugriff von Windows
git config --global --add safe.directory '%(prefix)///wsl.localhost/Ubuntu/home/admin_fuhos/fusion-hero-core' 2>$null

$WinRepo = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$WslRepo = "\\wsl.localhost\Ubuntu\home\admin_fuhos\fusion-hero-core"
$StatusDir = Join-Path $env:USERPROFILE ".fusion"
$StatusFile = Join-Path $StatusDir "merge-bottom-up.status.json"
$LogFile = Join-Path $StatusDir "merge-bottom-up.log"

$RootDuplicates = @(
    "apply-storage-policy.ps1",
    "disk_dedup_offload.py",
    "followup-all.ps1",
    "followup-all.sh",
    "load-env.ps1",
    "mesh_roles.yaml",
    "offload-full-sweep.ps1",
    "offload-to-gdrive.ps1",
    "paths.json",
    "storage_policy.json",
    "storage_policy.py",
    "workstation/BRANCH_STRATEGY.md",
    "workstation/mesh_roles.yaml"
)

$ExcludePatterns = @(
    "src/normal_os/llm/router.py.b64",
    "src/normal_os/llm/test.txt",
    "src/normal_os/llm/test_write.py"
)

function Write-Log([string]$Msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg"
    Write-Host $line
    if (-not (Test-Path $StatusDir)) { New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null }
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Write-Status([string]$State, [string]$Message, [hashtable]$Extra = @{}) {
    if (-not (Test-Path $StatusDir)) { New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null }
    $obj = [ordered]@{
        state     = $State
        message   = $Message
        policy_id = "bottom_up_merge"
        updated   = (Get-Date).ToString("o")
        win_repo  = $WinRepo
        wsl_repo  = $WslRepo
    }
    foreach ($k in $Extra.Keys) { $obj[$k] = $Extra[$k] }
    $obj | ConvertTo-Json -Depth 4 | Set-Content $StatusFile -Encoding UTF8
}

function Invoke-Git([string]$Repo, [string[]]$GitArgs) {
    Push-Location $Repo
    try {
        $out = & git @GitArgs 2>&1
        return @{ ok = ($LASTEXITCODE -eq 0); out = ($out | Out-String).Trim(); code = $LASTEXITCODE }
    } finally {
        Pop-Location
    }
}

function Test-RootDuplicatesPresent([string]$Repo) {
    $found = @()
    foreach ($f in $RootDuplicates) {
        if (Test-Path (Join-Path $Repo $f)) { $found += $f }
    }
    return $found
}

function Get-Rev([string]$Repo, [string]$Ref = "HEAD") {
    $r = Invoke-Git $Repo @("rev-parse", $Ref)
    if ($r.ok) { return $r.out.Trim() }
    return $null
}

Write-Log "=== Bottom-Up Merge (Windows) ==="
Write-Status "running" "Bottom-Up Merge gestartet"

if (-not (Test-Path $WinRepo)) {
    Write-Status "failed" "Windows-Repo nicht gefunden: $WinRepo"
    throw "Windows-Repo nicht gefunden"
}

$wslOk = Test-Path (Join-Path $WslRepo ".git")
if (-not $wslOk) {
    Write-Log "WARNUNG: WSL-Repo nicht erreichbar: $WslRepo"
}

# Phase 1: Root-Duplikat-Guard
$dupes = Test-RootDuplicatesPresent $WinRepo
if ($dupes.Count -gt 0 -and -not $Force) {
    $msg = "Root-Duplikate gefunden: $($dupes -join ', '). Entfernen oder -Force nutzen."
    Write-Status "failed" $msg
    throw $msg
}
if ($dupes.Count -gt 0 -and $Force) {
    Write-Log "Entferne Root-Duplikate (-Force)..."
    Push-Location $WinRepo
    foreach ($f in $dupes) {
        if (Test-Path $f) { git rm $f 2>$null | Out-Null }
    }
    $st = git status --porcelain
    if ($st) {
        git commit -m "chore: remove duplicate root files (bottom-up merge guard)" --no-verify 2>$null | Out-Null
    }
    Pop-Location
}

# Phase 2: WSL vorbereiten (Commit falls noetig)
if ($wslOk -and $CommitMessage) {
    $wslStatus = Invoke-Git $WslRepo @("status", "--porcelain")
    if ($wslStatus.out) {
        Write-Log "WSL: Commit vorbereiten..."
        Push-Location $WslRepo
        foreach ($pat in $ExcludePatterns) {
            git reset HEAD -- $pat 2>$null | Out-Null
        }
        git add -A
        foreach ($pat in $ExcludePatterns) {
            git reset HEAD -- $pat 2>$null | Out-Null
        }
        $st2 = git status --porcelain
        if ($st2 -and -not $PlanOnly) {
            git commit -m $CommitMessage --no-verify 2>&1 | ForEach-Object { Write-Log $_ }
        }
        Pop-Location
    }
}

# Phase 3: Fetch origin + WSL
Write-Log "Fetch origin..."
Invoke-Git $WinRepo @("fetch", "origin") | Out-Null

$wslHead = $null
if ($wslOk) {
    Write-Log "Fetch WSL..."
    Invoke-Git $WinRepo @("fetch", $WslRepo, "main") | Out-Null
    $wslHead = Get-Rev $WinRepo "FETCH_HEAD"
}

$winHead = Get-Rev $WinRepo "HEAD"
$originHead = Get-Rev $WinRepo "origin/main"

$plan = [ordered]@{
    win_head    = $winHead
    origin_head = $originHead
    wsl_head    = $wslHead
}

Write-Log "Windows HEAD: $winHead"
Write-Log "origin/main:  $originHead"
Write-Log "WSL HEAD:     $wslHead"

# Phase 4: WSL -> Windows merge wenn WSL voraus
if ($wslOk -and $wslHead -and $wslHead -ne $winHead) {
    $ahead = Invoke-Git $WinRepo @("rev-list", "--count", "HEAD..FETCH_HEAD")
    if ($ahead.ok -and [int]$ahead.out -gt 0) {
        Write-Log "Merge WSL -> Windows ($($ahead.out) commits)..."
        if ($PlanOnly) {
            Write-Log "PlanOnly: WSL-Merge wuerde ausgefuehrt"
        } else {
            $mg = Invoke-Git $WinRepo @("merge", "FETCH_HEAD", "-m", "Merge WSL fusion-hero-core (bottom-up)")
            if (-not $mg.ok) {
                Write-Status "failed" "WSL-Merge fehlgeschlagen" @{ detail = $mg.out }
                throw "WSL-Merge fehlgeschlagen: $($mg.out)"
            }
            $winHead = Get-Rev $WinRepo "HEAD"
        }
    }
}

# Phase 5: origin/main -> Windows
if ($originHead -and $winHead -ne $originHead) {
    $behind = Invoke-Git $WinRepo @("rev-list", "--count", "HEAD..origin/main")
    $aheadRemote = Invoke-Git $WinRepo @("rev-list", "--count", "origin/main..HEAD")
    Write-Log "Windows vs origin: behind=$($behind.out) ahead=$($aheadRemote.out)"
    if ($PlanOnly) {
        Write-Log "PlanOnly: git pull --no-rebase wuerde ausgefuehrt"
    } else {
        Write-Log "Pull origin/main (merge, no rebase)..."
        $pl = Invoke-Git $WinRepo @("pull", "origin", "main", "--no-rebase", "--no-edit")
        if (-not $pl.ok) {
            Write-Status "failed" "Pull fehlgeschlagen" @{ detail = $pl.out }
            throw "Pull fehlgeschlagen: $($pl.out)"
        }
        $winHead = Get-Rev $WinRepo "HEAD"
    }
} elseif ($originHead -and $winHead -eq $originHead) {
    Write-Log "Windows bereits sync mit origin/main"
}

# Phase 6: Push
$finalHead = Get-Rev $WinRepo "HEAD"
$finalOrigin = Get-Rev $WinRepo "origin/main"
$needsPush = $finalHead -and $finalOrigin -and ($finalHead -ne $finalOrigin)

if ($needsPush) {
    if ($NoPush -or $PlanOnly) {
        Write-Log "PlanOnly/NoPush: Push ausstehend ($finalHead)"
        Write-Status "planned" "Push ausstehend" @{ head = $finalHead }
        exit 0
    }
    Write-Log "Push origin main..."
    $ps = Invoke-Git $WinRepo @("push", "origin", "main")
    if (-not $ps.ok) {
        Write-Status "failed" "Push fehlgeschlagen" @{ detail = $ps.out }
        throw "Push fehlgeschlagen: $($ps.out)"
    }
    $finalOrigin = Get-Rev $WinRepo "origin/main"
} else {
    Write-Log "Bereits sync - kein Push noetig"
}

if (-not $needsPush -and -not ($wslOk -and $wslHead -and $wslHead -ne $winHead)) {
    Write-Status "success" "already-synced" @{
        head = $finalHead
        origin = $finalOrigin
    }
} else {
    Write-Status "success" "Bottom-Up Merge abgeschlossen" @{
        head = $finalHead
        origin = $finalOrigin
    }
}

Write-Log "Status: $StatusFile"
Write-Log "=== Fertig ==="
