# force-headset-mesh-only.ps1
# AudioRelay headset traffic MUST use Tailscale mesh (100.64.0.0/10) only — never LAN.
# Elevates for firewall if needed (UAC prompt).
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File workstation\force-headset-mesh-only.ps1
#   powershell -File workstation\force-headset-mesh-only.ps1 -NoElevate

param(
    [switch]$NoElevate,
    [switch]$NoRestartAudioRelay,
    [switch]$SkipRoute
)

$ErrorActionPreference = "Continue"
$Port = 59100
$MeshCidr = "100.64.0.0/10"   # Tailscale CGNAT
$LanCidrs = @("192.168.0.0/16", "172.16.0.0/12")
# Note: do NOT block all 10.0.0.0/8 — that would hit Tailscale 100.64/10
$RuleAllow = "Fusion-AudioRelay-MeshOnly-Allow-100"
$RuleBlockLan = "Fusion-AudioRelay-MeshOnly-Block-LAN"
$RuleBlockLegacy = "Fusion-AudioRelay-59100"  # broad allow from fix-headset — disable
$StateDir = Join-Path $env:USERPROFILE ".fusion"
$StateFile = Join-Path $StateDir "headset_mesh_only.json"
$TsExe = "C:\Program Files\Tailscale\tailscale.exe"
$Repo = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else {
    Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Test-IsAdmin {
    $p = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Step($name, $ok, $msg) {
    $mark = if ($ok) { "OK" } else { "!!" }
    Write-Host ("  [{0}] {1}: {2}" -f $mark, $name, $msg)
}

$Report = [ordered]@{
    ts = (Get-Date).ToString("o")
    policy = "mesh_only"
    platform = "v10.0.0"
    steps = [ordered]@{}
    ok = $false
}

Write-Host "=== FORCE HEADSET MESH-ONLY (Tailscale 100.x) ===" -ForegroundColor Cyan

# --- 1) Resolve mesh identities ---
$selfIp = $null
$phoneIp = $null
$phoneHost = $null
$selfHost = $null
if (Test-Path $TsExe) {
    try {
        $j = & $TsExe status --json 2>$null | ConvertFrom-Json
        $selfHost = [string]$j.Self.HostName
        $selfIps = @($j.Self.TailscaleIPs)
        $selfIp = ($selfIps | Where-Object { $_ -match '^100\.' } | Select-Object -First 1)
        if (-not $selfIp -and $selfIps.Count) { $selfIp = $selfIps[0] }
        foreach ($prop in $j.Peer.PSObject.Properties) {
            $p = $prop.Value
            $h = [string]$p.HostName
            $d = [string]$p.DNSName
            if ($h -match 'redmi|phone' -or $d -match 'redmi|phone') {
                $phoneHost = $h
                $phoneIps = @($p.TailscaleIPs)
                $phoneIp = ($phoneIps | Where-Object { $_ -match '^100\.' } | Select-Object -First 1)
                if (-not $phoneIp -and $phoneIps.Count) { $phoneIp = $phoneIps[0] }
                $phoneOnline = [bool]$p.Online
                break
            }
        }
        Write-Step "mesh_ids" $true "pc=$selfHost/$selfIp  phone=$phoneHost/$phoneIp online=$phoneOnline"
        $Report.steps.mesh_ids = @{
            ok = $true
            self_host = $selfHost
            self_ip = $selfIp
            phone_host = $phoneHost
            phone_ip = $phoneIp
            phone_online = $phoneOnline
        }
    } catch {
        Write-Step "mesh_ids" $false $_.Exception.Message
        $Report.steps.mesh_ids = @{ ok = $false; error = $_.Exception.Message }
    }
} else {
    Write-Step "mesh_ids" $false "tailscale.exe missing"
    $Report.steps.mesh_ids = @{ ok = $false; error = "no_tailscale" }
}

# --- 2) Tailscale profile Private ---
$tsProfile = Get-NetConnectionProfile -InterfaceAlias "Tailscale" -ErrorAction SilentlyContinue
if ($tsProfile -and $tsProfile.NetworkCategory -ne "Private") {
    try {
        Set-NetConnectionProfile -InterfaceAlias "Tailscale" -NetworkCategory Private -ErrorAction Stop
        Write-Step "tailscale_profile" $true "set Private"
        $Report.steps.tailscale_profile = @{ ok = $true; message = "Private" }
    } catch {
        Write-Step "tailscale_profile" $false "need Admin: $($_.Exception.Message)"
        $Report.steps.tailscale_profile = @{ ok = $false; error = $_.Exception.Message }
    }
} elseif ($tsProfile) {
    Write-Step "tailscale_profile" $true "already Private"
    $Report.steps.tailscale_profile = @{ ok = $true }
} else {
    Write-Step "tailscale_profile" $false "no Tailscale interface"
    $Report.steps.tailscale_profile = @{ ok = $false }
}

# --- 3) Firewall mesh-only (elevate if needed) ---
function Install-MeshOnlyFirewall {
    # Disable legacy broad allow
    Disable-NetFirewallRule -DisplayName $RuleBlockLegacy -ErrorAction SilentlyContinue
    Disable-NetFirewallRule -DisplayName "Fusion-AudioRelay-EXE" -ErrorAction SilentlyContinue

    # Allow ONLY Tailscale CGNAT -> local :59100
    if (Get-NetFirewallRule -DisplayName $RuleAllow -ErrorAction SilentlyContinue) {
        Remove-NetFirewallRule -DisplayName $RuleAllow -ErrorAction SilentlyContinue
    }
    New-NetFirewallRule -DisplayName $RuleAllow `
        -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port `
        -RemoteAddress $MeshCidr `
        -Profile Any `
        -Description "Fusion Hero OS: AudioRelay mesh-only allow (100.64.0.0/10)" `
        -ErrorAction Stop | Out-Null

    # Block classic LAN remotes on 59100
    if (Get-NetFirewallRule -DisplayName $RuleBlockLan -ErrorAction SilentlyContinue) {
        Remove-NetFirewallRule -DisplayName $RuleBlockLan -ErrorAction SilentlyContinue
    }
    New-NetFirewallRule -DisplayName $RuleBlockLan `
        -Direction Inbound -Action Block -Protocol TCP -LocalPort $Port `
        -RemoteAddress $LanCidrs `
        -Profile Any `
        -Description "Fusion Hero OS: AudioRelay block LAN (use Tailscale only)" `
        -ErrorAction Stop | Out-Null

    return $true
}

$fwOk = $false
if (Test-IsAdmin) {
    try {
        Install-MeshOnlyFirewall | Out-Null
        $fwOk = $true
        Write-Step "firewall_mesh_only" $true "allow $MeshCidr ; block LAN $($LanCidrs -join ',')"
        $Report.steps.firewall = @{ ok = $true; allow = $MeshCidr; block = $LanCidrs; elevated = $true }
    } catch {
        Write-Step "firewall_mesh_only" $false $_.Exception.Message
        $Report.steps.firewall = @{ ok = $false; error = $_.Exception.Message }
    }
} elseif (-not $NoElevate) {
    Write-Host "  [..] Elevating for firewall (UAC)..." -ForegroundColor Yellow
    $elevScript = @"
`$ErrorActionPreference = 'Stop'
`$Port = $Port
`$MeshCidr = '$MeshCidr'
`$LanCidrs = @('$($LanCidrs -join "','")')
`$RuleAllow = '$RuleAllow'
`$RuleBlockLan = '$RuleBlockLan'
`$RuleBlockLegacy = '$RuleBlockLegacy'
Disable-NetFirewallRule -DisplayName `$RuleBlockLegacy -ErrorAction SilentlyContinue
Disable-NetFirewallRule -DisplayName 'Fusion-AudioRelay-EXE' -ErrorAction SilentlyContinue
if (Get-NetFirewallRule -DisplayName `$RuleAllow -EA SilentlyContinue) { Remove-NetFirewallRule -DisplayName `$RuleAllow -EA SilentlyContinue }
New-NetFirewallRule -DisplayName `$RuleAllow -Direction Inbound -Action Allow -Protocol TCP -LocalPort `$Port -RemoteAddress `$MeshCidr -Profile Any -Description 'Fusion mesh-only allow' | Out-Null
if (Get-NetFirewallRule -DisplayName `$RuleBlockLan -EA SilentlyContinue) { Remove-NetFirewallRule -DisplayName `$RuleBlockLan -EA SilentlyContinue }
New-NetFirewallRule -DisplayName `$RuleBlockLan -Direction Inbound -Action Block -Protocol TCP -LocalPort `$Port -RemoteAddress `$LanCidrs -Profile Any -Description 'Fusion mesh-only block LAN' | Out-Null
'FIREWALL_MESH_ONLY_OK' | Set-Content -Path '$StateDir\firewall_mesh_only.flag' -Encoding ascii
"@
    $tmp = Join-Path $env:TEMP "fusion_mesh_only_fw.ps1"
    Set-Content -Path $tmp -Value $elevScript -Encoding UTF8
    try {
        $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $tmp
        ) -Wait -PassThru
        if (Test-Path "$StateDir\firewall_mesh_only.flag") {
            $fwOk = $true
            Remove-Item "$StateDir\firewall_mesh_only.flag" -Force -ErrorAction SilentlyContinue
            Write-Step "firewall_mesh_only" $true "elevated install OK (allow $MeshCidr, block LAN)"
            $Report.steps.firewall = @{ ok = $true; elevated = $true; allow = $MeshCidr; block = $LanCidrs }
        } else {
            Write-Step "firewall_mesh_only" $false "elevation failed or cancelled (exit $($p.ExitCode))"
            $Report.steps.firewall = @{ ok = $false; elevated = $false; exit = $p.ExitCode }
        }
    } catch {
        Write-Step "firewall_mesh_only" $false "UAC/elevation: $($_.Exception.Message)"
        $Report.steps.firewall = @{ ok = $false; error = $_.Exception.Message }
    }
} else {
    Write-Step "firewall_mesh_only" $false "skipped (NoElevate, not admin)"
    $Report.steps.firewall = @{ ok = $false; skipped = $true }
}

# --- 4) Drop LAN session: restart AudioRelay ---
$exe = @(
    "${env:ProgramFiles(x86)}\AudioRelay\AudioRelay.exe",
    "$env:ProgramFiles\AudioRelay\AudioRelay.exe",
    "$env:LOCALAPPDATA\Programs\AudioRelay\AudioRelay.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $NoRestartAudioRelay) {
    $procs = @(Get-Process -Name "AudioRelay","audiorelay-backend" -ErrorAction SilentlyContinue)
    if ($procs) {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    if ($exe) {
        Start-Process -FilePath $exe
        Start-Sleep -Seconds 3
        Write-Step "restart_audiorelay" $true "restarted (drops LAN ESTABLISHED)"
        $Report.steps.restart = @{ ok = $true; exe = $exe }
    } else {
        Write-Step "restart_audiorelay" $false "AudioRelay.exe not found"
        $Report.steps.restart = @{ ok = $false }
    }
} else {
    Write-Step "restart_audiorelay" $true "skipped"
    $Report.steps.restart = @{ ok = $true; skipped = $true }
}

# --- 5) Route speakers + layer state ---
if (-not $SkipRoute) {
    $fix = Join-Path $Repo "workstation\fix-headset-relay.ps1"
    if (Test-Path $fix) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $fix -NoRestartAudioRelay -SkipFirewall 2>&1 | Out-Null
    }
    $py = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
        "C:\Users\Admin\venv\Scripts\python.exe"
    } else { "python" }
    $env:PYTHONPATH = $Repo
    $env:FUSION_HEADSET_MESH_ONLY = "1"
    & $py -c @"
from fusion_hero_os.core.headset_layers import set_mesh_only, set_active, status
set_mesh_only(True)
r = set_active('L2_phone', apply_route=True)
s = status(apply_probe=True)
print(s.get('banner',''))
print(s.get('banner_one_line',''))
print('mesh_only', s.get('mesh_only'), 'link', (s.get('phone_link') or {}).get('link'))
print('connected', s.get('connected_to_phone'), 'mesh_ok', s.get('mesh_link_ok'))
"@ 2>&1
    Write-Step "layer_route" $true "L2_phone + mesh_only flag"
    $Report.steps.layer = @{ ok = $true; active = "L2_phone"; mesh_only = $true }
}

# --- 6) Snapshot connections ---
$conns = @(Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)
$listen = @($conns | Where-Object { $_.State -eq "Listen" }).Count
$estab = @($conns | Where-Object { $_.State -eq "Established" })
$meshEstab = @($estab | Where-Object { $_.RemoteAddress -match '^100\.' })
$lanEstab = @($estab | Where-Object { $_.RemoteAddress -match '^(192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)' })

Write-Host ""
Write-Host "  listen=$listen  established=$($estab.Count)  mesh_estab=$($meshEstab.Count)  lan_estab=$($lanEstab.Count)"
foreach ($e in $estab) {
    Write-Host ("    ESTABLISHED {0} -> {1}:{2}" -f $e.LocalAddress, $e.RemoteAddress, $e.RemotePort)
}

$Report.steps.ports = @{
    listen = $listen
    established = $estab.Count
    mesh_established = $meshEstab.Count
    lan_established = $lanEstab.Count
    remotes = @($estab | ForEach-Object { "$($_.RemoteAddress):$($_.RemotePort)" })
}

# Success criteria: firewall ok (or elevated), no LAN established, preferably mesh established
# After restart phone may need a few seconds to reconnect via mesh
$noLan = ($lanEstab.Count -eq 0)
$Report.ok = $fwOk -and $noLan
$Report.self_ip = $selfIp
$Report.phone_ip = $phoneIp
$Report.connect_hint = if ($selfIp) {
    "On phone AudioRelay: connect to MESH IP $selfIp (or MagicDNS $selfHost) port $Port - NOT LAN 192.168.x"
} else {
    "On phone AudioRelay: connect via Tailscale IP of PC, not LAN"
}

$Report | ConvertTo-Json -Depth 6 | Set-Content -Path $StateFile -Encoding UTF8

Write-Host ""
if ($Report.ok -and $meshEstab.Count -gt 0) {
    Write-Host "=== RESULT: MESH-ONLY ACTIVE (session on 100.x) ===" -ForegroundColor Green
} elseif ($Report.ok -and $meshEstab.Count -eq 0) {
    Write-Host "=== RESULT: LAN BLOCKED - reconnect phone via mesh ===" -ForegroundColor Yellow
    Write-Host $Report.connect_hint -ForegroundColor Yellow
} else {
    Write-Host "=== RESULT: PARTIAL ===" -ForegroundColor Yellow
    Write-Host $Report.connect_hint -ForegroundColor Yellow
    if (-not $fwOk) {
        Write-Host "  Re-run elevated: powershell -File workstation\force-headset-mesh-only.ps1" -ForegroundColor Yellow
    }
}
Write-Host "State: $StateFile"
exit $(if ($Report.ok) { 0 } else { 2 })
