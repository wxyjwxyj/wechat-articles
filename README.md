# AI 日报自动化系统

多源 AI 资讯采集 → 去重打标签 → 生成公众号稿件 → 提交草稿箱 → 推送 GitHub Pages，全链路自动化。

## 快速开始

### 环境要求

- Python 3.11+
- Chrome 浏览器（需登录微信公众平台，供 CDP 采集使用）
- CDP Proxy（本地运行于 localhost:3456）
- `.env` 文件（含 `ANTHROPIC_API_KEY`）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

```bash
cp config.example.json config.json   # 填入 cdp_proxy 地址
cp .env.example .env                 # 填入 ANTHROPIC_API_KEY
python scripts/seed_sources.py       # 初始化数据源（首次运行）
```

### 一键运行

```bash
./daily_run.sh    # 全自动（launchd 每天 11:30 自动调用）
./run.sh          # 交互式执行
```

### 单步运行

```bash
# 采集各数据源
python fetch_wechat_today.py              # 微信公众号（CDP，4个）
python fetch_rss_today.py                 # 微信公众号 RSS + 海外 RSS（11个）
python fetch_hackernews_today.py          # Hacker News
python fetch_arxiv_today.py               # ArXiv 论文
python fetch_github_trending_today.py     # GitHub Trending

# 处理与生成
python scripts/build_bundle.py            # 去重 → 打标签 → bundle
python generate_html.py bundle_today.json # 生成 HTML 预览页
python scripts/generate_mp_article.py bundle_today.json  # 生成公众号稿件
python scripts/publish_to_mp.py           # 提交草稿箱

# 工具
python scripts/seed_sources.py            # 初始化/更新数据源
pytest tests/ -v                          # 全量测试
```

## 数据源

### 微信公众号（9个）

| 采集方式 | 公众号 |
|---------|--------|
| CDP（需登录） | AI寒武纪、36氪、虎嗅APP、硅星人Pro |
| Wechat2RSS 免费 RSS | 量子位、机器之心、新智元 |
| wechatrss.waytomaster.com | APPSO、数字生命卡兹克 |

### 海外源（6个）

Hacker News、ArXiv、GitHub Trending、TechCrunch AI、MIT Technology Review、The Verge AI

## 主链路

```
fetch_wechat_today.py（CDP 4个公众号）  ┐
fetch_rss_today.py（RSS 5个公众号 + 3个海外）│
fetch_hackernews_today.py               ├→ content.db
fetch_arxiv_today.py                    │
fetch_github_trending_today.py          ┘
  → build_bundle.py（去重 → 打标签 → 翻译 → bundle）→ bundle_today.json
  → generate_html.py（today.html）
  → generate_mp_article.py（公众号稿件）
  → publish_to_mp.py（封面图 + 草稿箱）
  → daily_run.sh 步骤13（推 GitHub Pages）
```

## 模块结构

```
collectors/     # 采集器（wechat/rss/hackernews/arxiv/github_trending）
pipeline/       # 内容处理（normalize/dedupe/tagging/bundles）
storage/        # SQLite 数据访问层（db/repository）
publishers/     # 输出（html_preview/mp_article）
scripts/        # 独立脚本（seed/build/generate/publish）
utils/          # 工具（config/log/http/errors）
tests/          # 测试
```

## 数据文件

| 文件 | 说明 |
|------|------|
| `content.db` | SQLite 主数据库（WAL 模式） |
| `bundle_today.json` | 每日 bundle 快照 |
| `today.html` | HTML 预览页 |
| `.env` | 密钥（不进 Git） |
| `config.json` | 本地配置（不进 Git） |

## GitHub Pages

归档页：https://wxyjwxyj.github.io/wechat-articles/

每日 HTML 自动推送到 `main` 分支，`index.html` 是手写门户页，不能覆盖。

## 常见问题

**Q: CDP 采集返回空数据？**

检查：CDP Proxy 是否运行（`curl http://localhost:3456/health`）、浏览器是否登录微信公众平台。

**Q: 如何添加新公众号？**

修改 `scripts/seed_sources.py` 后执行，RSS 源加 `is_wechat: True` 标记。

**Q: 为什么不用 async/await？**

CDP Proxy 的 `/eval` 端点对 Promise 返回值处理不完善，同步 XMLHttpRequest 更可靠。
