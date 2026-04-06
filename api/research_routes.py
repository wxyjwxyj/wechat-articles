"""主题研究功能的 Flask 路由。"""
import os
from flask import request, jsonify
from research.topic_searcher import TopicSearcher
from research.result_renderer import render_results_html
from utils.log import get_logger

logger = get_logger(__name__)


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
            loading.classList.add('show');
            try {
                const response = await fetch('/api/research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic })
                });
                if (!response.ok) throw new Error('搜索失败');
                const data = await response.json();
                sessionStorage.setItem('searchResults', JSON.stringify(data));
                window.location.href = '/research/results?topic=' + encodeURIComponent(topic);
            } catch (error) {
                alert('搜索出错：' + error.message);
                loading.classList.remove('show');
            }
        }
    </script>
</body>
</html>"""
        return html

    @app.get("/research/results")
    def get_research_results():
        """显示搜索结果页面"""
        topic = request.args.get('topic', '未知主题')
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - 学习资料</title>
</head>
<body>
    <div id="results"></div>
    <script>
        const results = JSON.parse(sessionStorage.getItem('searchResults') || '{{}}');
        const topic = decodeURIComponent('{topic}');
        fetch('/api/research/render', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ topic, results }})
        }})
        .then(r => r.text())
        .then(html => {{ document.body.innerHTML = html; }})
        .catch(e => {{ document.body.innerHTML = '<h1>加载失败</h1><p>' + e.message + '</p>'; }});
    </script>
</body>
</html>"""
        return html

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

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return jsonify({"error": "未配置 ANTHROPIC_API_KEY"}), 500

        try:
            searcher = TopicSearcher(
                api_key=api_key,
                google_api_key=os.getenv("GOOGLE_SEARCH_API_KEY", ""),
                google_cx=os.getenv("GOOGLE_SEARCH_CX", ""),
                bing_api_key=os.getenv("BING_SEARCH_API_KEY", ""),
            )
            results = searcher.search_topic(topic)
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
