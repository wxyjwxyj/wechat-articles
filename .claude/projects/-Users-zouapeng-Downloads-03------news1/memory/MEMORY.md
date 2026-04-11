# 项目经验沉淀

> 状态快照在 CLAUDE.local.md，踩坑经验在各 lessons 文件。

---

## 当前版本：v26

```
v21: daily_run.sh 健壮性改进（stash 保护 + bundle 失败跳过 + 日期校验）
v22: 系统安全与可靠性加固 + code review 体系
     密钥→.env / SQLite WAL / retry session / Claude 429 重试
     DB 索引 / 异常细化 / 配置校验 / 封面图兜底
     test-runner + code-reviewer agents / finish v2
v23: today.html 来源分类修复、海外源中文翻译、全面 XSS 防护
v24: HN采集串行→20并发、RSS并发、多来源分数加成、plist 11:30+17:30双次
v25: 系统高频问题专项修复
     HN url 改为 hn_url（讨论页）/ SQL OR 加括号 / 采集脚本并行化
     items 冲突键 url→content_hash / Claude API 启动探测
v26: 翻译结果持久化到 DB
     items 表加 title_zh/summary_zh / 重跑 build_bundle 跳过已翻译条目
     翻译后回写 DB，build_bundle 从 2 分钟→秒级
```

---

## 架构决策

### 可用模型：只有 claude-opus-4-6（2026-04-11）

**背景：** 本机 API 环境（CodeWhisperer 代理）不支持 haiku 模型，`claude-haiku-4-5` 和 `claude-haiku-4-5-20251001` 均返回 `INVALID_MODEL_ID`。

**决策：** 所有 Claude API 调用统一用 `claude-opus-4-6`，不做 haiku fallback。

**不要：** 在代码里加 haiku 作为首选或 fallback，会直接失败。

### 密钥管理：环境变量优先，config.json 降级（2026-04-11）

**背景：** claude_api_key 明文存在 config.json，虽然 .gitignore 排除了但文件系统可读。

**决策：** `utils/config.py` 统一读取，`ANTHROPIC_API_KEY` 环境变量优先，config.json 降级兜底。`daily_run.sh` 启动时 `source .env`。

**不要：** 把密钥放回 config.json，也不要在代码里直接读 config.json 的 claude_api_key。

### SQLite 并发：WAL + busy_timeout（2026-04-11）

**背景：** daily_run.sh 同时跑 5 个采集脚本写 content.db，偶发 `database is locked`。

**决策：** `storage/db.py` 的 `get_connection()` 统一设置 `journal_mode=WAL` + `busy_timeout=5000` + `timeout=10`。

**不要：** 在各脚本里单独设置 PRAGMA，统一在 get_connection 一处管理。

### 网络请求：统一 retry session（2026-04-11）

**背景：** 采集脚本裸调 requests，网络抖动一次就整个失败。

**决策：** `utils/http.py` 的 `retry_session()` 返回带指数退避的 Session（3 次重试，覆盖 429/5xx）。所有 collector 用 `self._session` 替代 `requests`。

**不要：** 在各脚本里自己写重试逻辑，统一用 retry_session()。

### items 冲突键：content_hash 而非 url（2026-04-11）

**背景：** url 语义变化时（如 HN 从原文链接改为讨论页），旧数据无法被 upsert 覆盖，产生重复记录，bundle 选了旧的。

**决策：** `items` 表冲突键改为 `content_hash unique`，url 改为可更新字段。迁移脚本：`scripts/migrate_items_hash_key.py`。

**不要：** 用 url 做 upsert 冲突键，url 是可变的展示字段。

---

| 文件 | 内容 |
|------|------|
| `lessons_engineering.md` | 工程化配置、hooks、代码质量、密钥管理、SQLite 并发、网络重试 |
| `lessons_data.md` | 数据采集、管道、公众号发布经验 |
| `lessons_frontend.md` | 前端、分支、GitHub Pages 经验 |
| `lessons_research_hub.md` | Research Hub 经验 |
| `project_wechat_lessons.md` | 早期项目历史 |

---

## 会话历史（关键里程碑）

| 日期 | 版本 | 主要工作 |
|------|------|----------|
| 2026-04-04 | v1-v10 | 初始化项目，微信CDP采集、去重打标签、bundle pipeline、HTML生成、公众号稿件生成 |
| 2026-04-05 | v11 | 接入 RSS 数据源（TechCrunch/MIT/The Verge），today.html 来源分组+话题优化 |
| 2026-04-06 | v12-v14 | Topic Research Hub 核心功能（HN/GitHub/ArXiv/Claude评分/文档库/Web Search/DuckDuckGo兜底） |
| 2026-04-06 | v15 | 接入小红书数据源（Research Hub 第7个），公众号本地搜索数据源，微信登录态过期自动重试 |
| 2026-04-07 | v16-v18 | launchd 定时任务调试，daily_run.sh 健壮性改进（stash保护/bundle失败跳过/日期校验） |
| 2026-04-10 | v19-v21 | bundle_items 保序去重修复（UNIQUE约束），微信标签页未打开时自动创建 |
| 2026-04-11 | v22 | 系统安全与可靠性加固（密钥→.env/SQLite WAL/retry session/Claude 429重试/DB索引/封面图兜底） |
| 2026-04-11 | v22+ | code review 体系（test-runner + code-reviewer agents，finish v2），CLAUDE.md 精简重构 |
| 2026-04-11 | v23 | today.html 来源分类修复、海外源中文翻译（claude-opus-4-6 逐条翻译）、全面 XSS 防护 |
| 2026-04-11 | v25 | 系统高频问题专项修复：HN url→hn_url、SQL OR 加括号、采集并行化、items冲突键→content_hash、API启动探测 |

---

## 待观察 / 下一步

- [ ] retry session 对采集成功率的提升效果
- [ ] SQLite WAL 下多进程写入是否还有锁问题
- [ ] Claude API 429 重试是否够用（当前 3 次）
- [ ] 类型提示完善（mypy）
- [ ] 测试覆盖提升

---

## 常用命令

```bash
./daily_run.sh                              # 全自动日报
python fetch_wechat_today.py                # 只跑微信采集
python scripts/build_bundle.py              # 重建 bundle
python generate_html.py bundle_today.json   # 重建 HTML
python -m flask --app api.app run           # Research Hub
pytest tests/ -v                            # 全量测试
```
