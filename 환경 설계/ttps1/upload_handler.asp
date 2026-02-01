<%@ Language=VBScript %>
<%
Option Explicit
'On Error Resume Next ' 에러 확인을 위해 주석 처리 유지

' 1. 업로드 디렉토리 설정
Dim savePath
savePath = Server.MapPath("uploads")

Dim fs
Set fs = Server.CreateObject("Scripting.FileSystemObject")
If Not fs.FolderExists(savePath) Then
    fs.CreateFolder(savePath)
End If
Set fs = Nothing

' 2. 전체 요청을 바이너리로 읽은 후 텍스트로 변환
Dim binData, stream, body
binData = Request.BinaryRead(Request.TotalBytes)

Set stream = Server.CreateObject("ADODB.Stream")
stream.Type = 1 ' binary
stream.Open
stream.Write binData
stream.Position = 0
stream.Type = 2 ' text
stream.Charset = "iso-8859-1"
body = stream.ReadText
stream.Close
Set stream = Nothing

' 3. boundary 및 데이터 파싱
Dim boundary, parts, i
boundary = "--" & Split(Request.ServerVariables("CONTENT_TYPE"), "boundary=")(1)
parts = Split(body, boundary)

For i = 0 To UBound(parts)
    If InStr(parts(i), "filename=") > 0 Then
        
        ' 4. 안정적인 파일명 추출 (개선된 부분)
        Dim filename, temp, startPos, endPos
        temp = parts(i)
        startPos = InStr(temp, "filename=") + 10 ' filename=" 다음 위치
        endPos = InStr(startPos, temp, """")     ' 닫는 따옴표 위치
        
        If endPos > startPos Then
            filename = Mid(temp, startPos, endPos - startPos)
        Else
            filename = "" ' 파싱 실패
        End If
        
        If filename <> "" Then
            ' 5. 파일 내용 추출 및 저장 (기존에 잘 되던 방식)
            Dim dataStart, fileContent
            dataStart = InStr(parts(i), vbCrLf & vbCrLf) + 4
            fileContent = Mid(parts(i), dataStart)
            
            ' 마지막 경계선 바로 앞의 줄바꿈 문자(\r\n) 제거
            If Len(fileContent) > 1 Then
                fileContent = Left(fileContent, Len(fileContent) - 2)
            End If

            ' 파일 저장
            Set stream = Server.CreateObject("ADODB.Stream")
            stream.Type = 2 ' text
            stream.Charset = "iso-8859-1"
            stream.Open
            stream.WriteText fileContent
            stream.Position = 0
            stream.Type = 1 ' binary로 변환 후 저장
            stream.SaveToFile savePath & "\" & filename, 2 ' 덮어쓰기
            stream.Close
            Set stream = Nothing

            Response.Write "업로드 완료: " & filename
            Response.End
        End If
    End If
Next

Response.Write "업로드 실패"
%>
