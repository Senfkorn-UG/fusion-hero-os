# install-planova.ps1 — Planova Inneneinrichter (Tauri) auf Windows installieren
param(
    [switch]$SkipBuild,
    [switch]$ForceDeps,
    [switch]$Background,
    [switch]$PollOnly
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")
$ErrorActionPreference = "Continue"

$CloneDir   = Join-Path $env:USERPROFILE "src\planova"
$InstallDir = Join-Path $env:USERPROFILE "Programs\planova"
$ShortcutName = "Planova Inneneinrichter"
$RepoUrl    = "https://github.com/XUranus/planova.git"
$PathsFile  = Join-Path $PSScriptRoot "paths.json"
$StatusFile = Join-Path $env:USERPROFILE ".fusion\planova-install.status.json"
$MingwRoot  = Join-Path $env:USERPROFILE "mingw64"

function Write-Step([string]$Msg) {
    Write-Host "`n=== $Msg ===" -ForegroundColor Cyan
}

function Write-Status([string]$Phase, [string]$Message, [string]$State = "running") {
    $dir = Split-Path $StatusFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    @{
        phase     = $Phase
        message   = $Message
        state     = $State
        updated   = (Get-Date).ToString("o")
        install_dir = $InstallDir
        clone_dir = $CloneDir
    } | ConvertTo-Json | Set-Content $StatusFile -Encoding UTF8
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-CargoPath {
    $cargo = Join-Path $env:USERPROFILE ".cargo\bin"
    if ((Test-Path $cargo) -and ($env:Path -notlike "*$cargo*")) {
        $env:Path = "$cargo;$env:Path"
    }
}

function Ensure-Pnpm {
    if (Test-Command pnpm) { return }
    Write-Step "pnpm installieren"
    npm install -g pnpm
    if (-not (Test-Command pnpm)) { throw "pnpm konnte nicht installiert werden" }
}

function Ensure-Rust {
    Ensure-CargoPath
    if ((Test-Command rustc) -and -not $ForceDeps) { return }
    Write-Step "Rust installieren (rustup)"
    $installer = Join-Path $env:TEMP "rustup-init.exe"
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $installer -UseBasicParsing
    & $installer -y --default-toolchain stable --profile minimal
    Ensure-CargoPath
    if (-not (Test-Command rustc)) { throw "Rust konnte nicht installiert werden" }
}

function Test-MsvcReady {
    if (Test-Command cl) { return $true }
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) { return $false }
    $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if (-not $installPath) { return $false }
    return (Test-Path (Join-Path $installPath "VC\Auxiliary\Build\vcvars64.bat"))
}

function Test-MingwReady {
    if (Test-Command dlltool) { return $true }
    $candidates = @(
        (Join-Path $MingwRoot "bin\dlltool.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\dlltool.exe")
    )
    foreach ($wingetPkg in (Get-ChildItem (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages") -Filter "*WinLibs*" -Directory -ErrorAction SilentlyContinue)) {
        $candidates += (Join-Path $wingetPkg.FullName "mingw64\bin\dlltool.exe")
    }
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $bin = Split-Path $c -Parent
            if ($env:Path -notlike "*$bin*") { $env:Path = "$bin;$env:Path" }
            return $true
        }
    }
    return $false
}

function Ensure-MingwPath {
    if (Test-MingwReady) { return $true }
    if (Test-Path (Join-Path $MingwRoot "bin\dlltool.exe")) {
        $env:Path = "$(Join-Path $MingwRoot 'bin');$env:Path"
        return $true
    }
    return $false
}

function Start-MingwInstall {
    Write-Status "deps" "MinGW (WinLibs) wird installiert..."
    $log = Join-Path (Split-Path $StatusFile -Parent) "winlibs-install.log"
    $err = "$log.err"
    if (Get-Process winget -ErrorAction SilentlyContinue) {
        Write-Host "  winget laeuft bereits (WinLibs?)" -ForegroundColor DarkGray
        return
    }
    Start-Process -FilePath winget -ArgumentList @(
        "install", "--id", "BrechtSanders.WinLibs.POSIX.UCRT", "-e",
        "--accept-package-agreements", "--accept-source-agreements"
    ) -RedirectStandardOutput $log -RedirectStandardError $err -NoNewWindow | Out-Null
}

function Ensure-Linker {
    Ensure-CargoPath
    Write-Step "Linker / Build-Tools pruefen"

    if (Test-MsvcReady) {
        Write-Host "  MSVC Build Tools gefunden" -ForegroundColor Green
        & rustup toolchain install stable-x86_64-pc-windows-msvc 2>&1 | ForEach-Object { Write-Host $_ }
        & rustup default stable-x86_64-pc-windows-msvc 2>&1 | ForEach-Object { Write-Host $_ }
        return
    }

    if (Ensure-MingwPath) {
        Write-Host "  MinGW (dlltool) gefunden" -ForegroundColor Green
        & rustup toolchain install stable-x86_64-pc-windows-gnu 2>&1 | ForEach-Object { Write-Host $_ }
        & rustup default stable-x86_64-pc-windows-gnu 2>&1 | ForEach-Object { Write-Host $_ }
        return
    }

    Write-Host "  MinGW fehlt — starte WinLibs-Installation (Hintergrund moeglich)" -ForegroundColor Yellow
    Start-MingwInstall
    throw "MinGW noch nicht bereit. Erneut ausfuehren wenn winget fertig ist, oder: winget install BrechtSanders.WinLibs.POSIX.UCRT"
}

function Ensure-PlanovaPatches {
    Write-Step "Planova Build-Patches"
    $ws = Join-Path $CloneDir "pnpm-workspace.yaml"
    if (-not (Test-Path $ws)) {
        "allowBuilds:`n  msw: true`n" | Set-Content $ws -Encoding UTF8
    } elseif ((Get-Content $ws -Raw) -notmatch "msw:\s*true") {
        Add-Content $ws "`nallowBuilds:`n  msw: true"
    }

    $pkg = Join-Path $CloneDir "package.json"
    if (Test-Path $pkg) {
        $j = Get-Content $pkg -Raw | ConvertFrom-Json
        if ($j.scripts.build -match "tsc") {
            $j.scripts.build = "vite build"
            $j | ConvertTo-Json -Depth 20 | Set-Content $pkg -Encoding UTF8
            Write-Host "  package.json: build -> vite build" -ForegroundColor DarkGray
        }
    }
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
    Ensure-PlanovaPatches
}

function Build-Planova {
    Write-Step "Planova bauen (pnpm tauri build - kann 10-20 Min. dauern)"
    Write-Status "build" "pnpm tauri build laeuft..."
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

function Invoke-PlanovaInstall {
    Write-Host "=== Planova Inneneinrichter - Installation ===" -ForegroundColor Cyan
    Write-Status "start" "Installation gestartet"

    if (-not (Test-Command node)) { throw "Node.js fehlt - bitte Node 20+ installieren" }
    Write-Host "Node: $(node --version)"

    Ensure-Pnpm
    Ensure-Rust
    Ensure-Linker
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
    Write-Status "done" "Installation abgeschlossen" "success"

    Write-Host "`n=== Planova Installation abgeschlossen ===" -ForegroundColor Green
    Write-Host "Starten: Desktop-Verknuepfung '$ShortcutName' oder: $exe"
}

if ($PollOnly) {
    if (Test-Path $StatusFile) { Get-Content $StatusFile -Raw } else { Write-Host '{"state":"unknown"}' }
    exit 0
}

if ($Background) {
    $log = Join-Path (Split-Path $StatusFile -Parent) "planova-install.log"
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $MyInvocation.MyCommand.Path)
    if ($SkipBuild) { $args += "-SkipBuild" }
    if ($ForceDeps) { $args += "-ForceDeps" }
    Write-Status "queued" "Hintergrund-Installation gestartet"
    Start-Process powershell.exe -ArgumentList $args -RedirectStandardOutput $log -RedirectStandardError "$log.err" -NoNewWindow
    Write-Host "Hintergrund-Job gestartet. Status: $StatusFile"
    exit 0
}

try {
    Invoke-PlanovaInstall
} catch {
    Write-Status "error" $_.Exception.Message "failed"
    throw
}
