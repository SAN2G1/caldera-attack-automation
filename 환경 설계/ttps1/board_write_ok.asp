<%@ Language="VBScript" %>
    <html>

    <head>
        <meta charset="utf-8">
        <title>파일 업로드</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f0f0f0;
            }

            .header {
                background: white;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }

            .container {
                background: white;
                padding: 30px;
                border-radius: 5px;
                max-width: 500px;
            }

            .back-link {
                color: #1976d2;
                text-decoration: none;
            }
        </style>
    </head>

    <body>
        <div class="header">
            <a href="index.asp" class="back-link">← 메인으로</a>
        </div>
        <div class="container">
            <h2>파일 업로드</h2>
            <form method="post" action="upload_handler.asp" enctype="multipart/form-data">
                <input type="file" name="file"><br><br>
                <input type="submit" value="업로드">
            </form>
        </div>
    </body>

    </html>