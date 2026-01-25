# test.ps1
# Test script that uploads result to VM1

param(
    [string]$ServerIP = "192.168.56.210",
    [int]$ServerPort = 8080
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$computer = $env:COMPUTERNAME
$user = whoami

# Create result message
$result = @"
========================================
Test Script Executed Successfully
========================================
Time:     $timestamp
Computer: $computer
User:     $user
========================================
"@

Write-Host $result -ForegroundColor Green

# Save to local file
$logPath = "C:\Windows\Temp\deployed\test-log.txt"
$result | Out-File $logPath -Append

Write-Host "[+] Log saved: $logPath" -ForegroundColor Cyan

# Upload result to VM1
try {
    Write-Host "[*] Uploading result to VM1..." -ForegroundColor Yellow
    
    $resultFilename = "result_${computer}_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    
    $boundary = [Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $body = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$resultFilename`"",
        "Content-Type: text/plain$LF",
        $result,
        "--$boundary--$LF"
    ) -join $LF
    
    Invoke-WebRequest -Uri "http://${ServerIP}:${ServerPort}/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body `
        -UseBasicParsing -TimeoutSec 5 | Out-Null
    
    Write-Host "[+] Result uploaded to VM1" -ForegroundColor Green
    
} catch {
    Write-Host "[-] Failed to upload result: $_" -ForegroundColor Red
}