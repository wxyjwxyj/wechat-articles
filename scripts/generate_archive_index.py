"""生成 archive/index.html，列出所有历史日期。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.log import get_logger

logger = get_logger(__name__)

ARCHIVE_DIR = Path(__file__).parent.parent / "archive"


def build_archive_index() -> str:
    # 找所有 YYYY-MM-DD.html 文件，按日期降序
    files = sorted(
        [f for f in ARCHIVE_DIR.glob("????-??-??.html")],
        reverse=True,
    )

    rows = ""
    for f in files:
        date = f.stem  # "2026-04-04"
        # 从 HTML 里提取文章数
        content = f.read_text(encoding="utf-8")
        m = re.search(r"共采集\s*(\d+)\s*篇.*?聚合为\s*(\d+)\s*条", content)
        if m:
            raw, merged = m.group(1), m.group(2)
            stat = f"{raw} 篇 → {merged} 条"
        else:
            stat = ""
        rows += (
            f"<tr>"
            f"<td><a href='{f.name}'>{date}</a></td>"
            f"<td>{stat}</td>"
            f"</tr>\n"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 资讯归档</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
      background: #f0f2f5;
      min-height: 100vh;
    }}
    .container {{
      max-width: 640px;
      margin: 40px auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 24px 32px;
    }}
    .header h1 {{ font-size: 20px; font-weight: 700; margin-bottom: 4px; }}
    .header p {{ font-size: 13px; opacity: 0.8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      background: #f8f9fb;
      padding: 10px 24px;
      text-align: left;
      font-size: 12px;
      color: #888;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 2px solid #eaecf0;
    }}
    td {{
      padding: 14px 24px;
      border-bottom: 1px solid #f0f2f5;
      font-size: 14px;
      color: #555;
    }}
    td:first-child {{ font-weight: 500; }}
    td a {{
      color: #667eea;
      text-decoration: none;
      font-size: 15px;
      font-weight: 600;
    }}
    td a:hover {{ text-decoration: underline; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #fafbff; }}
    .footer {{
      text-align: center;
      padding: 16px;
      font-size: 12px;
      color: #bbb;
      border-top: 1px solid #f0f2f5;
    }}
    .back-link {{
      display: inline-block;
      margin: 16px 24px;
      font-size: 13px;
      color: #667eea;
      text-decoration: none;
    }}
    .back-link:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📚 AI 资讯归档</h1>
      <p>共 {len(files)} 天 · 点击日期查看当天内容</p>
    </div>
    <a href="../index.html" class="back-link">← 返回今日</a>
    <table>
      <thead>
        <tr><th>日期</th><th>文章数</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <div class="footer">由 Claude 自动生成</div>
  </div>
</body>
</html>"""


def main():
    ARCHIVE_DIR.mkdir(exist_ok=True)
    html = build_archive_index()
    out = ARCHIVE_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    logger.info("归档索引已生成 → %s（共 %d 天）", out, len(list(ARCHIVE_DIR.glob('????-??-??.html'))))


if __name__ == "__main__":
    main()
