# 项目经验沉淀

> 状态快照在 CLAUDE.local.md，踩坑经验在各 lessons 文件。

---

## 当前版本：v29

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
     build_bundle 支持 --date 参数 / 日志中文括号乱码修复
v27: 测试覆盖提升 + bug 修复
     新增 test_repository / test_github_trending / test_config（共 +10 个测试）
     list_items_by_date 用 date() 函数修复时区后缀兼容问题
     schema.sql 补表达式索引 idx_items_created_at_date / published_at_date
     翻译日志区分新翻译和缓存复用数量
v28: 微信公众号采集 CDP→RSS 迁移
     量子位/机器之心/新智元 → Wechat2RSS 免费 RSS
     APPSO/数字生命卡兹克 → wechatrss.waytomaster.com RSS
     CDP 只负责剩余 4 个（AI寒武纪/36氪/虎嗅APP/硅星人Pro）
     normalize_rss_item 支持从 source config 读取 language
     use_original_time=True 用 RSS 原始发布时间（公众号时区无偏差）
     is_wechat=True 标记微信 RSS 源，html_preview 按此分类到公众号行
     build_bundle 严格日期过滤：微信源只保留采集日当天发布的文章
     Research Hub Web 搜索升级：Exa AI 优先 + Claude query 扩展
     topic → 4个中英双语子查询 → 5路并行 Exa → 去重合并（~5x 结果量）
     Claude prompt 用英文，避免中文 prompt 被代理拦截返回"I can't discuss that"
v29: cckeys.top 代理拦截问题全面修复
     所有 Claude API prompt 指令部分改为英文（翻译/去重/打标签/点评/评分/query扩展）
     "You are..." 角色扮演句式也会被拦截，改为直接描述任务
     去重 JSON 解析改为取最后一个对象（处理 Claude 自我纠正场景）
     去重 prompt 加正反示例，区分"同一事件"和"仅共享关键词"
     Research Hub 评分缓存（research_score_cache 表，url+topic 为 key）
     采集端初筛（_prefilter）减少 Claude token 消耗
     新增测试：dedupe 误合并防护、Claude 自我纠正场景
     publish_to_mp 新增 --force 参数跳过已有同日草稿检查
v30: Research Hub 深度研究功能
     新增 /research/deep SSE 接口，流式输出横纵分析报告
     result_renderer.py 新增深度研究按钮和流式展示区
     全面修复渲染层 XSS：_html.escape 所有外部字段、_safe_url 过滤 javascript: 协议
     JS 嵌入 topic 用 json.dumps().replace("</", "<\\/") 防 </script> 注入
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

### Python f-string 里嵌 JS 代码的转义陷阱（2026-04-14）

**背景：** `result_renderer.py` 用 f-string 生成含 `<script>` 块的 HTML，JS 正则里的 `\n` 在 Python f-string 里是真实换行，导致 JS 语法错误；`\*` 是无效 Python 转义序列。

**决策：**
- JS 正则中的 `\n` 写成 `\\n`（Python 转义后输出字面量 `\n`）
- `join('\n')` 写成 `join('\\n')`
- `\*\*` 写成 `[*][*]`（避免无效转义）
- 用户输入嵌入 JS 字符串：`json.dumps(value).replace("</", "<\\/")` 防 `</script>` 注入

**不要：** 在 f-string 里直接写 JS 正则的 `\n`、`\*` 等转义序列，会被 Python 先解释。

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

### cckeys.top 代理拦截规律（2026-04-13）

**背景：** 代理会拦截特定 prompt 模式，返回 "I'm Kiro" 或 "I can't discuss that"，导致翻译/去重/点评全部失败。

**规律：**
- 中文指令性 prompt → 拦截
- `"You are [角色]..."` 角色扮演句式 → 拦截
- 英文直接描述任务（"Translate...", "Write...", "Score..."）→ 正常
- 输出内容可以是中文，只要指令框架是英文

**排查方法：** 加 `logger.info("原始响应: %s", raw[:300])` 看实际返回。

**不要：** 用中文写 prompt 指令，也不要用 "You are..." 开头。

### 手动跑脚本读不到 API key（2026-04-13）

**背景：** 项目用 `.env` 存密钥，`daily_run.sh` 里 `source .env` 后跑脚本没问题。但直接 `python scripts/xxx.py` 时读不到 `ANTHROPIC_API_KEY`，出现"未配置 claude_api_key"。

**原因：** 项目代码里没有 `load_dotenv()`，完全依赖 shell 的 `source .env` 注入环境变量。

**手动跑的正确姿势：**
```bash
set -a && source .env && set +a && python scripts/xxx.py
```

**不要：** 直接 `python scripts/xxx.py`，也不要用 `python -c "from dotenv import load_dotenv; load_dotenv(); ..."` 绕过（容易忘）。如果频繁手动跑，考虑在 `utils/config.py` 的 `get_claude_config()` 里加 `load_dotenv()`。

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
| 2026-04-12 | v27 | 测试覆盖提升（+10 tests）、list_items_by_date 时区 bug 修复、翻译日志改进 |
| 2026-04-12 | v28 | 微信公众号采集 CDP→RSS 迁移；is_wechat 标记 + 严格日期过滤；Research Hub Exa + Claude query 扩展 |
| 2026-04-13 | v29 | cckeys.top 代理拦截全面修复（所有 prompt 改英文，去掉 You are 句式）；去重取最后 JSON + 正反示例；评分缓存；采集端初筛；量子位/机器之心/新智元 改回 CDP；publish_to_mp 新增 --force 参数 |

---

## 待观察 / 下一步

- [ ] retry session 对采集成功率的提升效果
- [ ] SQLite WAL 下多进程写入是否还有锁问题
- [ ] Claude API 429 重试是否够用（当前 3 次）
- [ ] 类型提示完善（mypy）

---

## 常用命令

```bash
./daily_run.sh                              # 全自动日报
python fetch_wechat_today.py                # 只跑微信采集
python scripts/build_bundle.py              # 重建 bundle
python generate_html.py bundle_today.json   # 重建 HTML
python scripts/publish_to_mp.py --force     # 强制重新提交草稿（忽略已有同日草稿）
pytest tests/ -v                            # 全量测试
```
