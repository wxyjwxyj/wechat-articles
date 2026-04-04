# 微信内容中台 — 第一阶段

把微信公众号文章采集升级为"采集入库 → 内容处理 → API 输出 → 小程序可读 → 公众号发布稿生成"的闭环系统。

## 快速开始

### 环境要求

- Python 3.11+
- Chrome 浏览器（需登录微信公众平台）
- CDP Proxy（本地运行于 localhost:3456）

### 安装依赖

```bash
pip install requests flask pytest
```

### 配置

复制 `config.example.json` 为 `config.json` 并填入：

```json
{
  "cdp_proxy": "http://localhost:3456",
  "token": "你的微信公众平台 token"
}
```

### 一键运行

```bash
bash run.sh
```

### 单步运行

```bash
# 初始化 sources（首次运行或新增公众号时）
python scripts/seed_sources.py

# 抓取今日微信文章并入库
python fetch_wechat_today.py

# 生成每日 bundle（标准化 → 去重 → 标签 → bundle）
python scripts/build_bundle.py

# 生成 HTML 预览页
python generate_html.py bundle_today.json

# 生成公众号发布稿
python scripts/generate_mp_article.py bundle_today.json

# 启动本地 API（供小程序或调试使用）
python -m flask --app api.app run --debug
```

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `config.json` | 微信配置（token 等），**不提交 git** |
| `content.db` | SQLite 主数据库，所有内容的唯一数据源 |
| `bundle_today.json` | 每日 bundle 快照，HTML 和公众号稿件的共同输入 |
| `index.html` | 生成的 HTML 预览页 |
| `mp_article_preview.json` | 公众号发布稿预览，人工确认后发布 |

## 本地 API

启动：`python -m flask --app api.app run --debug`

| 路由 | 说明 |
|------|------|
| `GET /api/bundles/today` | 今日 bundle |
| `GET /api/bundles/<date>` | 指定日期 bundle（格式：YYYY-MM-DD）|
| `GET /api/sources` | 所有来源列表 |
| `GET /api/sources/<name>/items` | 指定来源今日文章 |

## 模块结构

```
collectors/     # 内容采集器（微信公众号等）
pipeline/       # 内容处理（标准化、去重、标签、bundle 生成）
storage/        # SQLite 数据库访问层
publishers/     # 内容输出（HTML 预览、公众号发布稿）
api/            # Flask 只读 API
scripts/        # 独立脚本（seed sources、build bundle、生成稿件）
tests/          # 测试
```

## 运行测试

```bash
pytest
```

## 常见问题

**Q: 为什么返回空数据？**

A: 检查以下几点：
1. CDP Proxy 是否正常运行（`curl http://localhost:3456/health`）
2. 浏览器是否已登录微信公众平台
3. token 是否过期（从浏览器 URL 中重新获取）

**Q: 为什么不用 async/await？**

A: CDP Proxy 的 `/eval` 端点对 Promise 返回值处理不完善，异步代码会返回空对象 `{}`。使用同步的 XMLHttpRequest 更可靠。

**Q: 如何添加新的公众号？**

A: 在 `content.db` 的 `sources` 表中新增记录，或修改 `scripts/seed_sources.py` 后重新执行。
