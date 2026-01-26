# Setup-IIS-Management.ps1
# Run as Administrator

Write-Host "=== Setting up IIS Management Console ===" -ForegroundColor Cyan

$webRoot = "C:\inetpub\wwwroot"
$uploadDir = "$webRoot\uploads"
$deployDir = "$webRoot\deploy"

# Stop IIS
Write-Host "`n[1] Stopping IIS..."
iisreset /stop | Out-Null
Start-Sleep -Seconds 2

# Clean up
Write-Host "`n[2] Cleaning up..."
Get-ChildItem -Path $webRoot -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

# Create directories
Write-Host "`n[3] Creating directories..."
@($uploadDir, $deployDir) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

# Set permissions
Write-Host "`n[4] Setting permissions..."
icacls $uploadDir /grant "Everyone:(OI)(CI)F" /T | Out-Null
icacls $deployDir /grant "Everyone:(OI)(CI)F" /T | Out-Null

# Main page
Write-Host "`n[5] Creating files..."
$indexHtml = @'
<!DOCTYPE html>
<html>
<head><title>Management Console</title></head>
<body>
<h1>Central Management Console</h1>
<h2>Upload Files</h2>
<form action="upload.asp" method="post" enctype="multipart/form-data">
<input type="file" name="file" required />
<input type="submit" value="Upload" />
</form>
<h2>Uploaded Files</h2>
<ul id="uploadedFiles"><li>Loading...</li></ul>
<h2>Deploy to Clients</h2>
<form action="deploy.asp" method="post">
<select name="filename" id="deploySelect"><option value="">Select file...</option></select>
<input type="submit" value="Deploy" />
</form>
<h2>Deployed Files</h2>
<ul id="deployedFiles"><li>Loading...</li></ul>
<script>
function loadFiles() {
fetch('list.asp?dir=uploads').then(r => r.text()).then(data => {
document.getElementById('uploadedFiles').innerHTML = data || '<li>No files</li>';
let options = '<option value="">Select file...</option>';
let parser = new DOMParser();
let doc = parser.parseFromString(data, 'text/html');
let items = doc.querySelectorAll('li');
items.forEach(item => {
let text = item.textContent.trim();
if (text && text !== 'No files') {
let filename = text.split(' - ')[0];
options += `<option value="${filename}">${text}</option>`;
}
});
document.getElementById('deploySelect').innerHTML = options;
});
fetch('list.asp?dir=deploy').then(r => r.text()).then(data => {
document.getElementById('deployedFiles').innerHTML = data || '<li>No files</li>';
});
}
loadFiles();
setInterval(loadFiles, 5000);
</script>
</body>
</html>
'@

Set-Content -Path "$webRoot\index.html" -Value $indexHtml -Force

# Upload handler - SIMPLE BINARY
$uploadAsp = @'
<%
Dim byteCount, binData, strData, pos, fileName, dataStart, dataEnd

byteCount = Request.TotalBytes
If byteCount > 0 Then
    binData = Request.BinaryRead(byteCount)
    
    strData = ""
    For i = 1 To LenB(binData)
        strData = strData & Chr(AscB(MidB(binData, i, 1)))
    Next
    
    pos = InStr(strData, "filename=""")
    If pos > 0 Then
        pos = pos + 10
        Dim endPos
        endPos = InStr(pos, strData, """")
        fileName = Mid(strData, pos, endPos - pos)
        
        If InStr(fileName, "\") > 0 Then
            fileName = Mid(fileName, InStrRev(fileName, "\") + 1)
        End If
        
        dataStart = InStr(endPos, strData, vbCrLf & vbCrLf) + 4
        dataEnd = InStrRev(strData, vbCrLf & "--") - 1
        
        If dataEnd > dataStart And fileName <> "" Then
            Dim content, savePath, fso, ts
            content = Mid(strData, dataStart, dataEnd - dataStart + 1)
            savePath = Server.MapPath("uploads\" & fileName)
            
            Set fso = Server.CreateObject("Scripting.FileSystemObject")
            Set ts = fso.CreateTextFile(savePath, True)
            ts.Write content
            ts.Close
            
            Response.Write "<html><body><h2>Upload Success</h2><p>File: " & fileName & "</p><p><a href='/'>Back</a></p></body></html>"
        End If
    End If
End If
%>
'@

Set-Content -Path "$webRoot\upload.asp" -Value $uploadAsp -Force

# List
$listAsp = @'
<%
Dim dirName, fso, folder, files, file
dirName = Request.QueryString("dir")
If dirName = "" Then dirName = "uploads"
Set fso = Server.CreateObject("Scripting.FileSystemObject")
Set folder = fso.GetFolder(Server.MapPath(dirName))
Set files = folder.Files
If files.Count = 0 Then
Response.Write("<li>No files</li>")
Else
For Each file In files
Response.Write("<li>" & file.Name & " - " & Round(file.Size/1024, 2) & " KB</li>")
Next
End If
%>
'@

Set-Content -Path "$webRoot\list.asp" -Value $listAsp -Force

# Deploy
$deployAsp = @'
<%
Dim fileName, sourcePath, destPath, fso, serverIP, clientURL
fileName = Request.Form("filename")
serverIP = "192.168.56.210"
If fileName <> "" Then
Set fso = Server.CreateObject("Scripting.FileSystemObject")
sourcePath = Server.MapPath("uploads\" & fileName)
destPath = Server.MapPath("deploy\" & fileName)
If fso.FileExists(sourcePath) Then
fso.CopyFile sourcePath, destPath, True
Response.Write("<html><body><h2>Deployment Started</h2><p>File: " & fileName & "</p><pre>")
clientURL = "http://192.168.56.211:8081/execute?file=" & fileName & "&url=http://" & serverIP & ":80/deploy/" & fileName
On Error Resume Next
Dim http
Set http = Server.CreateObject("MSXML2.ServerXMLHTTP")
http.open "GET", clientURL, False
http.send
If Err.Number = 0 Then
Response.Write("Client 192.168.56.211: " & http.responseText & vbCrLf)
Else
Response.Write("Client 192.168.56.211: ERROR - " & Err.Description & vbCrLf)
End If
On Error Goto 0
Response.Write("</pre><p><a href='/'>Back</a></p></body></html>")
End If
End If
%>
'@

Set-Content -Path "$webRoot\deploy.asp" -Value $deployAsp -Force

# API
$apiAsp = @'
<%
Dim action, username, password, fso, userFile, users
action = Request.QueryString("action")
username = Request.QueryString("user")
password = Request.QueryString("pass")
userFile = Server.MapPath("users.txt")
Set fso = Server.CreateObject("Scripting.FileSystemObject")
If action = "createuser" And username <> "" And password <> "" Then
Dim ts
Set ts = fso.OpenTextFile(userFile, 8, True)
ts.WriteLine(username & ":" & password)
ts.Close
Response.Write("User created: " & username)
ElseIf action = "login" And username <> "" And password <> "" Then
If fso.FileExists(userFile) Then
Set ts = fso.OpenTextFile(userFile, 1)
users = ts.ReadAll()
ts.Close
If InStr(users, username & ":" & password) > 0 Then
Response.Write("Login success")
Else
Response.Write("Login failed")
End If
Else
Response.Write("No users")
End If
End If
%>
'@

Set-Content -Path "$webRoot\api.asp" -Value $apiAsp -Force

# Enable errors
Write-Host "`n[6] Configuring..."
& $env:windir\system32\inetsrv\appcmd.exe set config -section:system.webServer/asp /scriptErrorSentToBrowser:true | Out-Null
& $env:windir\system32\inetsrv\appcmd.exe set config -section:system.webServer/httpErrors /errorMode:"Detailed" | Out-Null

# Start
Write-Host "`n[7] Starting IIS..."
iisreset /start | Out-Null

Write-Host "`n=== Complete ===" -ForegroundColor Green
Start-Process "http://localhost/"