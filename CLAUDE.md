# 微信公众号文章监控项目

## 项目概述

自动获取指定微信公众号的最新文章，生成 HTML 汇总页面。  
第一阶段已升级为"采集入库 → 内容处理 → API 输出 → 小程序可读 → 公众号发布稿生成"闭环系统。

## 工作区约定

- 实施类任务默认使用 git worktree 隔离执行
- worktree 目录固定使用项目根目录下的 `.worktrees/`

## 分支管理

- **`main`**：放 GitHub Pages 展示的页面文件，推 GitHub
  - 地址：https://wxyjwxyj.github.io/wechat-articles/
  - **`index.html`**：门户导航页（三栏：导读/完整版/归档），不要用 generate_html.py 覆盖！
  - **`today.html`**：今日完整版（由 generate_html.py 生成）
  - **`mp_article_preview.html`**：今日导读精选点评
  - **`archive/`**：历史归档页面
- **`dev`**：所有代码改动提交到这里，只本地保存，不推 GitHub

### ⚠️ 推送 GitHub Pages 的正确流程

**关键：index.html 是手写的门户页，不能用脚本覆盖！**

```bash
# 1. 改代码 → 在 dev 提交
git checkout dev
git add <文件>
git commit -m "..."

# 2. 切 main → 用 dev 代码生成子页面（不碰 index.html）
git checkout main

# 从 dev 临时拉生成代码
git checkout dev -- publishers/html_preview.py generate_html.py

# 生成 today.html（注意输出到 today.html，不是 index.html！）
python generate_html.py bundle_today.json today.html

# 还原临时拉取的代码
git checkout -- publishers/html_preview.py generate_html.py

# 提交并推送（只 add 页面文件）
git add today.html mp_article_preview.html
git commit -m "Update: $(date +%Y-%m-%d)"
git push

# 3. 切回 dev
git checkout dev
```

## 监控的公众号

- 量子位 (MzIzNjc1NzUzMw==)
- AI寒武纪 (Mzg3MTkxMjYzOA==)
- 机器之心 (MzA3MzI4MjgzMw==)
- 数字生命卡兹克 (MzIyMzA5NjEyMA==)
- APPSO (MjM5MjAyNDUyMA==)

---

## 项目架构（第一阶段）

### 主链路

```
sources 表
  → fetch_wechat_today.py（采集）
  → items 表
  → build_bundle.py（标准化 → 去重 → 标签 → bundle 生成）
  → bundles 表 + bundle_today.json
  → generate_html.py / generate_mp_article.py（输出）
```

### 关键约定

- `fetch_wechat_today.py` 是 **collector 入口**，不是最终产物，结果写入 `content.db`
- **主数据源是 `content.db`（SQLite）**，不是 JSON 文件
- `bundle_today.json` 是 HTML 与公众号稿件的**共同输入**，由 `build_bundle.py` 生成

### 模块职责

| 模块 | 职责 | 边界 |
|------|------|------|
| `collectors/` | 从外部拿数据，写入 `items` 表 | 不写 bundle |
| `pipeline/` | 标准化、去重、打标签、bundle 生成 | 不负责 API 或页面 |
| `publishers/` | 消费 bundle 数据，生成 HTML / 公众号稿 | 不直接读原始抓取结果 |
| `api/` | 只读接口，供小程序或调试使用 | 不承担采集或生成逻辑 |
| `storage/` | SQLite 数据库访问层 | 统一的数据访问入口 |
| `scripts/` | 独立执行脚本（seed、build、generate） | 编排各模块 |

---

## 推荐入口

### 一键执行（推荐）

```bash
./run.sh
```

流程：检查环境 → 初始化 sources → 采集文章 → 生成 bundle → 生成 HTML → 生成公众号稿 → 提交草稿箱 → 推送 GitHub Pages

### API 启动

```bash
python -m flask --app api.app run --debug
```

---

## 核心脚本说明

### ✅ 推荐使用

**`fetch_wechat_today.py`** - 采集今天的文章并入库
- 使用 CDP Proxy + 同步 XMLHttpRequest
- 只返回今天发布的文章，结果写入 `content.db`
- 复用已打开的浏览器标签页
- **最稳定可靠的采集方案**

**`scripts/seed_sources.py`** - 初始化公众号 sources 表

**`scripts/build_bundle.py`** - 生成每日 bundle（标准化 → 去重 → 打标签 → 写库 + 输出 JSON）

**`generate_html.py`** - 消费 `bundle_today.json` 生成 HTML 预览页

**`scripts/generate_mp_article.py`** - 消费 `bundle_today.json` 生成公众号发布稿

**`scripts/publish_to_mp.py`** - 将公众号稿件提交到草稿箱
- 读取 `mp_article_preview.json`，通过 CDP Proxy 调用公众号后台接口创建草稿
- 自动检查是否已有同日草稿（防重复）
- 支持 `--dry-run` 模式
- **只提交到草稿箱，不自动发布**，需人工确认后点"发布"

### ⚠️ 已废弃

以下脚本**不要使用**：

- `fetch_all_wechat.py` - 使用搜狗微信搜索（反爬严重，数据不准）
- `fetch_wechat.py` - 早期测试脚本
- `fetch_wechat_articles.py` - 早期测试脚本
- `fetch_wechat_browser.py` - 使用搜狗搜索（已废弃）
- `wechat_playwright.py` - Playwright 方案（不稳定）
- `test_playwright.py` - 测试脚本
- `wechat_api.py` - 直接调用 API（缺少认证）
- `wechat_monitor.py` - 早期监控脚本

### 📝 参考

- `fetch_wechat_cdp.py` - CDP 方案的早期版本（async 有问题，已被 fetch_wechat_today.py 替代）

---

## 技术方案

### 为什么不用搜狗微信搜索？

❌ **搜狗微信搜索的问题：**
- 反爬机制严重
- 返回空结果或被拦截
- 数据不准确
- 需要处理验证码

### ✅ 正确方案：CDP Proxy + 微信公众平台 API

**原理：**
1. 启动 CDP Proxy 连接用户的 Chrome 浏览器
2. 在浏览器中打开微信公众平台 (mp.weixin.qq.com)
3. 利用浏览器的完整登录态执行 fetch 调用官方 API
4. 自动处理所有认证和 CSRF token

**关键技术细节：**
- 使用**同步 XMLHttpRequest** 而非 async fetch（CDP 的 /eval 端点对 Promise 处理有 bug）
- 复用已打开的标签页而非每次创建新标签页（提高效率和稳定性）

---

## 快速开始

### 一键执行（推荐）

```bash
./run.sh
```

这个脚本会自动：
1. 检查 CDP Proxy 状态
2. 检查浏览器登录状态
3. 初始化 sources
4. 获取今日文章（写入 content.db）
5. 生成每日 bundle
6. 生成 HTML 页面
7. 生成公众号发布稿
8. 询问是否提交到 Git

### 手动执行

```bash
# 1. 初始化 sources（首次运行或新增公众号时）
python scripts/seed_sources.py

# 2. 获取今天的文章
python fetch_wechat_today.py

# 3. 生成每日 bundle
python scripts/build_bundle.py

# 4. 生成 HTML 页面
python generate_html.py bundle_today.json

# 5. 生成公众号发布稿
python scripts/generate_mp_article.py bundle_today.json

# 6. 启动 API（可选）
python -m flask --app api.app run --debug

# 7. 提交到 Git（可选）
git add index.html bundle_today.json
git commit -m "Update: $(date +%Y-%m-%d) articles"
git push
```

---

## 项目文件说明

### 核心脚本

- `fetch_wechat_today.py` - 采集今日文章（collector 入口）
- `generate_html.py` - 生成 HTML 预览页
- `run.sh` - 一键执行脚本
- `scripts/seed_sources.py` - 初始化 sources 表
- `scripts/build_bundle.py` - 生成每日 bundle
- `scripts/generate_mp_article.py` - 生成公众号发布稿

### 配置文件

- `config.json` - 微信配置（**不提交 git**）
- `config.example.json` - 配置模板
- `CLAUDE.md` - 项目文档（本文件）

### 数据文件

- `content.db` - SQLite 主数据库（唯一数据源）
- `bundle_today.json` - 每日 bundle 快照（HTML 与公众号稿的共同输入）
- `index.html` - 生成的 HTML 预览页
- `mp_article_preview.json` - 公众号发布稿预览

### 废弃文件（不要使用）

- `fetch_all_wechat.py` - 使用搜狗搜索（已废弃）
- `fetch_wechat_cdp.py` - 早期 CDP 版本（已被 fetch_wechat_today.py 替代）
- 其他 `fetch_*.py` 和 `wechat_*.py` - 早期测试脚本

---

## 数据格式

### bundle_today.json 格式

```json
{
  "date": "2026-04-04",
  "items": [
    {
      "id": 1,
      "source_name": "量子位",
      "title": "文章标题",
      "url": "https://mp.weixin.qq.com/s/xxxxx",
      "summary": "文章摘要",
      "published_at": "2026-04-04 09:30:05",
      "tags": ["AI", "大模型"]
    }
  ]
}
```

### 注意事项

- **不包含**：阅读量、评论数（需要访问文章详情页才能获取）
- **时间戳**：`update_time` 字段是发布时间的 Unix 时间戳

---

## 常见问题

### Q: 为什么返回空数据？

A: 检查以下几点：
1. CDP Proxy 是否正常运行
2. 浏览器是否已登录微信公众平台
3. token 是否过期（从浏览器 URL 中重新获取）
4. 标签页 ID 是否正确（可以通过 `curl http://localhost:3456/targets` 查看）

### Q: 为什么不用 async/await？

A: CDP Proxy 的 `/eval` 端点对 Promise 返回值处理不完善，异步代码会返回空对象 `{}`。使用同步的 XMLHttpRequest 更可靠。

### Q: 如何添加新的公众号？

A: 在 `scripts/seed_sources.py` 中添加公众号信息后重新执行，数据会写入 `content.db` 的 `sources` 表。

## 项目历史

详见 `.claude/projects/-Users-zouapeng-Downloads-03------news1/memory/project_wechat_lessons.md`

记录了所有踩过的坑和最终解决方案。
