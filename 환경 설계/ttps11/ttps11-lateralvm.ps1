# Agent.ps1
# Client Agent

param(
    [int]$Port = 8081,
    [string]$DownloadPath = "C:\Users\Public"
)

$ErrorActionPreference = "Continue"

if (!(Test-Path $DownloadPath)) {
    New-Item -ItemType Directory -Path $DownloadPath -Force | Out-Null
}

$listener = New-Object System.Net.HttpListener

try {
    $listener.Prefixes.Add("http://+:$Port/")
    $listener.Start()
    
    Write-Host "`n[+] Agent started on port $Port" -ForegroundColor Green
    Write-Host "[*] Computer: $env:COMPUTERNAME" -ForegroundColor Cyan
    Write-Host "[*] User: $(whoami)" -ForegroundColor Cyan
    Write-Host "[*] Download path: $DownloadPath" -ForegroundColor Yellow
    Write-Host "[*] Press Ctrl+Q to stop`n" -ForegroundColor Yellow
} catch {
    Write-Host "[-] Failed to start: $_" -ForegroundColor Red
    exit
}

# Ctrl+C handler
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    if ($listener -and $listener.IsListening) {
        $listener.Stop()
        $listener.Close()
    }
}

function Send-Response {
    param($Response, $Content = "OK", $StatusCode = 200)
    try {
        $Response.StatusCode = $StatusCode
        $Response.ContentType = "text/plain; charset=utf-8"
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($Content)
        $Response.ContentLength64 = $buffer.Length
        $Response.OutputStream.Write($buffer, 0, $buffer.Length)
        $Response.OutputStream.Flush()
        $Response.Close()
        Write-Host "[+] Response sent: $Content" -ForegroundColor Green
    } catch {
        Write-Host "[-] Response error: $_" -ForegroundColor Red
    }
}

while ($listener.IsListening) {
    try {
        $contextTask = $listener.GetContextAsync()
        
        while (-not $contextTask.AsyncWaitHandle.WaitOne(200)) {
            if ([Console]::KeyAvailable) {
                $key = [Console]::ReadKey($true)
                if ($key.Key -eq 'Q' -and $key.Modifiers -eq 'Control') {
                    throw "User interrupted"
                }
            }
        }
        
        $context = $contextTask.GetAwaiter().GetResult()
        $request = $context.Request
        $response = $context.Response
        $path = $request.Url.LocalPath
        
        Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Request: $path" -ForegroundColor Gray
        
        if ($path -eq "/execute") {
            $filename = $request.QueryString["file"]
            $downloadUrl = $request.QueryString["url"]
            
            if ($filename -and $downloadUrl) {
                Write-Host "[+] Deployment received: $filename" -ForegroundColor Cyan
                
                # 즉시 응답
                Send-Response -Response $response -Content "OK"
                
                # 백그라운드에서 다운로드 및 실행
                Start-Job -ScriptBlock {
                    param($url, $file, $path)
                    
                    try {
                        $localPath = Join-Path $path $file
                        
                        # 다운로드
                        Write-Host "[*] Downloading $file..." -ForegroundColor Yellow
                        $startTime = Get-Date
                        
                        Invoke-WebRequest -Uri $url -OutFile $localPath -UseBasicParsing
                        
                        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
                        Write-Host "[+] Downloaded in ${elapsed}s" -ForegroundColor Green
                        
                        # 실행
                        if ($file -match '\.ps1$') {
                            Write-Host "[*] Executing..." -ForegroundColor Yellow
                            
                            $scriptContent = Get-Content $localPath -Raw
                            Invoke-Expression $scriptContent
                            
                            Write-Host "[+] Executed" -ForegroundColor Green
                        }
                    } catch {
                        Write-Host "[-] Job error: $_" -ForegroundColor Red
                    }
                    
                } -ArgumentList $downloadUrl, $filename, $DownloadPath | Out-Null
                
                Write-Host "[*] Background job started" -ForegroundColor Yellow
            } else {
                Send-Response -Response $response -Content "MISSING_PARAMS" -StatusCode 400
            }
            
        } elseif ($path -eq "/health") {
            Send-Response -Response $response -Content "OK"
            
        } else {
            Send-Response -Response $response -Content "NOT_FOUND" -StatusCode 404
        }
        
    } catch {
        if ($_.Exception.Message -eq "User interrupted") {
            break
        }
        Write-Host "[-] Request error: $_" -ForegroundColor Red
    }
}

Write-Host "`n[*] Shutting down..." -ForegroundColor Yellow
$listener.Stop()
$listener.Close()
Write-Host "[+] Agent stopped" -ForegroundColor Green