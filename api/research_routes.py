"""主题研究功能的 Flask 路由。"""
import html as _html
import json
import os
import time
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
    api_key, base_url, _ = get_claude_config()
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
        .btn-row { display: flex; gap: 10px; margin-bottom: 20px; }
        .btn-deep {
            flex: 1; padding: 16px 20px; font-size: 1.05em; font-weight: 600;
            color: white; background: linear-gradient(135deg, #f093fb 0%, #f5a623 100%);
            border: none; border-radius: 12px; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-deep:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(240,147,251,0.4); }
        .btn-copy {
            padding: 16px 20px; font-size: 1.05em; font-weight: 600;
            color: #764ba2; background: #f3e8ff;
            border: 2px solid #d8b4fe; border-radius: 12px; cursor: pointer;
            transition: background 0.2s;
            white-space: nowrap;
        }
        .btn-copy:hover { background: #e9d5ff; }
        .copy-tip { text-align: center; font-size: 0.85em; color: #48bb78; min-height: 1.2em; margin-top: -10px; margin-bottom: 10px; }
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
        <div class="btn-row">
            <button class="btn-copy" onclick="copyPrompt()" title="复制横纵分析提示词，粘贴到任意 AI 使用">📋 复制深度研究提示词</button>
        </div>
        <div class="copy-tip" id="copyTip"></div>
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
        function copyPrompt() {
            const topic = document.getElementById('topicInput').value.trim() || '你的主题';
            const prompt = buildDeepResearchPrompt(topic);
            navigator.clipboard.writeText(prompt).then(() => {
                const tip = document.getElementById('copyTip');
                tip.textContent = '✅ 已复制！粘贴到任意 AI 即可使用';
                setTimeout(() => { tip.textContent = ''; }, 3000);
            });
        }
        function buildDeepResearchPrompt(topic) {
            return `请用横纵分析法，对「${topic}」撰写一份完整的深度研究报告。

报告分两个维度：

【纵轴：历时分析】
从起源到今天，完整追溯「${topic}」的发展历程：
1. 起源：背景、创始团队、初始技术/概念、当时的行业环境
2. 诞生节点：首次发布/成立时间与初始定位
3. 演进：按时间顺序列出所有关键里程碑——重大版本更新、融资轮次、团队变化、战略转型、架构调整、用户增长节点、合作关系、争议事件
4. 决策逻辑：每个关键节点，解释"为什么"——当时有哪些约束，为何选A而非B
5. 叙事风格：写成有因果逻辑的故事，而非干燥的时间线

【横轴：共时分析】
在当下时间截面，将「${topic}」与竞品/同类进行系统对比：
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
2. 最后以"横纵交汇"为标题，给出你对「${topic}」当前处境与未来走向的判断
3. 全文用中文撰写
4. 尽量标注信息来源和时间；推测内容明确标注`;
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

        api_key, _, _ = get_claude_config()
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

        api_key, _, _ = get_claude_config()
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
        if not data:
            return '<h1>请求体必须为 JSON</h1>', 400
        topic = data.get('topic', '未知主题')[:200]
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

        api_key, base_url, _ = get_claude_config()
        if not api_key:
            return jsonify({"error": "未配置 ANTHROPIC_API_KEY"}), 500

        # 清洗 topic，防止书名号闭合导致 prompt injection
        topic_safe = topic.replace('「', '').replace('」', '')

        prompt = f"""请用横纵分析法，对「{topic_safe}」撰写一份完整的深度研究报告。

报告分两个维度：

【纵轴：历时分析】
从起源到今天，完整追溯「{topic_safe}」的发展历程：
1. 起源：背景、创始团队、初始技术/概念、当时的行业环境
2. 诞生节点：首次发布/成立时间与初始定位
3. 演进：按时间顺序列出所有关键里程碑——重大版本更新、融资轮次、团队变化、战略转型、架构调整、用户增长节点、合作关系、争议事件
4. 决策逻辑：每个关键节点，解释"为什么"——当时有哪些约束，为何选A而非B
5. 叙事风格：写成有因果逻辑的故事，而非干燥的时间线

【横轴：共时分析】
在当下时间截面，将「{topic_safe}」与竞品/同类进行系统对比：
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
2. 最后以"横纵交汇"为标题，给出你对「{topic_safe}」当前处境与未来走向的判断
3. 全文用中文撰写
4. 尽量标注信息来源和时间；推测内容明确标注"""

        def generate():
            try:
                from utils.claude import claude_stream
                first_chunk = True
                t_start = time.time()
                char_count = 0
                with claude_stream(prompt, max_tokens=8192) as stream:
                    for text in stream.text_stream:
                        if first_chunk:
                            logger.info("深度研究首个 chunk（%.1fs）: %s", time.time() - t_start, repr(text[:100]))
                            first_chunk = False
                        char_count += len(text)
                        yield f"data: {json.dumps({'chunk': text})}\n\n"
                logger.info("深度研究完成：%.1fs，共 %d 字", time.time() - t_start, char_count)
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error("深度研究失败: %s", e, exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

