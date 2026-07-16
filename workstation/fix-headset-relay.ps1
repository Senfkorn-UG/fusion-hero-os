# fix-headset-relay.ps1 - FULL AUTO repair of PC to phone headset (AudioRelay)
# No operator interaction required. Idempotent.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File workstation\fix-headset-relay.ps1

param(
    [switch]$SkipFirewall,
    [switch]$NoRestartAudioRelay,
    [switch]$MeshOnly
)

$ErrorActionPreference = "Continue"
$Report = [ordered]@{
    ts           = (Get-Date).ToString("o")
    platform     = "v10.0.0"
    channel      = "bluetooth-audio-relay / AudioRelay headset"
    steps        = [ordered]@{}
    ok           = $false
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Svv       = Join-Path $ScriptDir "tools\SoundVolumeView.exe"
$StateDir  = Join-Path $env:USERPROFILE ".fusion"
$StateFile = Join-Path $StateDir "headset_relay.json"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Write-Step($name, $obj) {
    $Report.steps[$name] = $obj
    $mark = if ($obj.ok) { "OK" } else { "!!" }
    $msg  = if ($obj.message) { $obj.message } elseif ($obj.error) { $obj.error } else { ($obj | ConvertTo-Json -Compress) }
    Write-Host ("  [{0}] {1}: {2}" -f $mark, $name, $msg)
}

Write-Host "=== FIX HEADSET RELAY (auto) ===" -ForegroundColor Cyan

# Optional: mesh-only enforcement first (Tailscale 100.x, never LAN)
if ($MeshOnly) {
    $meshScript = Join-Path $ScriptDir "force-headset-mesh-only.ps1"
    if (Test-Path $meshScript) {
        Write-Host "  [..] MeshOnly: delegating to force-headset-mesh-only.ps1" -ForegroundColor Magenta
        & powershell -NoProfile -ExecutionPolicy Bypass -File $meshScript -NoRestartAudioRelay:$NoRestartAudioRelay
        exit $LASTEXITCODE
    }
}

# 1) Locate AudioRelay.exe
$candidates = @(
    "${env:ProgramFiles(x86)}\AudioRelay\AudioRelay.exe",
    "$env:ProgramFiles\AudioRelay\AudioRelay.exe",
    "$env:LOCALAPPDATA\Programs\AudioRelay\AudioRelay.exe",
    "$env:LOCALAPPDATA\AudioRelay\AudioRelay.exe"
)
$exe = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $exe) {
    $found = Get-ChildItem -Path "$env:LOCALAPPDATA","$env:ProgramFiles","${env:ProgramFiles(x86)}" `
        -Recurse -Filter "AudioRelay.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    if ($found) { $exe = $found }
}
if ($exe) {
    Write-Step "locate_audiorelay" @{ ok = $true; message = $exe; exe = $exe }
} else {
    Write-Step "locate_audiorelay" @{ ok = $false; error = "AudioRelay.exe not found - install from https://audiorelay.net" }
}

# 2) Ensure AudioRelay process running
$procs = @(Get-Process -Name "AudioRelay","audiorelay-backend" -ErrorAction SilentlyContinue)
if ($procs.Count -eq 0 -and $exe) {
    try {
        Start-Process -FilePath $exe
        Start-Sleep -Seconds 3
        $procs = @(Get-Process -Name "AudioRelay","audiorelay-backend" -ErrorAction SilentlyContinue)
        Write-Step "start_audiorelay" @{
            ok = ($procs.Count -gt 0)
            message = if ($procs.Count -gt 0) { "started PID $($procs.Id -join ',')" } else { "start issued but process not visible yet" }
            pids = @($procs.Id)
        }
    } catch {
        Write-Step "start_audiorelay" @{ ok = $false; error = $_.Exception.Message }
    }
} elseif ($procs.Count -gt 0) {
    $listen = Get-NetTCPConnection -LocalPort 59100 -State Listen -ErrorAction SilentlyContinue
    if ((-not $listen) -and (-not $NoRestartAudioRelay) -and $exe) {
        Write-Host "  Port 59100 not listening - restarting AudioRelay..." -ForegroundColor Yellow
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        Start-Process -FilePath $exe
        Start-Sleep -Seconds 3
        $procs = @(Get-Process -Name "AudioRelay","audiorelay-backend" -ErrorAction SilentlyContinue)
        Write-Step "start_audiorelay" @{
            ok = ($procs.Count -gt 0)
            message = "restarted; PID $($procs.Id -join ',')"
            pids = @($procs.Id)
        }
    } else {
        Write-Step "start_audiorelay" @{
            ok = $true
            message = "running PID $($procs.Id -join ',') port59100_listen=$([bool]$listen)"
            pids = @($procs.Id)
        }
    }
} else {
    Write-Step "start_audiorelay" @{ ok = $false; error = "cannot start - no exe" }
}

# 3) Tailscale Private profile + phone peer
$tsProfile = Get-NetConnectionProfile -InterfaceAlias "Tailscale" -ErrorAction SilentlyContinue
if ($tsProfile) {
    if ($tsProfile.NetworkCategory -ne "Private") {
        try {
            Set-NetConnectionProfile -InterfaceAlias "Tailscale" -NetworkCategory Private -ErrorAction Stop
            Write-Step "tailscale_profile" @{ ok = $true; message = "set Private (was $($tsProfile.NetworkCategory))" }
        } catch {
            Write-Step "tailscale_profile" @{
                ok = $false
                error = "need elevation for Set-NetConnectionProfile"
                current = [string]$tsProfile.NetworkCategory
            }
        }
    } else {
        Write-Step "tailscale_profile" @{ ok = $true; message = "already Private" }
    }
} else {
    Write-Step "tailscale_profile" @{ ok = $false; error = "no Tailscale interface" }
}

$phone = $null
$tsExe = "C:\Program Files\Tailscale\tailscale.exe"
if (Test-Path $tsExe) {
    try {
        $tsJson = & $tsExe status --json 2>$null | ConvertFrom-Json
        foreach ($prop in $tsJson.Peer.PSObject.Properties) {
            $p = $prop.Value
            $h = [string]$p.HostName
            $d = [string]$p.DNSName
            if ($h -match 'redmi|phone' -or $d -match 'redmi|phone') {
                $phone = @{
                    host    = $h
                    online  = [bool]$p.Online
                    ips     = @($p.TailscaleIPs)
                    dns     = $d
                }
                break
            }
        }
        if ($phone) {
            Write-Step "phone_peer" @{
                ok = [bool]$phone.online
                message = "$($phone.host) online=$($phone.online) ips=$($phone.ips -join ',')"
                phone = $phone
            }
        } else {
            Write-Step "phone_peer" @{ ok = $false; error = "no redmi/phone peer in tailnet" }
        }
    } catch {
        Write-Step "phone_peer" @{ ok = $false; error = $_.Exception.Message }
    }
} else {
    Write-Step "phone_peer" @{ ok = $false; error = "tailscale.exe missing" }
}

# 4) Firewall TCP 59100
if (-not $SkipFirewall) {
    $ruleName = "Fusion-AudioRelay-59100"
    try {
        if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $ruleName `
                -Direction Inbound -Action Allow -Protocol TCP -LocalPort 59100 `
                -Profile Private,Domain -ErrorAction Stop | Out-Null
            Write-Step "firewall" @{ ok = $true; message = "created $ruleName TCP 59100" }
        } else {
            Enable-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            Write-Step "firewall" @{ ok = $true; message = "rule exists + enabled" }
        }
        if ($exe -and -not (Get-NetFirewallRule -DisplayName "Fusion-AudioRelay-EXE" -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName "Fusion-AudioRelay-EXE" `
                -Direction Inbound -Action Allow -Program $exe `
                -Profile Private,Domain -ErrorAction SilentlyContinue | Out-Null
        }
    } catch {
        Write-Step "firewall" @{
            ok = $false
            error = "firewall needs Admin: $($_.Exception.Message)"
        }
    }
}

# 5) Discover Virtual Speakers GUID (machine-specific)
$virtualSpeakersName = "Virtual Speakers for AudioRelay"
$speakerItemId = $null
if (Test-Path $Svv) {
    $tsv = Join-Path $StateDir "audio_devices_live.tsv"
    & $Svv /stab $tsv 2>$null | Out-Null
    Start-Sleep -Milliseconds 400
    if (Test-Path $tsv) {
        foreach ($line in (Get-Content $tsv -Encoding UTF8)) {
            if ($line -match 'Virtual Speakers for AudioRelay' -and $line -match 'Device' -and $line -match 'Render') {
                if ($line -match '\{0\.0\.0\.00000000\}\.\{[0-9A-Fa-f\-]+\}') {
                    $speakerItemId = $Matches[0]
                }
            }
        }
    }
    if (-not $speakerItemId) {
        $pnp = Get-PnpDevice -Class AudioEndpoint -ErrorAction SilentlyContinue |
            Where-Object { $_.FriendlyName -match 'Virtual Speakers' -and $_.Status -eq 'OK' } |
            Select-Object -First 1
        if ($pnp -and $pnp.InstanceId -match '\{0\.0\.0\.00000000\}\.\{[0-9A-Fa-f\-]+\}') {
            $speakerItemId = $Matches[0]
        }
    }
    Write-Step "discover_devices" @{
        ok = [bool]$speakerItemId
        message = "speakers_id=$speakerItemId"
        speakers_name = $virtualSpeakersName
        speakers_id = $speakerItemId
    }
} else {
    Write-Step "discover_devices" @{ ok = $false; error = "SoundVolumeView.exe missing at $Svv" }
}

# 6) Route default PLAYBACK to Virtual Speakers
function Get-DefaultRenderDevice {
    param([string]$CsvPath)
    if (-not (Test-Path $CsvPath)) { return $null }
    $rows = Import-Csv $CsvPath -ErrorAction SilentlyContinue
    return $rows | Where-Object {
        $_.Type -eq 'Device' -and $_.Direction -eq 'Render' -and
        ($_.Default -eq 'Render' -or $_.'Default Multimedia' -eq 'Render' -or $_.Default -match 'Render')
    } | Select-Object -First 1
}

function Test-IsAudioRelayDefault {
    param($dev)
    if (-not $dev) { return $false }
    return (
        ($dev.Name -match 'Virtual Speakers|AudioRelay') -or
        ($dev.'Device Name' -match 'AudioRelay|Virtual Speakers')
    )
}

$routed = $false
if (Test-Path $Svv) {
    & $Svv /Unmute $virtualSpeakersName 2>$null | Out-Null
    & $Svv /SetVolume $virtualSpeakersName 100 2>$null | Out-Null
    if ($speakerItemId) {
        & $Svv /Unmute $speakerItemId 2>$null | Out-Null
        & $Svv /SetVolume $speakerItemId 100 2>$null | Out-Null
    }

    $targets = @(
        $virtualSpeakersName,
        $speakerItemId,
        "Virtual Speakers for AudioRelay\Device\Virtual Speakers\Render",
        "Virtual Speakers (Virtual Speakers for AudioRelay)"
    ) | Where-Object { $_ }

    $csv = Join-Path $StateDir "audio_devices_check.csv"
    foreach ($target in $targets) {
        & $Svv /SetDefault $target all 2>$null | Out-Null
        Start-Sleep -Milliseconds 700
        & $Svv /scomma $csv 2>$null | Out-Null
        Start-Sleep -Milliseconds 250
        $def = Get-DefaultRenderDevice -CsvPath $csv
        if (Test-IsAudioRelayDefault $def) {
            $routed = $true
            Write-Step "route_speakers" @{
                ok = $true
                message = "default render -> $($def.Name) / $($def.'Device Name')"
                device = $def.Name
                via = $target
            }
            break
        }
    }

    if (-not $routed) {
        $def = Get-DefaultRenderDevice -CsvPath $csv
        Write-Step "route_speakers" @{
            ok = $false
            error = "could not set Virtual Speakers as default"
            current = if ($def) { "$($def.Name) | $($def.'Device Name')" } else { "unknown" }
        }
    }
} else {
    Write-Step "route_speakers" @{ ok = $false; error = "no SoundVolumeView" }
}

# 7) Port status
$listen = @(Get-NetTCPConnection -LocalPort 59100 -State Listen -ErrorAction SilentlyContinue)
$estab  = @(Get-NetTCPConnection -LocalPort 59100 -State Established -ErrorAction SilentlyContinue)
Write-Step "port_59100" @{
    ok = ($listen.Count -gt 0)
    message = "listen=$($listen.Count) established=$($estab.Count)"
    established_remote = @($estab | ForEach-Object { "$($_.RemoteAddress):$($_.RemotePort)" })
}

# 8) Probe tone on default device
try {
    [console]::Beep(880, 180)
    Start-Sleep -Milliseconds 40
    [console]::Beep(1175, 220)
    Write-Step "probe_tone" @{ ok = $true; message = "880+1175 Hz beep sent" }
} catch {
    Write-Step "probe_tone" @{ ok = $false; error = $_.Exception.Message }
}

# Aggregate: core path
$coreOk = $true
foreach ($k in @("start_audiorelay", "route_speakers", "port_59100")) {
    if (-not $Report.steps[$k].ok) { $coreOk = $false }
}
$Report.ok = $coreOk
$Report.phone = $phone
if ($Report.ok) {
    $Report.summary = "Headset relay armed: AudioRelay up, default=Virtual Speakers, port 59100 listening."
} else {
    $Report.summary = "Partial repair - see steps. If established=0 open AudioRelay on phone and enable Playback."
}

$Report | ConvertTo-Json -Depth 8 | Set-Content -Path $StateFile -Encoding UTF8
Write-Host ""
if ($Report.ok) {
    Write-Host "=== RESULT: OK ===" -ForegroundColor Green
} else {
    Write-Host "=== RESULT: PARTIAL ===" -ForegroundColor Yellow
}
Write-Host $Report.summary
Write-Host "State: $StateFile"
exit $(if ($Report.ok) { 0 } else { 2 })
