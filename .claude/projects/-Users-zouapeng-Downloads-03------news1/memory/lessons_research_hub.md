# Topic Research Hub — 经验教训

---

## 一、功能背景

现有系统是**定时拉取实时新闻**，Research Hub 是**按需检索学习资料**。
输入主题（如"强化学习"、"RAG"）→ 并行检索6个数据源 → Claude 评分 → HTML 展示。

访问：`python -m flask --app api.app run` → http://localhost:5000/research

---

## 二、架构

### 数据源（6个并行，ThreadPoolExecutor）

| 源 | 模块 | 备注 |
|----|------|------|
| ArXiv 论文 | `research/arxiv_search.py` | 有时 429 限流 |
| GitHub 仓库 | `research/github_search.py` | 全文搜索会带入无关高star项目 |
| HN 讨论 | `research/hn_search.py` | Algolia API |
| 官方文档库 | `research/doc_library.py` | 30+ 框架，本地关键词匹配 |
| Web 搜索 | `research/web_search.py` | Google→Bing→DuckDuckGo 三级降级 |
| 本地公众号 | `research/wechat_search.py` | 查 content.db，LIKE 匹配 |

### Claude 评分器
- `research/claude_scorer.py`，`score_resources(resources, topic=topic)`
- 传入 `topic` 参数，prompt 中加约束：**无关内容强制打 1-2 分**
- 解决 GitHub 高 star 无关项目（如 JavaGuide）混入结果的问题

### 文档库
- `research/doc_library.py`，30+ 框架预设 URL + 标签
- 搜索"Agent"现在返回 10 条（之前 1 条）
- 已补充：LangGraph、AutoGen、CrewAI、OpenAI Assistants API
- 已加 "agent" tag：LangChain、LlamaIndex、OpenAI、Anthropic、RL 框架

---

## 三、实现过程

### 并行 agent 执行（2026-04-06）

大型计划（3099 行）不内联执行，用 5 个后台 agent 并行跑 Task 1-5，耗时 ~4 分钟（vs 估计20-30分钟）。

| Task | 状态 | 文件 |
|------|------|------|
| Task 1: 文档库 | ✅ | `research/doc_library.py` |
| Task 2: ArXiv 扩展 | ✅ | `collectors/arxiv.py` |
| Task 3: GitHub Search | ✅ | `research/github_search.py` |
| Task 4: HN Search | ✅ | `research/hn_search.py` |
| Task 5: Claude 评分器 | ✅ | `research/claude_scorer.py` |
| Task 6: 主题搜索聚合器 | ✅ | `research/topic_searcher.py` |
| Task 7: 结果渲染器 | ✅ | `research/result_renderer.py` |
| Task 8: Flask 路由 | ✅ | `api/research_routes.py` |
| Task 9: 集成测试+文档 | ✅ | `research/README.md` |
| Task 10: Web Search | ✅ | `research/web_search.py` |

### Task 10 遗留补丁
agent 完成后发现 `topic_searcher.py` 未接入 WebSearcher，手动补接：
- 加 `max_articles`/`google_api_key`/`google_cx`/`bing_api_key` 参数
- 加 `_search_web()` 方法 + `articles` 评分和归一化
- `result_renderer.py` 加 `_render_articles()` 和统计徽章

---

## 四、Web 搜索三级降级

原方案 Google→Bing 都需要 API key，无法零配置。

| 级别 | 引擎 | 要求 |
|------|------|------|
| 1 | Google Custom Search | API key + CX（100次/天） |
| 2 | Bing Search | API key（1000次/月） |
| 3 | DuckDuckGo | **零配置**，`pip install ddgs` |

DuckDuckGo 用法：`region="cn-zh"` 优先中文内容，中文搜索质量正常。
注意：库已从 `duckduckgo_search` 更名为 `ddgs`。

---

## 五、教训

- **大型计划不要内联执行**：3000+ 行计划会耗尽 token 预算，用并行后台 agent
- **agent 完成后要人工 review 接口对接**：本次 topic_searcher 遗漏了 web_search 接入
- **零配置可用性**：依赖外部 API key 的功能必须有免费兜底，否则开箱体验差
- **需求确认要问清 6W**：避免做完发现方向错了
- **文档库要持续维护**：新框架出来及时加，tag 要覆盖常见别名（如 "agent"/"智能体"）
- **评分器要有主题约束**：不传 topic 会导致高质量但无关内容混入结果
