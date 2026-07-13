# install-planova.ps1 — Planova Inneneinrichter (Tauri) auf Windows installieren
param(
    [switch]$SkipBuild,
    [switch]$ForceDeps
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")
# Git schreibt Fortschritt auf stderr — nicht als Fehler werten
$ErrorActionPreference = "Continue"

$CloneDir   = Join-Path $env:USERPROFILE "src\planova"
$InstallDir = Join-Path $env:USERPROFILE "Programs\planova"
$ShortcutName = "Planova Inneneinrichter"
$RepoUrl    = "https://github.com/XUranus/planova.git"
$PathsFile  = Join-Path $PSScriptRoot "paths.json"

function Write-Step([string]$Msg) {
    Write-Host "`n=== $Msg ===" -ForegroundColor Cyan
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Pnpm {
    if (Test-Command pnpm) { return }
    Write-Step "pnpm installieren"
    npm install -g pnpm
    if (-not (Test-Command pnpm)) { throw "pnpm konnte nicht installiert werden" }
}

function Ensure-Rust {
    if ((Test-Command rustc) -and -not $ForceDeps) { return }
    $rustup = Join-Path $env:USERPROFILE ".cargo\bin\rustc.exe"
    if (Test-Path $rustup) {
        $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
        if (Test-Command rustc) { return }
    }
    Write-Step "Rust installieren (rustup)"
    $installer = Join-Path $env:TEMP "rustup-init.exe"
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $installer -UseBasicParsing
    & $installer -y --default-toolchain stable --profile minimal
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    if (-not (Test-Command rustc)) { throw "Rust konnte nicht installiert werden" }
}

function Ensure-BuildTools {
    if (Test-Command cl) { return }
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
        if ($installPath) {
            $vcvars = Join-Path $installPath "VC\Auxiliary\Build\vcvars64.bat"
            if (Test-Path $vcvars) {
                Write-Host "  MSVC gefunden: $installPath" -ForegroundColor DarkGray
                return
            }
        }
    }
    Write-Host "  WARNUNG: MSVC Build Tools nicht gefunden." -ForegroundColor Yellow
    Write-Host "  Falls Build fehlschlaegt: winget install Microsoft.VisualStudio.2022.BuildTools" -ForegroundColor Yellow
}

function Ensure-Clone {
    Write-Step "Planova Repository"
    if (-not (Test-Path (Split-Path $CloneDir -Parent))) {
        New-Item -ItemType Directory -Force -Path (Split-Path $CloneDir -Parent) | Out-Null
    }
    if (Test-Path (Join-Path $CloneDir ".git")) {
        Push-Location $CloneDir
        git pull --ff-only 2>&1 | ForEach-Object { Write-Host $_ }
        Pop-Location
    } else {
        git clone $RepoUrl $CloneDir 2>&1 | ForEach-Object { Write-Host $_ }
    }
}

function Build-Planova {
    Write-Step "Planova bauen (pnpm tauri build - kann 10-20 Min. dauern)"
    Push-Location $CloneDir
    try {
        pnpm install 2>&1 | ForEach-Object { Write-Host $_ }
        pnpm add -D @tauri-apps/cli@^2 2>&1 | ForEach-Object { Write-Host $_ }
        pnpm tauri build 2>&1 | ForEach-Object { Write-Host $_ }
    } finally {
        Pop-Location
    }
}

function Find-BundleArtifact {
    $bundleRoot = Join-Path $CloneDir "src-tauri\target\release\bundle"
    if (-not (Test-Path $bundleRoot)) { return $null }

    $candidates = @(
        (Get-ChildItem -Path (Join-Path $bundleRoot "msi") -Filter "*.msi" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1),
        (Get-ChildItem -Path (Join-Path $bundleRoot "nsis") -Filter "*setup*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1),
        (Get-ChildItem -Path (Join-Path $bundleRoot "nsis") -Filter "*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
    )
    foreach ($c in $candidates) {
        if ($c) { return $c.FullName }
    }

    $exe = Join-Path $CloneDir "src-tauri\target\release\planova.exe"
    if (Test-Path $exe) { return $exe }
    $exe2 = Get-ChildItem -Path (Join-Path $CloneDir "src-tauri\target\release") -Filter "*.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch "build|deps" } | Select-Object -First 1
    if ($exe2) { return $exe2.FullName }
    return $null
}

function Install-Artifact([string]$Artifact) {
    Write-Step "Installation nach $InstallDir"
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

    if ($Artifact -like "*.msi") {
        Write-Host "  MSI installieren: $Artifact"
        Start-Process msiexec.exe -ArgumentList "/i `"$Artifact`" /qn TARGETDIR=`"$InstallDir`"" -Wait -NoNewWindow
    } elseif ($Artifact -like "*setup*.exe" -or $Artifact -like "*planova*.exe") {
        if ($Artifact -match "setup") {
            Write-Host "  NSIS Setup: $Artifact"
            Start-Process $Artifact -ArgumentList "/S" -Wait -NoNewWindow
        } else {
            Copy-Item $Artifact (Join-Path $InstallDir "planova.exe") -Force
        }
    } else {
        Copy-Item $Artifact (Join-Path $InstallDir "planova.exe") -Force
    }

    $releaseDir = Join-Path $CloneDir "src-tauri\target\release"
    if (Test-Path $releaseDir) {
        Get-ChildItem $releaseDir -File | Where-Object {
            $_.Extension -in @(".dll", ".pdb") -or $_.Name -eq "planova.exe"
        } | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $InstallDir $_.Name) -Force -ErrorAction SilentlyContinue
        }
    }
}

function Resolve-Executable {
    $candidates = @(
        (Join-Path $InstallDir "planova.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\planova\planova.exe"),
        (Join-Path $CloneDir "src-tauri\target\release\planova.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    $found = Get-ChildItem -Path $InstallDir -Recurse -Filter "planova.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

function New-Shortcuts([string]$ExePath) {
    Write-Step "Verknuepfungen anlegen"
    $wsh = New-Object -ComObject WScript.Shell

    $desktop = [Environment]::GetFolderPath("Desktop")
    $desktopLnk = Join-Path $desktop "$ShortcutName.lnk"
    $sc = $wsh.CreateShortcut($desktopLnk)
    $sc.TargetPath = $ExePath
    $sc.WorkingDirectory = Split-Path $ExePath -Parent
    $sc.Description = "Planova - AI Floor Plan to 3D Interior (DIY)"
    $sc.Save()
    Write-Host "  Desktop: $desktopLnk" -ForegroundColor Green

    $startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
    $startLnk = Join-Path $startMenu "$ShortcutName.lnk"
    $sc2 = $wsh.CreateShortcut($startLnk)
    $sc2.TargetPath = $ExePath
    $sc2.WorkingDirectory = Split-Path $ExePath -Parent
    $sc2.Description = "Planova - AI Floor Plan to 3D Interior (DIY)"
    $sc2.Save()
    Write-Host "  Startmenue: $startLnk" -ForegroundColor Green
}

function Update-PathsJson([string]$ExePath) {
    Write-Step "paths.json aktualisieren"
    if (-not (Test-Path $PathsFile)) {
        Write-Warning "paths.json nicht gefunden: $PathsFile"
        return
    }
    $json = Get-Content $PathsFile -Raw | ConvertFrom-Json
    $json | Add-Member -NotePropertyName "interior_design" -NotePropertyValue ([ordered]@{
        app           = "planova"
        label         = "Planova Inneneinrichter"
        install_dir   = $InstallDir
        executable    = $ExePath
        source_repo   = $RepoUrl
        install_script = (Join-Path $PSScriptRoot "install-planova.ps1")
        features      = [ordered]@{
            free_local = @("3d_viewer", "furniture_edit", "style_presets", "glb_export")
            byok_paid  = @("ai_floorplan_parse", "ai_render")
        }
        export_hint   = "GLB manuell nach 03_VR_Assets kopieren fuer VR-Viewer"
    }) -Force
    $json | ConvertTo-Json -Depth 6 | Set-Content $PathsFile -Encoding UTF8
    Write-Host "  paths.json: interior_design.planova eingetragen" -ForegroundColor Green
}

Write-Host "=== Planova Inneneinrichter - Installation ===" -ForegroundColor Cyan

if (-not (Test-Command node)) { throw "Node.js fehlt - bitte Node 20+ installieren" }
Write-Host "Node: $(node --version)"

Ensure-Pnpm
Ensure-Rust
Ensure-BuildTools
Ensure-Clone

if (-not $SkipBuild) {
    Build-Planova
}

$artifact = Find-BundleArtifact
if (-not $artifact) { throw "Kein Build-Artefakt gefunden. Build erneut ausfuehren." }
Write-Host "Artefakt: $artifact" -ForegroundColor DarkGray

Install-Artifact $artifact
$exe = Resolve-Executable
if (-not $exe) { throw "planova.exe nach Installation nicht gefunden" }
Write-Host "Executable: $exe" -ForegroundColor Green

New-Shortcuts $exe
Update-PathsJson $exe

Write-Host "`n=== Planova Installation abgeschlossen ===" -ForegroundColor Green
Write-Host "Starten: Desktop-Verknuepfung '$ShortcutName' oder: $exe"
