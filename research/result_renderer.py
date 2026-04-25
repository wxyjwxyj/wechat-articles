"""渲染主题搜索结果为 HTML 页面。"""
import html as _html
import json as _json


def render_results_html(topic: str, results: dict, session_id: int | None = None) -> str:
    """渲染搜索结果为 HTML。

    Args:
        topic: 搜索主题
        results: 搜索结果字典（包含 papers, repositories, discussions, docs, articles）

    Returns:
        完整的 HTML 页面字符串
    """
    topic_escaped = _html.escape(topic)
    papers = results.get("papers", [])
    repos = results.get("repositories", [])
    discussions = results.get("discussions", [])
    docs = results.get("docs", [])
    articles = results.get("articles", [])
    wechat = results.get("wechat", [])
    xhs = results.get("xhs", [])

    total = len(papers) + len(repos) + len(discussions) + len(docs) + len(articles) + len(wechat) + len(xhs)

    # 渲染各分类
    papers_html = _render_papers(papers)
    repos_html = _render_repos(repos)
    discussions_html = _render_discussions(discussions)
    docs_html = _render_docs(docs)
    articles_html = _render_articles(articles)
    wechat_html = _render_wechat(wechat)
    xhs_html = _render_xhs(xhs)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic_escaped} - 学习资料</title>
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
        .deep-research-btn {{
            display: inline-block;
            margin-top: 16px;
            padding: 10px 24px;
            background: linear-gradient(135deg, #f093fb 0%, #f5a623 100%);
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .deep-research-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(240, 147, 251, 0.4);
        }}
        .deep-research-btn:disabled {{
            opacity: 0.6; cursor: not-allowed; transform: none;
        }}
        .dr-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: none;
        }}
        .dr-section.show {{ display: block; }}
        .dr-title {{
            font-size: 1.5em;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .dr-content {{
            font-size: 0.95em;
            line-height: 1.8;
            color: #2d3748;
            white-space: normal;
            word-break: break-word;
        }}
        .dr-content h1, .dr-content h2, .dr-content h3 {{
            margin: 1.2em 0 0.5em;
            color: #1a202c;
        }}
        .dr-content h1 {{ font-size: 1.4em; }}
        .dr-content h2 {{ font-size: 1.2em; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
        .dr-content h3 {{ font-size: 1.05em; }}
        .dr-content p {{ margin-bottom: 0.8em; }}
        .dr-content strong {{ color: #1a202c; }}
        .dr-content ul, .dr-content ol {{ padding-left: 1.5em; margin-bottom: 0.8em; }}
        .dr-content li {{ margin-bottom: 0.3em; }}
        .dr-cursor {{
            display: inline-block;
            width: 2px; height: 1em;
            background: #667eea;
            animation: blink 0.8s step-end infinite;
            vertical-align: text-bottom;
            margin-left: 2px;
        }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
        .dr-status {{
            font-size: 0.85em;
            color: #718096;
            margin-top: 12px;
        }}
        .btn-copy-prompt {{
            padding: 8px 16px;
            font-size: 0.85em;
            font-weight: 600;
            color: #764ba2;
            background: #f3e8ff;
            border: 2px solid #d8b4fe;
            border-radius: 20px;
            cursor: pointer;
            transition: background 0.2s;
            white-space: nowrap;
        }}
        .btn-copy-prompt:hover {{ background: #e9d5ff; }}
        .copy-prompt-tip {{
            font-size: 0.82em;
            color: #48bb78;
            margin-top: 8px;
            min-height: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 {topic_escaped}</h1>
            <p class="subtitle">学习资料汇总
              {'&nbsp;·&nbsp;<a href="/research/history/' + str(session_id) + '" style="color:#667eea;font-size:0.9em">永久链接 #' + str(session_id) + '</a>' if session_id else ''}
              &nbsp;·&nbsp;<a href="/research/history" style="color:#718096;font-size:0.9em">搜索历史</a>
              &nbsp;·&nbsp;<a href="/research" style="color:#718096;font-size:0.9em">新搜索</a>
            </p>
            <div class="stats">
                <span class="stat">📄 论文 {len(papers)}</span>
                <span class="stat">💻 代码 {len(repos)}</span>
                <span class="stat">💬 讨论 {len(discussions)}</span>
                <span class="stat">📖 文档 {len(docs)}</span>
                <span class="stat">🌐 文章 {len(articles)}</span>
                <span class="stat">📱 公众号 {len(wechat)}</span>
                <span class="stat">🍠 小红书 {len(xhs)}</span>
            </div>
            <div>
                <button class="deep-research-btn" id="drBtn" onclick="startDeepResearch()">🔬 深度研究</button>
            </div>
        </header>

        <!-- 深度研究结果区 -->
        <div class="dr-section" id="drSection">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:10px;border-bottom:2px solid #e2e8f0;">
                <h2 class="dr-title" style="margin:0;border:none;padding:0;">🔬 横纵深度研究报告</h2>
                <button class="btn-copy-prompt" id="copyPromptBtn" onclick="copyPrompt()" title="复制提示词，粘贴到任意 AI 使用">📋 复制提示词</button>
            </div>
            <div class="dr-content" id="drContent"></div>
            <div class="dr-status" id="drStatus"></div>
            <div class="copy-prompt-tip" id="copyPromptTip"></div>
        </div>

        {_render_empty_message(total) if total == 0 else ""}

        {docs_html}
        {papers_html}
        {repos_html}
        {discussions_html}
        {articles_html}
        {wechat_html}
        {xhs_html}
    </div>

        <script>
        function copyPrompt() {{
            const topic = {_json.dumps(topic).replace("</", "<\\/")};
            const prompt = `请用横纵分析法，对「${{topic}}」撰写一份完整的深度研究报告。

报告分两个维度：

【纵轴：历时分析】
从起源到今天，完整追溯「${{topic}}」的发展历程：
1. 起源：背景、创始团队、初始技术/概念、当时的行业环境
2. 诞生节点：首次发布/成立时间与初始定位
3. 演进：按时间顺序列出所有关键里程碑——重大版本更新、融资轮次、团队变化、战略转型、架构调整、用户增长节点、合作关系、争议事件
4. 决策逻辑：每个关键节点，解释"为什么"——当时有哪些约束，为何选A而非B
5. 叙事风格：写成有因果逻辑的故事，而非干燥的时间线

【横轴：共时分析】
在当下时间截面，将「${{topic}}」与竞品/同类进行系统对比：
- 先判断竞争格局：无竞品（场景A）/ 少量竞品（场景B）/ 众多竞品（场景C）
- 对比维度：技术路线、产品形态、目标用户、核心优劣势、定价策略
- 用户视角：真实用户反馈，实际使用体验 vs 官方定位
- 生态位：在整个行业版图中占据什么位置
- 趋势：竞争走向、机会与风险

写作风格要求：
- 像一篇优质长文，而非咨询报告
- 叙事驱动，纵轴部分要有故事弧线，不要堆砌列表
- 欢迎有观点，但必须有事实支撑；推测内容需明确标注
- 语言平实，避免空洞的行业黑话
- 对竞品的描述要有温度，说清楚它们"成了什么"，而不只是功能对比

篇幅要求：
- 纵轴：3000-8000字
- 横轴：1500-5000字
- 最终综合：800-1500字

输出格式：
1. 先写纵轴，再写横轴
2. 最后以"横纵交汇"为标题，给出你对「${{topic}}」当前处境与未来走向的判断
3. 全文用中文撰写
4. 尽量标注信息来源和时间；推测内容明确标注`;
            navigator.clipboard.writeText(prompt).then(() => {{
                const tip = document.getElementById('copyPromptTip');
                tip.textContent = '✅ 已复制！粘贴到任意 AI 即可使用';
                setTimeout(() => {{ tip.textContent = ''; }}, 3000);
            }});
        }}

        function startDeepResearch() {{
            const topic = {_json.dumps(topic).replace("</", "<\\/")};
            const btn = document.getElementById('drBtn');
            const section = document.getElementById('drSection');
            const content = document.getElementById('drContent');
            const status = document.getElementById('drStatus');

            btn.disabled = true;
            btn.textContent = '⏳ 研究中...';
            section.classList.add('show');
            content.innerHTML = '<span class="dr-cursor"></span>';
            status.textContent = '正在调用 Claude 深度研究，预计需要 1-3 分钟...';

            // 滚动到结果区
            section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});

            const es = new EventSource('/research/deep?topic=' + encodeURIComponent(topic));
            let text = '';

            es.onmessage = function(e) {{
                if (e.data === '[DONE]') {{
                    es.close();
                    btn.disabled = false;
                    btn.textContent = '🔬 重新研究';
                    content.innerHTML = renderMarkdown(text);
                    status.textContent = '研究完成，共 ' + text.length + ' 字';
                    return;
                }}
                try {{
                    const d = JSON.parse(e.data);
                    if (d.error) {{
                        es.close();
                        btn.disabled = false;
                        btn.textContent = '🔬 深度研究';
                        content.textContent = '出错了：' + d.error;
                        status.textContent = '';
                        return;
                    }}
                    if (d.chunk) {{
                        text += d.chunk;
                        content.innerHTML = renderMarkdown(text) + '<span class="dr-cursor"></span>';
                    }}
                }} catch(err) {{}}
            }};

            es.onerror = function() {{
                es.close();
                btn.disabled = false;
                btn.textContent = '🔬 深度研究';
                status.textContent = text ? '连接中断，内容可能不完整' : '连接失败，请检查服务是否正常';
            }};
        }}

        function renderMarkdown(text) {{
            const escaped = text
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return escaped.split(/\\n\\n+/).map(block => {{
                if (/^#{1,3} /.test(block)) {{
                    return block
                        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                        .replace(/^# (.+)$/gm, '<h1>$1</h1>');
                }}
                if (/^[-*] /m.test(block)) {{
                    const items = block.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
                    return '<ul>' + items + '</ul>';
                }}
                const inline = block.replace(/[*][*](.+?)[*][*]/g, '<strong>$1</strong>');
                return '<p>' + inline + '</p>';
            }}).join('\\n');
        }}
        </script>
</body>
</html>"""

    return html


def _safe_url(url: str) -> str:
    """只允许 http/https 协议，防止 javascript: 注入。"""
    if url and url.startswith(("http://", "https://")):
        return _html.escape(url)
    return "#"


def _render_papers(papers: list[dict]) -> str:
    """渲染论文列表"""
    if not papers:
        return ""

    items_html = ""
    for paper in papers:
        title = _html.escape(paper.get("title", ""))
        url = _safe_url(paper.get("url", ""))
        score = paper.get("score", 0)
        comment = _html.escape(paper.get("comment", ""))
        authors = paper.get("authors", [])
        author_str = _html.escape(", ".join(authors[:3]))
        if len(paper.get("authors", [])) > 3:
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
        name = _html.escape(repo.get("full_name", repo.get("name", "")))
        url = _safe_url(repo.get("url", ""))
        score = repo.get("score", 0)
        comment = _html.escape(repo.get("comment", ""))
        stars = repo.get("stars", 0)
        language = _html.escape(repo.get("language", ""))

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
        title = _html.escape(disc.get("title", ""))
        url = _safe_url(disc.get("hn_url", disc.get("url", "")))
        score = disc.get("score", 0)
        comment = _html.escape(disc.get("comment", ""))
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
        name = _html.escape(doc.get("name", ""))
        url = _safe_url(doc.get("url", ""))
        score = doc.get("score", 9)
        comment = _html.escape(doc.get("comment", "官方文档，权威可靠"))

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


def _render_articles(articles: list[dict]) -> str:
    """渲染 Web 搜索文章列表"""
    if not articles:
        return ""

    items_html = ""
    for article in articles:
        title = _html.escape(article.get("title", ""))
        url = _safe_url(article.get("url", ""))
        score = article.get("score", 0)
        comment = _html.escape(article.get("comment", ""))
        snippet = _html.escape(article.get("snippet", ""))
        published_date = article.get("published_date", "")
        # 过滤掉 "N/A" 和空值，只显示真实日期（取年月日部分）
        if published_date and published_date != "N/A":
            published_date = _html.escape(published_date[:10])
        else:
            published_date = ""

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{title}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
                {f'<span>{published_date}</span>' if published_date else ''}
            </div>
            {f'<div class="comment">{comment}</div>' if comment else f'<div class="comment">{snippet}</div>'}
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">🌐 技术文章 ({len(articles)})</h2>
        {items_html}
    </div>"""


def _render_wechat(articles: list[dict]) -> str:
    """渲染公众号文章列表"""
    if not articles:
        return ""

    items_html = ""
    for article in articles:
        title = _html.escape(article.get("title", ""))
        url = _safe_url(article.get("url", ""))
        score = article.get("score", 0)
        comment = _html.escape(article.get("comment", ""))
        author = _html.escape(article.get("author", ""))
        published_at = _html.escape(article.get("published_at", ""))
        summary = _html.escape(article.get("summary", ""))

        items_html += f"""
        <div class="item">
            <div class="item-title"><a href="{url}" target="_blank">{title}</a></div>
            <div class="item-meta">
                <span class="score">{score}分</span>
                {f'<span>📱 {author}</span>' if author else ''}
                {f'<span>{published_at}</span>' if published_at else ''}
            </div>
            {f'<div class="comment">{comment}</div>' if comment else f'<div class="comment">{summary}</div>'}
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">📱 公众号 ({len(articles)})</h2>
        {items_html}
    </div>"""


def _render_xhs(notes: list[dict]) -> str:
    """渲染小红书笔记列表（带封面图）"""
    if not notes:
        return ""

    items_html = ""
    for note in notes:
        title = _html.escape(note.get("title", ""))
        url = _safe_url(note.get("url", ""))
        score = note.get("score", 0)
        comment = _html.escape(note.get("comment", ""))
        author = _html.escape(note.get("author", ""))
        cover = _safe_url(note.get("cover", ""))
        liked_count = _html.escape(str(note.get("liked_count", "0")))
        collected_count = _html.escape(str(note.get("collected_count", "0")))
        note_type = note.get("type", "normal")
        type_badge = "🎬 视频" if note_type == "video" else "📝 图文"

        cover_html = f'<img src="{cover}" style="width:80px;height:80px;object-fit:cover;border-radius:6px;flex-shrink:0;" onerror="this.style.display=\'none\'">' if cover and cover != "#" else ""

        items_html += f"""
        <div class="item" style="display:flex;gap:12px;align-items:flex-start;">
            {cover_html}
            <div style="flex:1;min-width:0;">
                <div class="item-title"><a href="{url}" target="_blank">{title}</a></div>
                <div class="item-meta">
                    <span class="score">{score}分</span>
                    <span>{type_badge}</span>
                    {f'<span>@{author}</span>' if author else ''}
                    <span>❤️ {liked_count}</span>
                    <span>⭐ {collected_count}</span>
                </div>
                {f'<div class="comment">{comment}</div>' if comment else ''}
            </div>
        </div>"""

    return f"""
    <div class="section">
        <h2 class="section-title">🍠 小红书 ({len(notes)})</h2>
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
