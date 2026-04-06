# research/ - 主题学习资料搜索

## 功能概述

输入一个主题（如"强化学习"、"RAG"），系统会：
1. 并行搜索多个数据源（ArXiv 论文、GitHub 仓库、HN 讨论、内置文档库、Web 文章）
2. 使用 Claude 为每个资源打分（1-10分）并生成中文点评
3. 过滤低分资源（< 6分）
4. 按类型分类展示结果

## 使用方式

### Web 界面

启动 Flask 应用：

```bash
export ANTHROPIC_API_KEY=your-key
python -m flask --app api.app run
```

访问：http://localhost:5000/research

### Python API

```python
from research.topic_searcher import TopicSearcher

searcher = TopicSearcher(api_key="your-key")
results = searcher.search_topic("强化学习")

print(f"论文: {len(results['papers'])}")
print(f"仓库: {len(results['repositories'])}")
print(f"讨论: {len(results['discussions'])}")
print(f"文档: {len(results['docs'])}")
print(f"文章: {len(results['articles'])}")
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `doc_library.py` | 内置30个常见框架的官方文档 URL |
| `github_search.py` | GitHub Search API 封装 |
| `hn_search.py` | HN Algolia 搜索 API 封装 |
| `claude_scorer.py` | Claude 评分器（批量打分+点评） |
| `topic_searcher.py` | 主题搜索聚合器（并行调用各数据源） |
| `result_renderer.py` | 结果 HTML 渲染器 |
| `web_search.py` | Web 搜索（Google + Bing 双引擎） |

## 数据源

| 数据源 | API | 限制 | 内容类型 |
|--------|-----|------|----------|
| ArXiv | 免费 | 无 | 学术论文 |
| GitHub Search | 免费 | 60次/小时（无认证） | 开源项目 |
| HN Algolia | 免费 | 无 | 技术讨论 |
| 内置文档库 | 本地 | 无 | 官方文档 |
| Google Search | 免费 | 100次/天 | 中文技术文章（优先） |
| Bing Search | 免费 | 1000次/月 | 中文技术文章（降级） |

## 配置

环境变量：

| 变量 | 必须 | 说明 |
|------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key，用于评分 |
| `GOOGLE_SEARCH_API_KEY` | 可选 | Google Custom Search API key |
| `GOOGLE_SEARCH_CX` | 可选 | Google Custom Search Engine ID |
| `BING_SEARCH_API_KEY` | 可选 | Bing Search API key（Google 降级备用） |

**Web 搜索策略：**
1. 优先使用 Google（搜索质量更好）
2. Google 失败或未配置时降级到 Bing
3. 都未配置则跳过 Web 搜索，其他数据源正常工作

## 测试

```bash
# 单元测试
pytest tests/research/ -v

# 集成测试（需要 API key）
ANTHROPIC_API_KEY=your-key pytest tests/research/test_integration.py -v -m slow
```

## 扩展

### 添加新数据源

1. 在 `research/` 下创建新模块（如 `youtube_search.py`）
2. 实现搜索函数，返回统一格式的列表（包含 `title`、`url` 字段）
3. 在 `topic_searcher.py` 的 `search_topic()` 中添加并行调用
4. 在 `result_renderer.py` 中添加渲染逻辑

### 添加新文档

编辑 `doc_library.py` 的 `DOCS_LIBRARY` 字典，按现有格式添加新条目。
