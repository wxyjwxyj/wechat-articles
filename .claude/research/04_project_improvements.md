# 项目代码审查与改进建议

> 研究日期：2026-04-05
> 基于对项目代码的全面阅读和分析

---

## 一、当前架构评估

### 整体架构

```
collectors/          ← 数据采集
  └── wechat.py      ← 微信公众号采集器
pipeline/            ← 数据处理管道
  ├── normalize.py   ← 标准化
  ├── dedupe.py      ← 去重
  ├── tagging.py     ← 标签提取
  └── bundles.py     ← Bundle 生成
publishers/          ← 输出发布
  ├── html_preview.py     ← HTML 预览页
  ├── mp_publisher.py     ← 公众号草稿发布
  ├── mp_article.py       ← 公众号文章生成
  └── cover_generator.py  ← 封面图生成
storage/             ← 数据存储
  ├── db.py          ← 数据库初始化
  └── repository.py  ← 数据访问层
api/                 ← API 接口
  └── app.py         ← Flask API
scripts/             ← 执行脚本
  ├── seed_sources.py
  ├── build_bundle.py
  └── generate_mp_article.py
tests/               ← 测试
  └── 14 个测试文件
```

**架构评分：7/10**

**优点：**
- 模块职责清晰（采集/处理/发布/存储 分离）
- SQLite 作为单一数据源，数据流清晰
- Bundle 作为中间格式解耦了采集和输出
- 脚本入口统一，daily_run.sh 编排合理

**需改进：**
- 配置散落在多处（config.json、脚本内硬编码、环境变量）
- 错误处理不够统一
- 日志用 print 而非 logging 模块
- 类型提示不完整

---

## 二、P0 改进（必须做）

### 1. AI 内容标注合规

**问题**：2025年3月起强制要求标注 AI 生成内容，目前项目未添加标注。

**改进方案**：

在 `publishers/mp_article.py` 生成的 HTML 末尾添加合规标注：

```python
# 在生成的文章 HTML 末尾添加
AI_DISCLAIMER = '''
<section style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee;">
  <p style="color: #999; font-size: 12px; line-height: 1.6;">
    📌 本文由 AI 辅助采集和整理，经人工审核后发布。
  </p>
</section>
'''
```

**工作量**：0.5 小时

### 2. 错误处理统一

**问题**：各模块的错误处理不一致，有的用 try/except，有的直接抛异常，有的静默失败。

**改进方案**：

```python
# 新建 utils/errors.py

class News1Error(Exception):
    """基础异常类"""
    pass

class CollectorError(News1Error):
    """采集相关错误"""
    pass

class CDPConnectionError(CollectorError):
    """CDP 连接失败"""
    pass

class LoginExpiredError(CollectorError):
    """登录态过期"""
    pass

class PipelineError(News1Error):
    """数据处理错误"""
    pass

class PublishError(News1Error):
    """发布相关错误"""
    pass
```

**关键改动点**：

| 文件 | 改动 |
|------|------|
| `collectors/wechat.py` | 捕获 CDP 连接失败，抛 CDPConnectionError |
| `pipeline/dedupe.py` | Claude API 超时时降级为简单去重 |
| `publishers/mp_publisher.py` | 草稿提交失败记录详细原因 |
| `daily_run.sh` | 根据 exit code 区分失败类型 |

**工作量**：2-3 小时

### 3. 采集失败通知增强

**问题**：当前通知只区分"成功/失败/无内容"，不告知具体原因。

**改进方案**：

```bash
# daily_run.sh 中增强通知内容
if [ $EXIT_CODE -ne 0 ]; then
    case $EXIT_CODE in
        10) REASON="CDP Proxy 未启动" ;;
        11) REASON="浏览器登录态过期" ;;
        12) REASON="采集超时" ;;
        13) REASON="AI API 调用失败" ;;
        14) REASON="草稿提交失败" ;;
        *)  REASON="未知错误 (code=$EXIT_CODE)" ;;
    esac
    osascript -e "display notification \"失败原因：$REASON\" with title \"AI 日报\""
fi
```

**工作量**：1 小时

---

## 三、P1 改进（应该做）

### 4. 引入 logging 模块

**问题**：全项目使用 `print()` 输出日志，无法控制级别、无法统一格式。

**改进方案**：

```python
# utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "news1", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(console)

    # 文件输出
    log_dir = Path(".claude/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    from datetime import date
    file_handler = logging.FileHandler(
        log_dir / f"{date.today()}.log", encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(file_handler)

    return logger
```

**迁移策略**：
- 逐模块替换，不一次性重构
- 优先替换 `collectors/` 和 `publishers/`（最容易出问题的模块）
- `print()` 和 `logging` 可以暂时共存

**工作量**：3-4 小时

### 5. 配置文件统一

**问题**：配置散落在 config.json、脚本硬编码、环境变量等多处。

**改进方案**：

```python
# config/settings.py
from dataclasses import dataclass, field
from pathlib import Path
import json

@dataclass
class CDPConfig:
    proxy_url: str = "http://localhost:3456"
    timeout: int = 30

@dataclass
class AIConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1000
    temperature: float = 0.3

@dataclass
class PublishConfig:
    draft_only: bool = True  # 永远只提交草稿
    cover_size: tuple = (900, 383)
    ai_disclaimer: str = "本文由 AI 辅助采集和整理，经人工审核后发布。"

@dataclass
class Settings:
    cdp: CDPConfig = field(default_factory=CDPConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    publish: PublishConfig = field(default_factory=PublishConfig)
    db_path: Path = Path("content.db")
    bundle_output: Path = Path("bundle_today.json")

    @classmethod
    def load(cls, path: str = "config.json") -> "Settings":
        # 从文件加载，缺失字段用默认值
        ...
```

**工作量**：3-4 小时

### 6. 测试覆盖提升

**当前状态**：14 个测试，覆盖 schema/normalize/dedupe/tagging/bundles/mp_article/api

**缺失的测试**：

| 模块 | 需要的测试 | 优先级 |
|------|-----------|--------|
| `collectors/wechat.py` | CDP 连接、文章解析、日期过滤 | P1 |
| `publishers/mp_publisher.py` | 草稿创建（mock CDP） | P1 |
| `publishers/cover_generator.py` | 封面图尺寸、文字渲染 | P2 |
| `pipeline/bundles.py` | 边界情况（0篇、1篇、50篇） | P1 |
| `daily_run.sh` | 集成测试（各步骤独立验证） | P2 |

**建议新增测试**：

```python
# tests/test_collector_wechat.py
def test_parse_article_response():
    """验证文章列表 JSON 解析"""

def test_filter_today_articles():
    """验证只返回今天的文章"""

def test_cdp_connection_failure():
    """验证 CDP 连接失败时的错误处理"""

# tests/test_publisher_mp.py
def test_create_draft_formdata():
    """验证 FormData 格式正确"""

def test_draft_with_cover():
    """验证带封面的草稿创建"""
```

**工作量**：4-6 小时

### 7. 类型提示完善

**问题**：大部分函数缺少类型提示，IDE 无法提供补全和检查。

**改进方案**：
- 为所有公共函数添加类型提示
- 关键数据结构用 TypedDict 定义
- 配置 mypy 基础检查

```python
# types.py
from typing import TypedDict, Optional

class ArticleItem(TypedDict):
    title: str
    url: str
    summary: str
    published_at: str
    source_name: str
    tags: list[str]
    score: Optional[int]

class BundleDict(TypedDict):
    bundle_date: str
    title: str
    intro: str
    topics: list[dict]
    items_flat: list[ArticleItem]
    highlights: list[dict]
```

**工作量**：3-4 小时

---

## 四、P2 改进（锦上添花）

### 8. LLM 编辑点评增强

**当前**：简单摘要，缺乏个性化点评。

**改进**：用 LLM 为每条新闻生成编辑点评。

```python
COMMENT_PROMPT = """你是一位 AI 行业观察者，请为以下新闻写一句简短的编辑点评（15-30字）：
- 要有观点，不要中性描述
- 可以用比喻或类比
- 口语化，像朋友推荐给你看

标题：{title}
摘要：{summary}
"""
```

**成本估算**：
- 每条新闻约 200 tokens（输入）+ 50 tokens（输出）
- 每日 8 条 ≈ 2,000 tokens
- Claude Haiku 成本：约 $0.001/天 ≈ ¥0.007/天
- **几乎可以忽略不计**

### 9. 内容相关度评分优化

**当前**：基于关键词的简单打分。

**改进**：用 LLM 做更智能的评分。

```python
SCORING_PROMPT = """请为以下 AI 新闻打分（1-10），考虑：
- 新闻重要性（影响范围大小）
- 时效性（是否是今天的新消息）
- 读者价值（AI 从业者会感兴趣吗）
- 独特性（是否只有少数来源报道）

标题：{title}
摘要：{summary}
来源：{source}

只返回数字分数。"""
```

### 10. A/B 标题测试

**方案**：生成 2-3 个候选标题，选择最佳。

```python
TITLE_PROMPT = """为今日 AI 日报生成 3 个标题选项：
1. 基于今日最重要新闻的标题
2. 引发好奇心的标题
3. 数据驱动的标题

今日头条新闻：{top_news}
"""
```

### 11. 阅读数据回收

**方案**：定时爬取已发布文章的阅读数据。

```python
# 通过 CDP 获取文章阅读数据
def get_article_stats(app_msg_id: str) -> dict:
    """获取文章阅读量、点赞数、分享数"""
    # 调用 mp.weixin.qq.com 的统计接口
    ...
```

**用途**：
- 分析哪类内容最受欢迎
- 优化选题和标题策略
- 为变现（广告定价）提供数据支撑

---

## 五、架构层面建议

### 短期：补全缺失的基础设施

1. ✅ 统一错误处理（P0）— `76da0d7`
2. ✅ logging 替代 print（P1）— `583bd29`
3. ⬜ 配置统一管理（P1）— 待做
4. ⬜ 类型提示（P1）— 待做

### 中期：功能扩展

1. ✅ 多源数据接入（Hacker News）— `64df390`
2. ✅ 多源数据接入（ArXiv）— `cb37a64`
3. ✅ 多源数据接入（GitHub Trending）— `9b204c6`
4. ✅ LLM 编辑点评 — `529f8c8`
5. ✅ 内容质量评分（Claude 打分，集成在 build_bundle 中）
6. ✅ 导读精选多样性保底（HN/ArXiv/GitHub 各保底1条）— `647ef16`
7. 周报/月报自动生成

### 长期：产品化

1. Web 管理后台（配置数据源、查看统计）
2. 多租户支持
3. 模板市场
4. API 商业化

---

## 六、技术债务清理

### 废弃文件清理

✅ **已完成** — 废弃脚本已在之前的 session 中清理，项目根目录不再存在这些文件。

### 依赖管理

✅ **已完成** — `ec3bc0f` 创建了 `pyproject.toml`。

---

## 七、性能优化

### 当前瓶颈分析

| 步骤 | 耗时 | 瓶颈 |
|------|------|------|
| CDP 采集 | 30-60s | 网络请求 + 同步 XHR |
| 去重（Claude） | 10-20s | API 调用 |
| 标签提取 | <1s | CPU，可忽略 |
| Bundle 生成 | <1s | CPU，可忽略 |
| HTML 生成 | <1s | CPU，可忽略 |
| 封面图生成 | 1-2s | Pillow 渲染 |
| 草稿提交 | 5-10s | 网络请求 |
| GitHub Pages 推送 | 10-20s | Git + 网络 |

**总耗时**：约 1-2 分钟，对日报场景完全够用。

**优化优先级**：低。当前性能无瓶颈。

### 如果未来量级增大

- 采集 20+ 源：考虑并发采集（asyncio 或线程池）
- 去重 50+ 条：考虑批量调用 Claude API
- 多模板输出：考虑模板缓存

---

## 八、安全建议

### 当前安全措施

✅ 配置文件不入 git（.gitignore）
✅ 只提交草稿不自动发布
✅ CDP 仅本地监听
✅ Claude Code hooks 保护敏感文件

### 需要加强

| 风险 | 说明 | 建议 |
|------|------|------|
| 登录态泄露 | Chrome session 可被复用 | 定期手动登出+重新登录 |
| API Key 硬编码 | 部分脚本中可能有 | 统一从环境变量读取 |
| 数据库无加密 | SQLite 明文存储 | 对敏感数据（如 token）加密 |
| 日志泄露 | 日志可能包含 token | 日志脱敏处理 |
