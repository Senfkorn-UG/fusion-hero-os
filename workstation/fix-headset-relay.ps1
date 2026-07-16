# fix-headset-relay.ps1 — FULL AUTO repair of PC→phone headset (AudioRelay)
# No operator interaction required. Idempotent.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File workstation\fix-headset-relay.ps1

param(
    [switch]$SkipFirewall,
    [switch]$NoRestartAudioRelay
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
$RepoRoot  = Split-Path -Parent $ScriptDir
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

# ---------------------------------------------------------------------------
# 1) Locate AudioRelay.exe
# ---------------------------------------------------------------------------
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
    Write-Step "locate_audiorelay" @{ ok = $false; error = "AudioRelay.exe not found — install from https://audiorelay.net" }
}

# ---------------------------------------------------------------------------
# 2) Ensure AudioRelay process running
# ---------------------------------------------------------------------------
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
    if ($NoRestartAudioRelay) {
        Write-Step "start_audiorelay" @{ ok = $true; message = "already running PID $($procs.Id -join ',')"; pids = @($procs.Id) }
    } else {
        # Soft: leave running (connection may be active). Only restart if port dead.
        $listen = Get-NetTCPConnection -LocalPort 59100 -State Listen -ErrorAction SilentlyContinue
        if (-not $listen) {
            Write-Host "  Port 59100 not listening — restarting AudioRelay..." -ForegroundColor Yellow
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            if ($exe) {
                Start-Process -FilePath $exe
                Start-Sleep -Seconds 3
            }
            $procs = @(Get-Process -Name "AudioRelay","audiorelay-backend" -ErrorAction SilentlyContinue)
            Write-Step "start_audiorelay" @{
                ok = ($procs.Count -gt 0)
                message = "restarted; PID $($procs.Id -join ',')"
                pids = @($procs.Id)
            }
        } else {
            Write-Step "start_audiorelay" @{
                ok = $true
                message = "running + port 59100 Listen (PID $($procs.Id -join ','))"
                pids = @($procs.Id)
            }
        }
    }
} else {
    Write-Step "start_audiorelay" @{ ok = $false; error = "cannot start — no exe" }
}

# ---------------------------------------------------------------------------
# 3) Tailscale Private profile + phone peer
# ---------------------------------------------------------------------------
$tsProfile = Get-NetConnectionProfile -InterfaceAlias "Tailscale" -ErrorAction SilentlyContinue
if ($tsProfile) {
    if ($tsProfile.NetworkCategory -ne "Private") {
        try {
            Set-NetConnectionProfile -InterfaceAlias "Tailscale" -NetworkCategory Private -ErrorAction Stop
            Write-Step "tailscale_profile" @{ ok = $true; message = "set Private (was $($tsProfile.NetworkCategory))" }
        } catch {
            Write-Step "tailscale_profile" @{
                ok = $false
                error = "need elevation: Set-NetConnectionProfile -InterfaceAlias Tailscale -NetworkCategory Private"
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

# ---------------------------------------------------------------------------
# 4) Firewall: allow TCP 59100 (AudioRelay) on Private + Tailscale
# ---------------------------------------------------------------------------
if (-not $SkipFirewall) {
    $ruleName = "Fusion-AudioRelay-59100"
    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    try {
        if (-not $existing) {
            New-NetFirewallRule -DisplayName $ruleName `
                -Direction Inbound -Action Allow -Protocol TCP -LocalPort 59100 `
                -Profile Private,Domain -Program "Any" -ErrorAction Stop | Out-Null
            Write-Step "firewall" @{ ok = $true; message = "created $ruleName TCP 59100 Private/Domain" }
        } else {
            Enable-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            Write-Step "firewall" @{ ok = $true; message = "rule exists + enabled" }
        }
        # Also allow for any program path under AudioRelay install if we can
        if ($exe) {
            $ruleProg = "Fusion-AudioRelay-EXE"
            if (-not (Get-NetFirewallRule -DisplayName $ruleProg -ErrorAction SilentlyContinue)) {
                New-NetFirewallRule -DisplayName $ruleProg `
                    -Direction Inbound -Action Allow -Program $exe `
                    -Profile Private,Domain -ErrorAction SilentlyContinue | Out-Null
            }
        }
    } catch {
        Write-Step "firewall" @{
            ok = $false
            error = "firewall change needs Admin: $($_.Exception.Message)"
            hint = "Re-run elevated once; LAN may still work"
        }
    }
}

# ---------------------------------------------------------------------------
# 5) Discover Virtual Speakers / Virtual Mic (current machine GUIDs)
# ---------------------------------------------------------------------------
$virtualSpeakersName = "Virtual Speakers for AudioRelay"
$virtualMicName      = "Virtual Mic for AudioRelay"
$speakerItemId = $null
$micItemId = $null

if (Test-Path $Svv) {
    $tsv = Join-Path $StateDir "audio_devices_live.tsv"
    & $Svv /stab $tsv 2>$null | Out-Null
    Start-Sleep -Milliseconds 400
    if (Test-Path $tsv) {
        $lines = Get-Content $tsv -Encoding UTF8
        # header is tab-separated; find Device rows with AudioRelay
        foreach ($line in $lines) {
            if ($line -match 'Virtual Speakers for AudioRelay' -and $line -match 'Device' -and $line -match 'Render') {
                if ($line -match '\{0\.0\.0\.00000000\}\.\{[0-9A-Fa-f\-]+\}') {
                    $speakerItemId = $Matches[0]
                }
            }
            if ($line -match 'Virtual Mic for AudioRelay' -and $line -match 'Device' -and $line -match 'Capture') {
                if ($line -match '\{0\.0\.1\.00000000\}\.\{[0-9A-Fa-f\-]+\}') {
                    $micItemId = $Matches[0]
                }
            }
        }
    }
    # PnP fallback for speaker GUID
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
        message = "speakers=$speakerItemId mic=$micItemId"
        speakers_name = $virtualSpeakersName
        speakers_id = $speakerItemId
        mic_id = $micItemId
    }
} else {
    Write-Step "discover_devices" @{ ok = $false; error = "SoundVolumeView.exe missing at $Svv" }
}

# ---------------------------------------------------------------------------
# 6) Set default PLAYBACK → Virtual Speakers (all roles)
# ---------------------------------------------------------------------------
$routed = $false
if (Test-Path $Svv) {
    # Unmute + volume 100% first
    & $Svv /Unmute $virtualSpeakersName 2>$null | Out-Null
    & $Svv /SetVolume $virtualSpeakersName 100 2>$null | Out-Null

    foreach ($target in @($virtualSpeakersName, $speakerItemId)) {
        if (-not $target) { continue }
        & $Svv /SetDefault $target all 2>$null | Out-Null
        Start-Sleep -Milliseconds 600
        # Verify via CSV export
        $csv = Join-Path $StateDir "audio_devices_check.csv"
        & $Svv /scomma $csv 2>$null | Out-Null
        Start-Sleep -Milliseconds 300
        if (Test-Path $csv) {
            $rows = Import-Csv $csv -ErrorAction SilentlyContinue
            $def = $rows | Where-Object {
                $_.Type -eq 'Device' -and $_.Direction -eq 'Render' -and
                ($_.Default -eq 'Render' -or $_.'Default Multimedia' -eq 'Render')
            } | Select-Object -First 1
            if ($def -and ($def.'Device Name' -match 'AudioRelay' -or $def.Name -match 'Virtual Speakers|AudioRelay')) {
                $routed = $true
                Write-Step "route_speakers" @{
                    ok = $true
                    message = "default render -> $($def.Name) / $($def.'Device Name')"
                    device = $def.Name
                    via = $target
                }
                break
            }
            # Also check Name field alone
            $def2 = $rows | Where-Object {
                $_.Type -eq 'Device' -and $_.Direction -eq 'Render' -and
                $_.Name -match 'Virtual Speakers' -and
                ($_.Default -match 'Render' -or $_.'Default Multimedia' -match 'Render')
            } | Select-Object -First 1
            if ($def2) {
                $routed = $true
                Write-Step "route_speakers" @{
                    ok = $true
                    message = "default render -> $($def2.Name)"
                    device = $def2.Name
                    via = $target
                }
                break
            }
        }
    }
    if (-not $routed) {
        # Try Item ID form with \Device path
        if ($speakerItemId) {
            & $Svv /SetDefault $speakerItemId all 2>$null | Out-Null
            & $Svv /SetDefault "$virtualSpeakersName\Device\Virtual Speakers\Render" all 2>$null | Out-Null
            Start-Sleep -Milliseconds 800
        }
        # Final check: Command-Line Friendly ID style
        & $Svv /SetDefault "Virtual Speakers for AudioRelay\Device\Virtual Speakers\Render" all 2>$null | Out-Null
        Start-Sleep -Milliseconds 500
        $csv = Join-Path $StateDir "audio_devices_check.csv"
        & $Svv /scomma $csv 2>$null | Out-Null
        $rows = Import-Csv $csv -ErrorAction SilentlyContinue
        $def = $rows | Where-Object {
            $_.Type -eq 'Device' -and $_.Direction -eq 'Render' -and
            ($_.Default -eq 'Render' -or $_.'Default Multimedia' -eq 'Render')
        } | Select-Object -First 1
        $isAr = $def -and ($def.Name -match 'Virtual Speakers|AudioRelay' -or $def.'Device Name' -match 'AudioRelay')
        Write-Step "route_speakers" @{
            ok = [bool]$isAr
            message = if ($isAr) { "default -> $($def.Name)" } else { "still on $($def.Name) $($def.'Device Name') — forced SetDefault attempted" }
            device = $def.Name
            device_name = $def.'Device Name'
            default = $def.Default
        }
        $routed = [bool]$isAr
    }
} else {
    Write-Step "route_speakers" @{ ok = $false; error = "no SoundVolumeView" }
}

# ---------------------------------------------------------------------------
# 7) Port / connection status
# ---------------------------------------------------------------------------
$listen = @(Get-NetTCPConnection -LocalPort 59100 -State Listen -ErrorAction SilentlyContinue)
$estab  = @(Get-NetTCPConnection -LocalPort 59100 -State Established -ErrorAction SilentlyContinue)
Write-Step "port_59100" @{
    ok = ($listen.Count -gt 0)
    message = "listen=$($listen.Count) established=$($estab.Count)"
    established_remote = @($estab | ForEach-Object { "$($_.RemoteAddress):$($_.RemotePort)" })
}

# ---------------------------------------------------------------------------
# 8) Optional: play brief system beep to Virtual Speakers path (proves route)
# ---------------------------------------------------------------------------
try {
    # .NET console beep uses default device after SetDefault
    [console]::Beep(880, 180)
    Start-Sleep -Milliseconds 50
    [console]::Beep(1175, 220)
    Write-Step "probe_tone" @{ ok = $true; message = "880+1175 Hz beep on default device" }
} catch {
    Write-Step "probe_tone" @{ ok = $false; error = $_.Exception.Message }
}

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------
$need = @("start_audiorelay", "route_speakers", "port_59100")
$Report.ok = ($need | ForEach-Object { $Report.steps[$_].ok }) -notcontains $false
$Report.phone = $phone
$Report.summary = if ($Report.ok) {
    "Headset relay path armed: AudioRelay up, default speakers = Virtual Speakers, port 59100 listening."
} else {
    "Partial repair — see steps. Phone app must have Playback ON if established=0."
}

$Report | ConvertTo-Json -Depth 8 | Set-Content -Path $StateFile -Encoding UTF8
Write-Host ""
if ($Report.ok) {
    Write-Host "=== RESULT: OK ===" -ForegroundColor Green
} else {
    Write-Host "=== RESULT: PARTIAL / NEEDS PHONE SIDE ===" -ForegroundColor Yellow
}
Write-Host $Report.summary
Write-Host "State: $StateFile"
Write-Host ""
Write-Host "Phone side (only if established=0): AudioRelay Android → connect PC → Playback aktiv"
exit $(if ($Report.ok) { 0 } else { 2 })
