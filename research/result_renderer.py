"""渲染主题搜索结果为 HTML 页面。"""


def render_results_html(topic: str, results: dict) -> str:
    """渲染搜索结果为 HTML。

    Args:
        topic: 搜索主题
        results: 搜索结果字典（包含 papers, repositories, discussions, docs）

    Returns:
        完整的 HTML 页面字符串
    """
    papers = results.get("papers", [])
    repos = results.get("repositories", [])
    discussions = results.get("discussions", [])
    docs = results.get("docs", [])

    total = len(papers) + len(repos) + len(discussions) + len(docs)

    # 渲染各分类
    papers_html = _render_papers(papers)
    repos_html = _render_repos(repos)
    discussions_html = _render_discussions(discussions)
    docs_html = _render_docs(docs)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - 学习资料</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        h1 {{
            font-size: 2.5em;
            color: #1a202c;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #718096;
            font-size: 1.1em;
        }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .section-title {{
            font-size: 1.5em;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .item {{
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            background: #f7fafc;
            border-radius: 6px;
            transition: transform 0.2s;
        }}
        .item:hover {{
            transform: translateX(5px);
            background: #edf2f7;
        }}
        .item-title {{
            font-size: 1.2em;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 8px;
        }}
        .item-title a {{
            color: #667eea;
            text-decoration: none;
        }}
        .item-title a:hover {{
            text-decoration: underline;
        }}
        .item-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 8px;
            font-size: 0.9em;
            color: #718096;
        }}
        .score {{
            display: inline-block;
            background: #48bb78;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .comment {{
            color: #4a5568;
            font-style: italic;
        }}
        .empty {{
            text-align: center;
            color: #a0aec0;
            padding: 40px;
            font-size: 1.1em;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 10px;
        }}
        .stat {{
            background: #edf2f7;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.95em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 {topic}</h1>
            <p class="subtitle">学习资料汇总</p>
            <div class="stats">
                <span class="stat">📄 论文 {len(papers)}</span>
                <span class="stat">💻 代码 {len(repos)}</span>
                <span class="stat">💬 讨论 {len(discussions)}</span>
                <span class="stat">📖 文档 {len(docs)}</span>
            </div>
        </header>

        {_render_empty_message(total) if total == 0 else ""}

        {docs_html}
        {papers_html}
        {repos_html}
        {discussions_html}
    </div>
</body>
</html>"""

    return html


def _render_papers(papers: list[dict]) -> str:
    """渲染论文列表"""
    if not papers:
        return ""

    items_html = ""
    for paper in papers:
        title = paper.get("title", "")
        url = paper.get("url", "")
        score = paper.get("score", 0)
        comment = paper.get("comment", "")
        authors = paper.get("authors", [])
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{title}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
                {f'<span>作者: {author_str}</span>' if author_str else ''}
            </div>
            <div class="comment">{comment}</div>
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">📄 学术论文 ({len(papers)})</h2>
        {items_html}
    </div>"""


def _render_repos(repos: list[dict]) -> str:
    """渲染仓库列表"""
    if not repos:
        return ""

    items_html = ""
    for repo in repos:
        name = repo.get("full_name", repo.get("name", ""))
        url = repo.get("url", "")
        score = repo.get("score", 0)
        comment = repo.get("comment", "")
        stars = repo.get("stars", 0)
        language = repo.get("language", "")

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{name}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
                <span>⭐ {stars:,}</span>
                {f'<span>{language}</span>' if language else ''}
            </div>
            <div class="comment">{comment}</div>
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">💻 开源项目 ({len(repos)})</h2>
        {items_html}
    </div>"""


def _render_discussions(discussions: list[dict]) -> str:
    """渲染讨论列表"""
    if not discussions:
        return ""

    items_html = ""
    for disc in discussions:
        title = disc.get("title", "")
        url = disc.get("hn_url", disc.get("url", ""))
        score = disc.get("score", 0)
        comment = disc.get("comment", "")
        points = disc.get("score", 0)  # HN 的 score 字段是点赞数
        comments_count = disc.get("comments", 0)

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{title}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
                <span>👍 {points}</span>
                <span>💬 {comments_count}</span>
            </div>
            <div class="comment">{comment}</div>
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">💬 社区讨论 ({len(discussions)})</h2>
        {items_html}
    </div>"""


def _render_docs(docs: list[dict]) -> str:
    """渲染文档列表"""
    if not docs:
        return ""

    items_html = ""
    for doc in docs:
        name = doc.get("name", "")
        url = doc.get("url", "")
        score = doc.get("score", 9)
        comment = doc.get("comment", "官方文档，权威可靠")

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{name}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
            </div>
            <div class="comment">{comment}</div>
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">📖 官方文档 ({len(docs)})</h2>
        {items_html}
    </div>"""


def _render_empty_message(total: int) -> str:
    """渲染空结果提示"""
    if total > 0:
        return ""
    return """
    <div class="section">
        <div class="empty">
            😔 未找到相关学习资料<br>
            请尝试其他关键词
        </div>
    </div>"""
