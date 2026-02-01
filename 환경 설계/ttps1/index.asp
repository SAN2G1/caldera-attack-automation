<%@ Language="VBScript" %>
    <% ' 이미 로그인된 경우 메인 페이지로 리다이렉트
If Session("UserID") <> "" Then
    Response.Redirect "main.asp"
End If
%>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>사내 홈페이지 로그인</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .login-container { 
            width: 350px; 
            margin: 100px auto; 
            padding: 30px; 
            background: white; 
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h2 { text-align: center; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #555; }
        input[type="text"], input[type="password"] { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 4px;
            box-sizing: border-box;
        }
        button { 
            width: 100%; 
            padding: 12px; 
            background-color: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background-color: #45a049; }
        .error { color: red; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <!-- 개발자 메모: 테스트 계정 정보
         관리자 ID: admin
         관리자 PW: P@ssw0rd!2020
         운영자 ID: operator
         운영자 PW: Op3r@t0r#2020
    -->
    
    <div class="login-container">
        <h2>사내 시스템 로그인</h2>
        <form method="POST" action="login_process.asp">
            <div class="form-group">
                <label for="userid">사용자 ID:</label>
                <input type="text" id="userid" name="userid" required>
            </div>
            <div class="form-group">
                <label for="password">비밀번호:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">로그인</button>
        </form>
        <%
        If Request.QueryString("error") = "1" Then
            Response.Write "<p class=' error'>아이디 또는 비밀번호가 올바르지 않습니다.</p>"
        End If
        %>
        </div>
        </body>

        </html>