# AI 内容策展工具对比与技术方案研究

> 研究日期：2026-04-05
> 来源：综合 Web 搜索、GitHub、技术文档

---

## 一、AI 内容策展工具全景

### 商业产品

#### 1. Feedly + Leo AI

| 维度 | 详情 |
|------|------|
| **定位** | AI 驱动的 RSS 阅读器 |
| **核心功能** | AI 筛选（Leo）、优先级排序、话题追踪、自动标签 |
| **定价** | Pro $6/月、Pro+ $8.25/月、Enterprise $18/月 |
| **AI 特色** | Leo 可以学习你的阅读偏好，自动标记重要文章 |
| **数据源** | RSS、Twitter、Reddit、YouTube、Newsletter |
| **API** | 有（Pro+ 以上） |

**与我们的关系**：
- 可以作为补充数据源（通过 API 获取 Feedly 的筛选结果）
- Leo 的"AI 优先级"思路值得借鉴
- 但 Feedly 不支持微信公众号

#### 2. Alpha Signal

| 维度 | 详情 |
|------|------|
| **定位** | AI 研究和新闻追踪 |
| **核心功能** | 论文追踪、技术博客聚合、趋势分析 |
| **定价** | 免费版 + 付费版 |
| **特色** | 专注 AI/ML 领域，算法筛选重要论文 |
| **数据源** | ArXiv、技术博客、GitHub Trending |

**与我们的关系**：
- 直接竞品（AI 新闻聚合方向）
- 但不覆盖中文内容和微信公众号
- 论文追踪功能可以借鉴

#### 3. ReadHub

| 维度 | 详情 |
|------|------|
| **定位** | 中文科技新闻聚合 |
| **核心功能** | 热点话题聚合、相关报道归类 |
| **定价** | 免费 |
| **特色** | 将多家媒体对同一事件的报道归到一起 |
| **数据源** | 国内科技媒体（36氪、虎嗅、机器之心等） |

**与我们的关系**：
- 中文领域最接近的竞品
- "话题聚合"功能值得参考
- 但 ReadHub 覆盖范围更广（泛科技），我们专注 AI

#### 4. Artifact（已被收购）

| 维度 | 详情 |
|------|------|
| **定位** | AI 个性化新闻阅读器（由 Instagram 创始人创建） |
| **核心功能** | AI 推荐、TL;DR 摘要、去重 |
| **现状** | 2024 年被 Yahoo 收购 |
| **启示** | AI 新闻策展有明确的市场需求和 exit 路径 |

#### 5. Perplexity Discover

| 维度 | 详情 |
|------|------|
| **定位** | AI 搜索引擎的新闻发现功能 |
| **核心功能** | 基于用户兴趣的 AI 新闻推荐 |
| **特色** | 每条新闻自动生成 AI 摘要 |
| **启示** | AI 摘要 + 新闻推荐的结合方式 |

### 开发者工具

#### 6. Feedly Boards + API

- 可以通过 API 获取筛选后的文章列表
- Pro+ 以上支持 API 访问
- 可以作为我们的补充数据源

#### 7. Inoreader

| 维度 | 详情 |
|------|------|
| **定位** | 专业级 RSS 阅读器 |
| **定价** | 免费 / $2.99 / $4.99 / $9.99 月 |
| **API** | 有（付费版） |
| **特色** | 规则引擎强大，支持自动化工作流 |

---

## 二、开源项目详细分析

### 1. RSS-GPT (yinan-c/RSS-GPT)

| 维度 | 详情 |
|------|------|
| **GitHub** | github.com/yinan-c/RSS-GPT |
| **Star** | 1k+ |
| **技术栈** | Python + GitHub Actions |
| **功能** | RSS 订阅 → GPT 生成摘要 → 输出新的 RSS/HTML |
| **运行方式** | GitHub Actions 定时执行（免费额度内） |

**核心流程**：
```
RSS 源 → 获取新文章 → GPT 生成摘要 → 合并为新 RSS → GitHub Pages 展示
```

**配置示例**：
```yaml
feeds:
  - url: "https://example.com/feed.xml"
    name: "Example Blog"
    max_items: 10
    summary_length: 200
```

**与我们的对比**：

| 维度 | RSS-GPT | 我们的项目 |
|------|---------|-----------|
| 数据源 | RSS | 微信公众号 |
| AI | GPT 摘要 | Claude 去重+摘要+打分 |
| 运行环境 | GitHub Actions | 本地 macOS |
| 输出 | RSS + HTML | HTML + 公众号草稿 |
| 去重 | 简单 URL 去重 | 三级去重（URL+标题+AI） |
| 定制度 | 低 | 高 |

**可借鉴**：GitHub Actions 运行方式（如果我们未来想脱离本地运行）。

### 2. RSSHub (DIYgod/RSSHub)

| 维度 | 详情 |
|------|------|
| **GitHub** | github.com/DIYgod/RSSHub |
| **Star** | 35k+ |
| **技术栈** | Node.js |
| **功能** | 将任何网站内容转换为 RSS |
| **部署** | 自建或使用公共实例 |

**对我们的价值**：
- 可以用 RSSHub 生成微信公众号的 RSS 源
- 但 RSSHub 的微信路由不稳定（依赖第三方平台）
- 更适合接入 Hacker News、Reddit 等海外源

**微信公众号相关路由**：
```
/wechat/mp/profile/{id}  - 公众号文章（通过缓存）
/wechat/miniprogram      - 小程序内容
```

**注意**：RSSHub 的微信路由经常失效，不建议作为主要采集方式。

### 3. Doocs MD (doocs/md)

| 维度 | 详情 |
|------|------|
| **GitHub** | github.com/doocs/md |
| **Star** | 8k+ |
| **技术栈** | Vue.js |
| **功能** | Markdown → 微信公众号富文本 |
| **使用方式** | 在线编辑器或本地部署 |

**核心原理**：
```
Markdown 输入
    ↓ marked.js 解析
HTML 中间格式
    ↓ 主题样式注入
带 inline CSS 的 HTML
    ↓ 复制粘贴
微信公众号编辑器
```

**对我们的价值**：
- 可以参考其 CSS → inline style 的转换逻辑
- 内置的多种主题可以作为排版参考
- 但我们的场景是自动生成，不需要在线编辑器

### 4. WeChat Format (lyricat/wechat-format)

| 维度 | 详情 |
|------|------|
| **GitHub** | github.com/lyricat/wechat-format |
| **Star** | 3k+ |
| **技术栈** | JavaScript |
| **功能** | Markdown → 微信富文本（极简） |

**特色**：极其简洁，核心代码不到 500 行。

### 5. NewNewsAPI (各种新闻 API)

| API | 免费额度 | 数据源 | AI 特性 |
|-----|---------|--------|---------|
| **NewsAPI** | 100次/天 | 8万+新闻源 | 无 |
| **GNews** | 100次/天 | 6万+新闻源 | 无 |
| **Bing News** | 3000次/月 | 微软新闻 | 无 |
| **Google News RSS** | 无限制 | Google 新闻 | 无 |

---

## 三、数据源扩展技术方案

### Hacker News

**API**：完全免费，无需认证

```python
# Hacker News API 示例
import requests

# 获取 Top Stories
top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()

# 获取单条新闻
story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{top_ids[0]}.json").json()
# {
#   "title": "Show HN: ...",
#   "url": "https://...",
#   "score": 256,
#   "time": 1712345678,
#   "descendants": 42  # 评论数
# }
```

**筛选 AI 相关内容**：
```python
AI_KEYWORDS = ["AI", "GPT", "LLM", "Claude", "OpenAI", "machine learning",
               "neural", "transformer", "anthropic", "deep learning"]

def is_ai_related(story: dict) -> bool:
    title = story.get("title", "").lower()
    return any(kw.lower() in title for kw in AI_KEYWORDS)
```

**集成建议**：
- 每天获取 Top 200 条，筛选 AI 相关
- 按 score 排序取前 5-10 条
- 生成中文摘要（用 LLM 翻译+摘要）
- 独立 collector：`collectors/hackernews.py`

**工作量**：3-4 小时

### ArXiv 论文

**方式**：RSS 或 API

```python
# ArXiv RSS 示例
# AI 相关分类：cs.AI, cs.CL, cs.CV, cs.LG, stat.ML

import feedparser

feed = feedparser.parse("https://arxiv.org/rss/cs.AI")
for entry in feed.entries[:10]:
    print(entry.title)
    print(entry.summary)
    print(entry.link)
```

**API 方式**：
```python
import urllib.request
import xml.etree.ElementTree as ET

url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&max_results=20"
response = urllib.request.urlopen(url)
root = ET.parse(response).getroot()
```

**集成建议**：
- 每天获取 cs.AI + cs.CL 最新 20 篇
- 用 LLM 生成通俗中文摘要
- 标注论文 star 数（如果有 GitHub 实现）
- 独立 collector：`collectors/arxiv.py`

**工作量**：3-4 小时

### Reddit r/MachineLearning

**方式**：JSON API（无需认证）

```python
import requests

url = "https://www.reddit.com/r/MachineLearning/hot.json"
headers = {"User-Agent": "news1-bot/1.0"}
response = requests.get(url, headers=headers)
posts = response.json()["data"]["children"]

for post in posts[:10]:
    data = post["data"]
    print(data["title"])
    print(data["score"])
    print(data["url"])
```

**集成建议**：
- 获取 Hot 前 20 条
- 按 upvote 筛选（>100）
- 翻译标题+摘要
- 独立 collector：`collectors/reddit.py`

**工作量**：2-3 小时

### Twitter/X AI KOL

**问题**：API 价格高（$100/月基础版），且政策不稳定

**替代方案**：
1. 通过 RSSHub 获取特定用户推文（不稳定）
2. 通过 Nitter 实例抓取（经常被封）
3. 手动维护重要推文列表

**建议**：暂不接入，等 API 降价或找到稳定免费方案。

---

## 四、AI 策展技术趋势

### 1. RAG（检索增强生成）用于新闻策展

**思路**：将所有采集的新闻建立向量索引，用 RAG 做智能查询和关联。

```
新闻文章 → Embedding → 向量数据库（ChromaDB/Faiss）
用户查询 → Embedding → 相似度搜索 → LLM 生成回答
```

**适用场景**：
- "本周最重要的 AI 融资事件是什么？"
- "最近 Claude 和 GPT 的竞争态势如何？"
- 自动发现相关联的新闻（话题聚合）

**工作量**：大（需要 embedding 管道 + 向量数据库）
**建议**：中期可以考虑，短期不急

### 2. Agent 工作流用于内容策展

**思路**：用 AI Agent 自动完成"搜索→筛选→摘要→排版"全流程。

```
Agent 1: 数据采集（多源）
    ↓
Agent 2: 内容筛选（相关性+重要性）
    ↓
Agent 3: 摘要生成（中文摘要+编辑点评）
    ↓
Agent 4: 排版输出（HTML/公众号稿）
    ↓
Agent 5: 质量审核（查错+合规检查）
```

**适用场景**：完全自动化的内容生产。

**工作量**：大（需要 Agent 框架 + 多步编排）
**建议**：概念验证可以做，但目前的管道式架构已经够用

### 3. 个性化推荐

**思路**：根据读者历史行为推荐内容。

**公众号限制**：
- 公众号推送是"一对所有"，无法个性化
- 但可以在网页版/小程序中实现个性化
- 或者用微信社群分流（不同兴趣群推送不同内容）

---

## 五、工具和技术选型建议

### 短期推荐技术栈

| 需求 | 推荐方案 | 理由 |
|------|---------|------|
| 微信采集 | CDP + 同步 XHR（现有） | 已验证稳定 |
| HN/Reddit 采集 | requests + JSON API | 简单可靠 |
| ArXiv 采集 | feedparser + RSS | 成熟方案 |
| AI 摘要 | Claude Haiku | 成本低质量好 |
| AI 去重 | Claude Sonnet（现有） | 准确率高 |
| 存储 | SQLite（现有） | 足够用 |
| 定时任务 | launchd（现有） | macOS 原生 |
| 通知 | osascript（现有） | 简单可靠 |

### 中期考虑

| 需求 | 推荐方案 | 触发条件 |
|------|---------|---------|
| 服务器部署 | GitHub Actions 或 VPS | 想脱离本地运行 |
| 向量搜索 | ChromaDB | 需要话题聚合 |
| Web 管理后台 | Streamlit | 需要可视化管理 |
| 多租户 | PostgreSQL | SaaS 化 |

---

## 六、竞品功能对比矩阵

| 功能 | 我们 | ReadHub | Alpha Signal | RSS-GPT | Feedly+Leo |
|------|------|---------|--------------|---------|------------|
| 微信公众号源 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 中文内容 | ✅ | ✅ | ❌ | ❌ | ❌ |
| AI 摘要 | ✅ | ❌ | ❌ | ✅ | ❌ |
| AI 去重 | ✅ | ✅ | ❌ | ❌ | ❌ |
| AI 打分 | ✅ | ❌ | ✅ | ❌ | ✅ |
| 公众号发布 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 海外源 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 论文追踪 | ❌ | ❌ | ✅ | ❌ | ❌ |
| 个性化 | ❌ | ❌ | ✅ | ❌ | ✅ |
| 免费 | ✅ | ✅ | 部分 | ✅ | 部分 |

**我们的独特优势**：
1. ✅ 唯一支持微信公众号源的自动化方案
2. ✅ 采集→处理→发布全链路自动化
3. ✅ 中文 AI 内容的三级去重

**需要补强**：
1. ❌ 海外数据源接入（HN/ArXiv/Reddit）
2. ❌ 论文追踪
3. ❌ 个性化推荐

---

## 七、实施优先级建议

### 第一批（1-2 周内）

| 任务 | 预期收益 | 工作量 |
|------|---------|--------|
| Hacker News 接入 | 丰富海外视角 | 3-4h |
| AI 编辑点评 | 提升内容差异化 | 2-3h |
| AI 内容标注 | 合规必须 | 0.5h |

### 第二批（1 个月内）

| 任务 | 预期收益 | 工作量 |
|------|---------|--------|
| ArXiv 论文摘要 | 增加学术内容 | 3-4h |
| 发布时间优化 | 提升打开率 | 1h |
| logging 替代 print | 提升可维护性 | 3-4h |

### 第三批（1-3 个月内）

| 任务 | 预期收益 | 工作量 |
|------|---------|--------|
| Reddit 接入 | 补充社区讨论 | 2-3h |
| 周报自动生成 | 增加内容类型 | 4-6h |
| 配置文件统一 | 降低维护成本 | 3-4h |
| 类型提示完善 | 提升代码质量 | 3-4h |
