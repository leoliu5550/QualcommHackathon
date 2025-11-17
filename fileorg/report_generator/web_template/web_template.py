def build_web_html_template(json_str: str):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>檔案分類結果</title>
        <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 95%;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 25px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #6c757d;
            margin-top: 5px;
        }}

        .category-section {{
            padding: 30px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-evenly;
        }}

        .category-group {{
            margin-bottom: 30px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 30%;
        }}

        .category-group:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .category-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 25px;
            font-size: 1.4em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .file-count {{
            background: rgba(255, 255, 255, 0.25);
            padding: 6px 18px;
            border-radius: 20px;
            font-size: 0.8em;
        }}

        .file-list {{
            padding: 20px 25px;
            background: #fafbfc;
        }}

        .file-item {{
            padding: 12px 0;
            color: #2c3e50;
            font-size: 1.05em;
            border-bottom: 1px solid #e9ecef;
            transition: color 0.2s;
            cursor: pointer;
            position: relative;
        }}

        .file-item:last-child {{
            border-bottom: none;
        }}

        .file-item:hover {{
            color: #667eea;
            background: #f0f0f0;
            padding-left: 10px;
            margin-left: -10px;
            border-radius: 6px;
        }}

        .file-item::before {{
            content: "📄 ";
            margin-right: 8px;
        }}

        .copied-toast {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }}

        @keyframes slideIn {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8em;
            }}

            .stats {{
                flex-direction: column;
                gap: 20px;
            }}

            .category-section {{
                padding: 15px;
            }}
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📁 檔案分類結果</h1>
            </header>

            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number" id="totalFiles">0</div>
                    <div class="stat-label">總檔案數</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="totalCategories">0</div>
                    <div class="stat-label">分類數量</div>
                </div>
            </div>

            <div class="category-section" id="categorySection"></div>
        </div>

        <script>
        const jsonData = {json_str};

        function extractCategory(path) {{
            return path.split('/')[0];
        }}

        function extractFilename(path) {{
            return path.split('/').slice(1).join('/');
        }}

        function showCopiedToast(path) {{
            // 移除已存在的提示
            const existingToast = document.querySelector('.copied-toast');
            if (existingToast) {{
                existingToast.remove();
            }}

            // 創建新提示
            const toast = document.createElement('div');
            toast.className = 'copied-toast';
            toast.textContent = '✓ 已複製路徑';
            document.body.appendChild(toast);

            // 3秒後移除
            setTimeout(() => {{
                toast.remove();
            }}, 3000);
        }}

        function renderClassification() {{
            const categories = {{}};

            jsonData.file_paths.forEach(file => {{
                const category = extractCategory(file.new);
                const filename = extractFilename(file.new);

                if (!categories[category]) {{
                    categories[category] = [];
                }}

                categories[category].push({{
                    filename: filename,
                    fullPath: file.new
                }});
            }});

            document.getElementById('totalFiles').textContent = jsonData.file_paths.length;
            document.getElementById('totalCategories').textContent = Object.keys(categories).length;

            const categorySection = document.getElementById('categorySection');
            categorySection.innerHTML = '';

            Object.keys(categories).sort().forEach(category => {{
                const files = categories[category];
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'category-group';

                const header = document.createElement('div');
                header.className = 'category-header';
                header.innerHTML = `
                    <span>${{category}}</span>
                    <span class="file-count">${{files.length}}</span>
                `;

                const fileList = document.createElement('div');
                fileList.className = 'file-list';

                files.forEach(file => {{
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.textContent = file.filename;
                    fileItem.title = '點擊複製完整路徑: ' + file.fullPath;

                    // 添加點擊複製功能
                    fileItem.addEventListener('click', async () => {{
                        try {{
                            await navigator.clipboard.writeText(file.fullPath);
                            showCopiedToast(file.fullPath);
                        }} catch (err) {{
                            console.error('複製失敗:', err);
                            alert('複製失敗,請手動複製: ' + file.fullPath);
                        }}
                    }});

                    fileList.appendChild(fileItem);
                }});

                categoryDiv.appendChild(header);
                categoryDiv.appendChild(fileList);
                categorySection.appendChild(categoryDiv);
            }});
        }}

        renderClassification();
    </script>
    </body>
</html>"""


# 使用範例:
# import json
#
# # 你的 JSON 資料
# data = {
#     "file_paths": [
#         {"new": "文件/報告.pdf"},
#         {"new": "圖片/photo.jpg"}
#     ]
# }
#
# # 將資料轉成 JSON 字串
# json_str = json.dumps(data, ensure_ascii=False)
#
# # 使用 lambda 函數傳入參數
# html_content = html_template(json_str)
#
# # 寫入檔案
# with open("output.html", "w", encoding="utf-8") as f:
#     f.write(html_content)
