"""主题研究功能的 Flask 路由。"""
import html as _html
import json
import os
from flask import request, jsonify, Response, stream_with_context
from research.topic_searcher import TopicSearcher
from research.result_renderer import render_results_html
from storage.research_repository import ResearchRepository
from utils.config import get_claude_config
from utils.log import get_logger

logger = get_logger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content.db")


def _make_searcher() -> TopicSearcher:
    """创建 TopicSearcher 实例（复用配置读取逻辑）。"""
    api_key, base_url = get_claude_config()
    return TopicSearcher(
        api_key=api_key,
        base_url=base_url,
        google_api_key=os.getenv("GOOGLE_SEARCH_API_KEY", ""),
        google_cx=os.getenv("GOOGLE_SEARCH_CX", ""),
        bing_api_key=os.getenv("BING_SEARCH_API_KEY", ""),
        db_path=DB_PATH,
    )

def register_research_routes(app):
    """注册研究功能路由。"""

    @app.get("/research")
    def get_research_page():
        """返回搜索界面 HTML"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 学习资料搜索</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { text-align: center; color: #2d3748; font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #718096; margin-bottom: 40px; font-size: 1.1em; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] {
            flex: 1; padding: 16px 20px; font-size: 1.1em;
            border: 2px solid #e2e8f0; border-radius: 12px; outline: none;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus { border-color: #667eea; }
        button {
            padding: 16px 32px; font-size: 1.1em; font-weight: 600;
            color: white; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none; border-radius: 12px; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .examples { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
        .example {
            padding: 8px 16px; background: #edf2f7; border-radius: 20px;
            font-size: 0.9em; color: #4a5568; cursor: pointer; transition: background 0.2s;
        }
        .example:hover { background: #e2e8f0; }
        .loading { display: none; text-align: center; color: #718096; margin-top: 20px; }
        .loading.show { display: block; }
        .spinner {
            display: inline-block; width: 20px; height: 20px;
            border: 3px solid #e2e8f0; border-top-color: #667eea;
            border-radius: 50%; animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 AI 学习资料搜索</h1>
        <p class="subtitle">输入主题，发现高质量学习资源</p>
        <div class="search-box">
            <input type="text" id="topicInput" placeholder="例如：强化学习、RAG、Transformer..." />
            <button onclick="search()">搜索</button>
        </div>
        <div class="examples">
            <span class="example" onclick="fillExample('强化学习')">强化学习</span>
            <span class="example" onclick="fillExample('RAG')">RAG</span>
            <span class="example" onclick="fillExample('Transformer')">Transformer</span>
            <span class="example" onclick="fillExample('多模态')">多模态</span>
            <span class="example" onclick="fillExample('Agent')">Agent</span>
        </div>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在搜索中，请稍候...</p>
        </div>
    </div>
    <script>
        const input = document.getElementById('topicInput');
        const loading = document.getElementById('loading');
        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') search(); });
        function fillExample(topic) { input.value = topic; input.focus(); }
        async function search() {
            const topic = input.value.trim();
            if (!topic) { alert('请输入搜索主题'); return; }
            window.location.href = '/research/results?topic=' + encodeURIComponent(topic);
        }
    </script>
</body>
</html>"""
        return html

    @app.get("/research/results")
    def get_research_results():
        """显示搜索结果页面——直接渲染，不依赖 sessionStorage"""
        topic = request.args.get('topic', '').strip()
        if not topic:
            return '<h1>缺少 topic 参数</h1>', 400

        api_key, _ = get_claude_config()
        if not api_key:
            return '<h1>未配置 ANTHROPIC_API_KEY</h1>', 500

        try:
            results = _make_searcher().search_topic(topic)
            # 保存搜索历史
            repo = ResearchRepository(DB_PATH)
            session_id = repo.save_session(topic, results)
            logger.info("搜索历史已保存 session_id=%d topic=%s", session_id, topic)
            return render_results_html(topic, results, session_id=session_id)
        except Exception as e:
            logger.error("搜索失败: %s", e, exc_info=True)
            return f'<h1>搜索出错</h1><p>{_html.escape(str(e))}</p>', 500

    @app.post("/api/research")
    def post_research():
        """执行主题搜索"""
        data = request.get_json()
        if not data or 'topic' not in data:
            return jsonify({"error": "缺少 topic 参数"}), 400

        topic = data['topic'].strip()
        if not topic:
            return jsonify({"error": "topic 不能为空"}), 400

        logger.info("收到搜索请求: %s", topic)

        api_key, _ = get_claude_config()
        if not api_key:
            return jsonify({"error": "未配置 ANTHROPIC_API_KEY 环境变量"}), 500

        try:
            results = _make_searcher().search_topic(topic)
            return jsonify(results)
        except Exception as e:
            logger.error("搜索失败: %s", e, exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.post("/api/research/render")
    def post_research_render():
        """渲染搜索结果为 HTML"""
        data = request.get_json()
        topic = data.get('topic', '未知主题')
        results = data.get('results', {})
        html = render_results_html(topic, results)
        return html

    @app.get("/research/history")
    def get_research_history():
        """搜索历史列表页"""
        repo = ResearchRepository(DB_PATH)
        sessions = repo.list_sessions(limit=50)
        rows_html = "".join(
            f'<tr><td>{s["id"]}</td>'
            f'<td><a href="/research/history/{s["id"]}">{_html.escape(s["topic"])}</a></td>'
            f'<td>{s["created_at"][:16]}</td></tr>'
            for s in sessions
        ) or "<tr><td colspan='3'>暂无搜索记录</td></tr>"
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>搜索历史</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ font-size: 1.5em; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #f5f7fa; font-weight: 600; }}
  a {{ color: #667eea; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .back {{ margin-bottom: 16px; display: inline-block; color: #718096; }}
</style>
</head>
<body>
  <a class="back" href="/research">← 返回搜索</a>
  <h1>搜索历史</h1>
  <table>
    <thead><tr><th>#</th><th>主题</th><th>时间</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</body>
</html>"""

    @app.get("/research/history/<int:session_id>")
    def get_research_history_detail(session_id: int):
        """从历史记录直接渲染结果，不重新搜索"""
        repo = ResearchRepository(DB_PATH)
        session = repo.get_session(session_id)
        if not session:
            return '<h1>记录不存在</h1>', 404
        return render_results_html(session["topic"], session["results"], session_id=session_id)

    @app.get("/research/deep")
    def get_research_deep():
        """SSE 流式深度研究：横纵分析法 + Claude API"""
        topic = request.args.get('topic', '').strip()[:200]
        if not topic:
            return jsonify({"error": "缺少 topic 参数"}), 400

        api_key, base_url = get_claude_config()
        if not api_key:
            return jsonify({"error": "未配置 ANTHROPIC_API_KEY"}), 500

        prompt = f"""Produce a complete deep research report on「{topic}」using the Horizontal-Vertical Analysis Method.

The report has two main dimensions:

### Part 1: Longitudinal Analysis (Diachronic)
Trace the full history of 「{topic}」from its origin to today:
1. Origin: background, founding team, initial technology/concept, industry context at the time
2. Birth milestone: first release/founding date and initial positioning
3. Evolution: all key milestones in chronological order — major version updates, funding rounds, team changes, strategic pivots, architecture changes, user growth milestones, partnerships, controversies
4. Decision logic: at each key milestone, explain WHY — what constraints existed, why option A over option B
5. Narrative style: write as a compelling story with cause-and-effect, not a dry timeline

### Part 2: Horizontal Analysis (Synchronic)
Compare 「{topic}」with competitors/peers at the current moment:
- First assess: no competitors (Scene A) / few competitors (Scene B) / many competitors (Scene C)
- Compare on: technical approach, product form, target users, core strengths/weaknesses, pricing
- User perspective: real user feedback, actual usage vs official positioning
- Ecosystem position: what niche does it occupy in the landscape
- Trend: competitive trajectory, opportunities and risks

### Writing style requirements:
- Readable like a quality long-form tech article, not a consulting report
- Narrative-driven, not list-driven — the longitudinal part needs story arcs
- Opinions welcome but must be grounded in facts; label speculation clearly
- Plain language — avoid buzzwords
- Warm comparisons — explain what each competitor "became", not just feature diffs

### Length:
- Longitudinal: 3000-8000 Chinese characters
- Horizontal: 1500-5000 Chinese characters
- Final synthesis (横纵交汇): 800-1500 Chinese characters combining both dimensions

### Output format:
1. Longitudinal analysis first, then horizontal
2. End with 「横纵交汇」synthesis giving your judgment on 「{topic}」's current position and future trajectory
3. Write the full report in Chinese
4. Label sources/dates where possible; label speculation explicitly"""

        def generate():
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
                with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    for text in stream.text_stream:
                        yield f"data: {json.dumps({'chunk': text})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error("深度研究失败: %s", e, exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

