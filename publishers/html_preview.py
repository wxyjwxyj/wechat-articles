"""根据 bundle 数据生成 HTML 预览页。"""
from datetime import datetime


def render_bundle_html(bundle: dict) -> str:
    """
    将 bundle 数据渲染为 HTML 字符串。
    bundle 结构：
      - bundle_date: str（YYYY-MM-DD）
      - title: str
      - intro: str
      - topics: list[dict]，每个 dict 含 name、count
      - sources: dict[str, list[dict]]，来源名 → 文章列表
    """
    total_articles = sum(len(items) for items in bundle.get("sources", {}).values())
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 话题标签 HTML
    topics_html = ""
    for topic in bundle.get("topics", []):
        topics_html += f"<span class='topic-tag'>{topic['name']} ({topic['count']})</span>\n"

    # 来源分组内容 HTML
    sources_html = ""
    for source_name, articles in bundle.get("sources", {}).items():
        sources_html += f"<h2 class='source-name'>{source_name}</h2>\n<ul class='article-list'>\n"
        for article in articles:
            sources_html += (
                f"<li class='article-item'>"
                f"<a href='{article['url']}' target='_blank'>{article['title']}</a>"
                f"<p class='summary'>{article.get('summary', '')}</p>"
                f"</li>\n"
            )
        sources_html += "</ul>\n"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{bundle['title']}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
    h1 {{ font-size: 1.5em; margin-bottom: 8px; }}
    .meta {{ color: #888; font-size: 0.9em; margin-bottom: 16px; }}
    .intro {{ background: #f5f5f5; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; }}
    .topics {{ margin-bottom: 20px; }}
    .topic-tag {{ display: inline-block; background: #e8f4f8; color: #2196F3; padding: 4px 10px; border-radius: 12px; margin: 4px; font-size: 0.85em; }}
    h2.source-name {{ color: #555; border-left: 4px solid #2196F3; padding-left: 10px; margin-top: 24px; }}
    .article-list {{ list-style: none; padding: 0; }}
    .article-item {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
    .article-item a {{ text-decoration: none; color: #1a1a1a; font-weight: 500; }}
    .article-item a:hover {{ color: #2196F3; }}
    .summary {{ color: #666; font-size: 0.9em; margin: 4px 0 0; }}
  </style>
</head>
<body>
  <h1>{bundle['title']}</h1>
  <p class="meta">生成时间：{generated_at} | 共 {total_articles} 篇文章</p>
  <div class="intro">{bundle['intro']}</div>
  <div class="topics">
{topics_html}  </div>
{sources_html}
</body>
</html>"""
    return html
