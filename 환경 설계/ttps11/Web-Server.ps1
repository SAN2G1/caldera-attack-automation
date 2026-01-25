# Web-Server.ps1
# Central Management Server with Vulnerabilities

param(
    [int]$Port = 8080,
    [string]$IP = "192.168.56.210"
)

$uploadPath = "$PSScriptRoot\uploads"
$deployPath = "$PSScriptRoot\deploy"
$htmlPath = "$PSScriptRoot\index.html"

@($uploadPath, $deployPath) | ForEach-Object {
    if (!(Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

$script:users = @{ "admin" = "Admin123!" }
$script:clients = @("192.168.56.211:8081")

$listener = New-Object System.Net.HttpListener

try {
    $listener.Prefixes.Add("http://+:$Port/")
    $listener.Start()
    
    Write-Host "`n[+] Server: http://${IP}:${Port}" -ForegroundColor Green
    Write-Host "[*] Clients: $($script:clients.Count)" -ForegroundColor Cyan
    Write-Host "[*] Press Ctrl+Q to stop`n" -ForegroundColor Yellow
} catch {
    Write-Host "[-] Failed: $_" -ForegroundColor Red
    Write-Host "[!] Run as Administrator" -ForegroundColor Yellow
    exit
}

# Ctrl+Q handler
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    if ($listener -and $listener.IsListening) {
        $listener.Stop()
        $listener.Close()
    }
}

function Send-Response {
    param($Response, $Content, $ContentType = "text/html", $StatusCode = 200)
    try {
        $Response.StatusCode = $StatusCode
        $Response.ContentType = "$ContentType; charset=utf-8"
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($Content)
        $Response.ContentLength64 = $buffer.Length
        $Response.OutputStream.Write($buffer, 0, $buffer.Length)
        $Response.OutputStream.Flush()
        $Response.Close()
    } catch {}
}

function Parse-MultipartFormData {
    param($InputStream, $ContentType)
    
    $boundary = "--" + $ContentType.Split('=')[1]
    $reader = New-Object System.IO.StreamReader($InputStream)
    $content = $reader.ReadToEnd()
    $parts = $content -split $boundary
    
    foreach ($part in $parts) {
        if ($part -match 'filename="([^"]+)"') {
            $filename = $matches[1]
            $headerEnd = $part.IndexOf("`r`n`r`n")
            if ($headerEnd -gt 0) {
                $fileContent = $part.Substring($headerEnd + 4).TrimEnd("-", "`r", "`n")
                return @{ FileName = $filename; Content = $fileContent }
            }
        }
    }
    return $null
}

while ($listener.IsListening) {
    try {
        # Non-blocking receive with Ctrl+Q support
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
        $method = $request.HttpMethod
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $method $path" -ForegroundColor Gray
        
        switch -Wildcard ($path) {
            "/" {
                # Main dashboard
                if (Test-Path $htmlPath) {
                    $html = Get-Content $htmlPath -Raw
                    
                    $uploadedFiles = ""
                    Get-ChildItem $uploadPath -ErrorAction SilentlyContinue | ForEach-Object {
                        $uploadedFiles += "<li>$($_.Name) - $([math]::Round($_.Length/1KB, 2)) KB</li>"
                    }
                    if (!$uploadedFiles) { $uploadedFiles = "<li>No files</li>" }
                    
                    $deployedFiles = ""
                    Get-ChildItem $deployPath -ErrorAction SilentlyContinue | ForEach-Object {
                        $deployedFiles += "<li>$($_.Name) - $([math]::Round($_.Length/1KB, 2)) KB</li>"
                    }
                    if (!$deployedFiles) { $deployedFiles = "<li>No files</li>" }
                    
                    $fileOptions = ""
                    Get-ChildItem $uploadPath -ErrorAction SilentlyContinue | ForEach-Object {
                        $fileOptions += "<option value='$($_.Name)'>$($_.Name)</option>"
                    }
                    
                    $html = $html -replace "{{UPLOADED_FILES}}", $uploadedFiles
                    $html = $html -replace "{{DEPLOYED_FILES}}", $deployedFiles
                    $html = $html -replace "{{FILE_OPTIONS}}", $fileOptions
                    
                    Send-Response -Response $response -Content $html
                }
            }
            
            "/uploads" {
                # POST: multipart/form-data (웹 UI 전용)
                if ($method -eq "POST" -and $request.ContentType -and $request.ContentType.Contains("multipart")) {
                    $fileData = Parse-MultipartFormData -InputStream $request.InputStream -ContentType $request.ContentType
                    
                    if ($fileData) {
                        $filePath = Join-Path $uploadPath $fileData.FileName
                        [System.IO.File]::WriteAllText($filePath, $fileData.Content, [System.Text.Encoding]::UTF8)
                        
                        Write-Host "[+] Uploaded: $($fileData.FileName)" -ForegroundColor Green
                        
                        Send-Response -Response $response -Content "<html><body><h2>OK</h2><a href='/'>Back</a></body></html>"
                    }
                }
            }

            "/uploads/*" {
                $filename = $path.Replace("/uploads/", "")
                $filePath = Join-Path $uploadPath $filename
                
                # POST: 파일 업로드
                if ($method -eq "POST") {
                    try {
                        # 텍스트 파일 (.ps1, .bat, .txt, .aspx)
                        if ($filename -match '\.(ps1|bat|txt|aspx)$') {
                            $reader = New-Object System.IO.StreamReader($request.InputStream, [System.Text.Encoding]::UTF8)
                            $content = $reader.ReadToEnd()
                            [System.IO.File]::WriteAllText($filePath, $content, [System.Text.Encoding]::ASCII)
                            
                            Write-Host "[+] Uploaded: $filename" -ForegroundColor Green
                        }
                        # 바이너리 파일 (.exe, .dll, etc)
                        else {
                            $bytes = New-Object byte[] $request.ContentLength64
                            $request.InputStream.Read($bytes, 0, $request.ContentLength64) | Out-Null
                            [System.IO.File]::WriteAllBytes($filePath, $bytes)
                            
                            Write-Host "[+] Uploaded: $filename ($($bytes.Length) bytes)" -ForegroundColor Green
                        }
                        
                        Send-Response -Response $response -Content "OK" -ContentType "text/plain"
                    } catch {
                        Write-Host "[-] Upload error: $_" -ForegroundColor Red
                        Send-Response -Response $response -Content "ERROR" -ContentType "text/plain" -StatusCode 500
                    }
                }
                # GET: 파일 다운로드 또는 웹셸 실행
                elseif ($method -eq "GET") {
                    if (Test-Path $filePath) {
                        # 웹셸 실행 (.aspx?cmd=)
                        if ($filename -match '\.(aspx|asp)$' -and $request.QueryString["cmd"]) {
                            $cmd = $request.QueryString["cmd"]
                            Write-Host "[!] Webshell: $cmd" -ForegroundColor Red
                            
                            $output = powershell -Command $cmd 2>&1 | Out-String
                            Send-Response -Response $response -Content $output -ContentType "text/plain"
                        }
                        # 파일 다운로드
                        else {
                            $content = Get-Content $filePath -Raw
                            Send-Response -Response $response -Content $content
                        }
                    } else {
                        Send-Response -Response $response -Content "Not Found" -StatusCode 404
                    }
                }
            }

            "/api/health" {
                Send-Response -Response $response -Content "OK" -ContentType "text/plain"
            }
            
            "/api/createuser" {
                # VULN 2: No authentication
                if ($method -eq "GET") {
                    $username = $request.QueryString["user"]
                    $password = $request.QueryString["pass"]
                    
                    if ($username -and $password) {
                        $script:users[$username] = $password
                        Write-Host "[!] User created (NO AUTH): $username" -ForegroundColor Yellow
                        Send-Response -Response $response -Content "OK" -ContentType "text/plain"
                    } else {
                        Send-Response -Response $response -Content "ERROR" -ContentType "text/plain" -StatusCode 400
                    }
                }
            }
            
            "/api/login" {
                if ($method -eq "GET") {
                    $username = $request.QueryString["user"]
                    $password = $request.QueryString["pass"]
                    
                    if ($script:users[$username] -eq $password) {
                        Write-Host "[+] Login: $username" -ForegroundColor Green
                        Send-Response -Response $response -Content "OK" -ContentType "text/plain"
                    } else {
                        Send-Response -Response $response -Content "FAIL" -ContentType "text/plain" -StatusCode 401
                    }
                }
            }
            
            "/api/list" {
                $files = Get-ChildItem $deployPath -ErrorAction SilentlyContinue
                $list = ($files | ForEach-Object { $_.Name }) -join "`n"
                Send-Response -Response $response -Content $list -ContentType "text/plain"
            }
            
            "/api/download/*" {
                $filename = $path.Replace("/api/download/", "")
                $filePath = Join-Path $deployPath $filename
                
                if (Test-Path $filePath) {
                    try {
                        $content = Get-Content $filePath -Raw -Encoding UTF8
                        
                        Send-Response -Response $response -Content $content -ContentType "text/plain"
                        
                        Write-Host "[+] Downloaded: $filename" -ForegroundColor Cyan
                    } catch {
                        Write-Host "[-] Download error: $_" -ForegroundColor Red
                        Send-Response -Response $response -Content "ERROR" -ContentType "text/plain" -StatusCode 500
                    }
                } else {
                    Send-Response -Response $response -Content "NOT_FOUND" -ContentType "text/plain" -StatusCode 404
                }
            }
            
            "/api/deploy/*" {
                if ($method -eq "GET") {
                    $filename = $path.Replace("/api/deploy/", "")
                    
                    if ($filename) {
                        $sourcePath = Join-Path $uploadPath $filename
                        $destPath = Join-Path $deployPath $filename
                        
                        if (Test-Path $sourcePath) {
                            Copy-Item $sourcePath $destPath -Force
                            Write-Host "[+] Deploying: $filename" -ForegroundColor Green
                            
                            $results = @()
                            
                            foreach ($client in $script:clients) {
                                try {
                                    $url = "http://${client}/execute?file=${filename}&url=http://${IP}:${Port}/api/download/${filename}"
                                    
                                    $result = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
                                    
                                    if ($result.Content -eq "OK") {
                                        Write-Host "  -> ${client}: OK" -ForegroundColor Green
                                        $results += "  -> ${client}: OK"
                                    } else {
                                        Write-Host "  -> ${client}: ERROR" -ForegroundColor Red
                                        $results += "  -> ${client}: ERROR"
                                    }
                                } catch {
                                    Write-Host "  -> ${client}: FAIL - $($_.Exception.Message)" -ForegroundColor Red
                                    $results += "  -> ${client}: FAIL"
                                }
                            }
                            
                            Start-Sleep -Seconds 2
                            
                            $resultFiles = Get-ChildItem $uploadPath -Filter "result_*" -ErrorAction SilentlyContinue |
                                Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-1) }
                            
                            $responseText = "Deployment: $filename`n"
                            $responseText += ($results -join "`n") + "`n"
                            
                            if ($resultFiles) {
                                foreach ($file in $resultFiles) {
                                    $responseText += "[+] Uploaded: $($file.Name)`n"
                                }
                            }
                            
                            Send-Response -Response $response -Content $responseText -ContentType "text/plain"
                        } else {
                            Send-Response -Response $response -Content "FILE_NOT_FOUND" -ContentType "text/plain" -StatusCode 404
                        }
                    } else {
                        Send-Response -Response $response -Content "MISSING_FILENAME" -ContentType "text/plain" -StatusCode 400
                    }
                }
            }
            
            default {
                Send-Response -Response $response -Content "Not Found" -StatusCode 404
            }
        }
    } catch {
        if ($_.Exception.Message -eq "User interrupted") {
            break
        }
        Write-Host "[-] Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n[*] Shutting down..." -ForegroundColor Yellow
$listener.Stop()
$listener.Close()
Write-Host "[+] Server stopped" -ForegroundColor Green