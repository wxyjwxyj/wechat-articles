# 微信公众号文章监控项目 — 经验与教训

> 记录从 2026-04-04 开始的所有踩坑和最终方案，供后续 session 参考。

---

## 一、数据采集

### ❌ 搜狗微信搜索方案（已废弃）
- **问题**：反爬严重，频繁返回空结果或验证码，数据时效性差
- **教训**：第三方搜索引擎做微信采集不可靠，不要在这个方向上花时间

### ❌ Playwright 方案（已废弃）
- **问题**：不稳定，难以处理微信公众平台的登录态
- **教训**：自动化浏览器方案看似万能，但对登录态管理复杂的站点反而不如更轻量的方案

### ❌ async/await + CDP（已废弃）
- **问题**：CDP Proxy 的 `/eval` 端点对 Promise 返回值处理有 bug，异步代码返回空对象 `{}`
- **教训**：遇到中间层代理时，不要假设所有 JS 特性都能正常工作，先用最简单的方式验证

### ✅ 最终方案：同步 XMLHttpRequest + CDP Proxy
- 利用用户已登录的 Chrome 浏览器的 session
- 通过 CDP Proxy 注入同步 XMLHttpRequest 调用微信公众平台 API
- 复用已打开的标签页而非创建新标签页（更高效、更稳定）
- **关键**：同步 XHR 虽然"落后"，但在 CDP 场景下是最可靠的

---

## 二、数据管道架构

### 教训：先定数据流再写代码
- 早期直接从采集脚本输出 JSON 文件，导致格式不统一、重复数据难处理
- **最终架构**：`采集 → SQLite(items表) → 标准化/去重/打标签 → bundle → 输出`
- SQLite 作为单一数据源（single source of truth）是正确决策

### 教训：去重需要多级策略
- 简单 URL 去重不够 — 同一篇文章可能有不同的短链
- 最终实现：URL 精确匹配 + 标题相似度 + Claude 智能去重（三级）
- Claude 去重虽然成本高但效果最好，适合日均 20 条的量级

### 教训：bundle 是衔接采集和输出的关键抽象
- `bundle_today.json` 作为"每日快照"，解耦了采集逻辑和输出逻辑
- HTML 生成和公众号稿件生成共用同一个 bundle 输入，保证一致性

---

## 三、前端页面

### 教训：单页面 index.html 会越来越臃肿
- 最初所有内容都往 index.html 塞（文章列表、筛选、归档入口）
- 功能多了之后维护困难，每次生成都覆盖整个文件

### ✅ 最终方案：拆分为门户 + 内容页
- `index.html` — 静态导航门户（手工维护，报纸封面风格）
- `today.html` — 每日完整文章列表（脚本自动生成）
- `archive/digest_YYYY-MM-DD.html` — 每日导读存档
- **好处**：index.html 不再被脚本覆盖，可以独立设计；内容页专注内容

### ✅ 导读页（mp_article_preview.html）
- 由 `scripts/generate_mp_html.py` 生成，精选当日重要文章 + 编辑点评
- 风格偏向简洁卡片式，适合快速浏览
- 与 today.html（完整版）形成互补

### 教训：手机端适配不能忽视
- 表格布局在手机上溢出严重 → 改为卡片式布局
- 标签栏过长 → 加了折叠按钮
- **方案**：用 CSS media query 在窄屏时切换布局，而非 JS 动态判断

### 教训：GitHub Pages 部署注意事项
- main 分支用于 GitHub Pages，只放前端产物
- 所有代码改动在 dev 分支
- 推送时要记得带上所有需要展示的 HTML 文件（index.html + today.html + mp_article_preview.html）
- **index.html 是手写的导航门户页，绝对不能被脚本覆盖！**

---

## 四、分支管理

### ✅ 双分支策略有效
- `main` — 只放 GitHub Pages 的前端文件，推远端
- `dev` — 所有开发改动，只在本地
- 合并方式：`git checkout main && git checkout dev -- <文件>` 按需拉取

### 教训：dev → main 合并要选择性
- 不要 `git merge dev`，因为 dev 有很多 main 不需要的文件（Python 脚本、配置等）
- 用 `git checkout dev -- <文件>` 精准拉取需要的前端文件

---

## 五、自动化脚本

### ✅ daily_run.sh 是正确抽象
- 无交互全自动：检查环境 → 采集 → bundle → HTML → 导读页 → 归档 → 推送 GitHub Pages
- 包含 dev → main 分支切换和推送逻辑
- 但要注意：脚本里的路径假设和分支操作要与实际工作流一致

### ✅ launchd 定时任务已配置
- plist 路径：`~/Library/LaunchAgents/com.news1.daily.plist`
- 每天 **9:57** 自动执行 `daily_run.sh`
- PATH 包含 miniconda3，日志输出到 `.claude/daily_run.log`
- 前提：电脑开机 + Chrome 已打开微信公众平台标签页 + CDP Proxy 运行中

### 教训：脚本要幂等
- 同一天多次运行不应产生重复数据
- 采集脚本用日期过滤 + 数据库去重保证幂等性

---

## 六、AI 集成

### ✅ Claude 的合适用途
- **去重判断**：标题相似但不完全相同的文章，Claude 判断准确率很高
- **内容摘要/点评**：为每篇文章生成编辑点评，质量稳定
- **重要性打分**：基于标题和摘要给文章打分排序

### 教训：AI 调用要有成本意识
- 每次 build_bundle 都调用 Claude 做去重和打分，日均成本可控（20 条左右）
- 但如果量级增大需要考虑缓存或批量处理

---

## 七、公众号草稿箱自动提交

### ✅ 通过 CDP 调用公众号后台内部接口
- 复用采集文章的同一套技术方案（CDP Proxy + 浏览器登录态 + 同步 XHR）
- 接口：`POST /cgi-bin/operate_appmsg?t=ajax-response&sub=create&type=77`
- 以 FormData 提交：title0, content0, digest0, author0, count=1 等
- 不需要官方 API 认证，直接利用浏览器 session

### 教训：type=77 是草稿箱
- `type=10` 是旧版素材管理，`type=77` 对应 2021 年后的草稿箱+发布体系
- 创建返回 `appMsgId`，删除时用 `sub=del` + `AppMsgId`

### 安全策略
- **只提交到草稿箱，不自动发布**（发布需要人工确认）
- 提交前检查是否已有同日草稿（按标题日期判断），防止重复
- 失败时优雅降级，不影响其他流程

### 相关文件
- `publishers/mp_publisher.py` — MpPublisher 类（create_draft / list_drafts / delete_draft）
- `scripts/publish_to_mp.py` — 命令行入口（支持 --dry-run）
- `daily_run.sh` 步骤 11 自动调用

---

## 八、项目演进总结

```
v0: 搜狗搜索 → 失败
v1: Playwright → 不稳定
v2: CDP async → 返回空对象
v3: CDP 同步 XHR → ✅ 稳定
v4: 加入 SQLite + pipeline 架构 → 数据可靠
v5: 加入 Claude 去重/打分/点评 → 内容质量提升
v6: 前端拆分为门户+内容页+导读页 → 架构清晰
v7: 手机端适配（表格→卡片 + 标签栏折叠） → 体验完善
v8: 公众号草稿箱自动提交（CDP 内部接口） → 发布半自动化
v9: 封面图自动生成+上传+草稿一体化 → 完整发布链路
v10: Claude Code 工程化（hooks/rules/skills/memory/tests） → 开发体验提升
v11: 统一 logging 替代全项目 print() → 日志可控
v12: 统一错误处理体系（自定义异常 + exit code） → 故障定位效率提升
v13: pyproject.toml 依赖管理 → 项目规范化
v14: 接入 ArXiv + GitHub Trending 数据源 → 4源覆盖（微信/HN/ArXiv/GitHub）
v15: 导读精选多样性保底 + 打标签分批处理 → 内容多样性 + 稳定性提升
v16: 修复 daily_run.sh 推 GitHub Pages 拉旧 HTML 的 bug
v17: RSS 接入（TechCrunch/MIT/The Verge），feedparser 通用采集器
v18: 精选 8条→6条，ArXiv 去保底，内容负担降低
```

每一步失败都直接指向了更好的方案。不要怕推翻重来，但要记录为什么失败。

---

## 九、封面图自动生成与上传

### ✅ 封面图生成（Pillow）
- 尺寸 900×383（微信公众号推荐比例 2.35:1）
- 深蓝渐变底色 + 红色装饰条 + 日期文字
- 文件：`publishers/cover_generator.py`，输出 `cover_today.png`

### ✅ 封面图上传流程
- 通过 CDP 调用 `filetransfer` 接口上传图片到公众号素材库
- 返回 `fileid`（如 100000016），作为 `create_draft` 的 `fileid` 参数
- 上传前需将图片转为 base64
- 文件：`publishers/mp_publisher.py` 中的 `upload_cover_image()` 方法

### 教训：草稿创建带封面
- `create_draft` 的 FormData 中 `fileid0=<封面fileid>` 即可绑定封面
- 不设置 fileid 草稿也能创建，但在公众号后台显示无封面

---

## 十、Claude Code 工程化配置

### ✅ hooks 安全护栏
- `PreToolUse`: protect-files.sh（保护 .env/config.json/content.db 等敏感文件）
- `PreToolUse`: block-dangerous.sh（拦截 rm -rf /、git push --force main 等危险命令）
- `PostToolUse`: check-garbled.sh（编辑后自动检查 UTF-8 乱码 U+FFFD）
- `Notification`: macOS 原生通知（osascript）

### ✅ rules 自动加载
- `.claude/rules/code-style.md` — Python 代码规范（paths: *.py）
- `.claude/rules/git.md` — 提交和分支规范
- `.claude/rules/deprecated.md` — 废弃文件清单

### ✅ finish skill 收尾流程
- 4 步流程：乱码检查 → 改动说明（等用户）→ 更新记忆 → 提交
- 改动说明是唯一等用户确认的点，之后全自动
- 详见 `.claude/skills/finish/SKILL.md`

### ✅ 测试维护
- 14 个测试全部通过（pytest tests/ -v）
- 测试覆盖：schema、normalize、dedupe、tagging、bundles、mp_article、api
- 测试数据要跟着代码结构变化同步更新（如 sources → items_flat）

---

## 十一、daily_run.sh 完整 16 步流程

```
1. 检查 CDP Proxy
2. 检查浏览器登录态
3. 初始化 sources
4. 采集文章（写入 content.db）
5. 生成 bundle（标准化 → 去重 → 打标签 → 写库 + JSON）
6. 生成 today.html
7. 生成公众号发布稿 HTML
8. 生成封面图
9. 生成导读页 mp_article_preview.html
10. 归档到 archive/
11. 提交到 dev 分支
12. 发布到公众号草稿箱
13. 推送 GitHub Pages（dev→main 选择性拉取→推送→切回 dev）
14. macOS 通知（成功/失败/无内容）
15. 输出统计摘要
16. 日志轮转（30 天自动清理）
```

日志路径：`.claude/logs/YYYY-MM-DD.log`

---

## 十二、后台研究任务（2026-04-05 启动）

睡前启动了 5 个后台研究任务，结果存放在 `.claude/research/` 目录：

1. `01_ai_newsletter_landscape.md` — AI Newsletter 行业全景、赚钱模式、成功案例
2. `02_wechat_mp_automation.md` — 公众号自动化最佳实践、增长策略、变现路径
3. `03_monetization_deep_dive.md` — 独立开发者变现策略、项目可行方向
4. `04_project_improvements.md` — 项目代码审查、架构改进、测试覆盖分析
5. `05_ai_curation_tools.md` — AI 内容策展工具对比、技术方案、开源项目

下次 session 先检查这些文件是否已生成，然后基于研究结果讨论下一步方向。

---

## 十三、代码质量优化记录（2026-04-05）

基于 `04_project_improvements.md` 的审查建议，完成了以下优化：

### ✅ 已完成

| 项目 | 优先级 | commit | 说明 |
|------|--------|--------|------|
| AI 内容标注合规 | P0 | `770433f` | 文章末尾添加 AI 辅助生成标注 |
| 统一 logging | P1→P0 | `583bd29` | utils/log.py + 全项目 print→logger |
| 错误处理统一 | P0 | `76da0d7` | utils/errors.py 异常层级 + exit code 映射 |
| 采集失败通知增强 | P0 | `76da0d7` | daily_run.sh 捕获各步 exit code 通知具体原因 |
| pyproject.toml | P2 | `ec3bc0f` | 依赖声明 + pytest/mypy 配置 |
| LLM 编辑点评增强 | P2 | `529f8c8` | 有态度的 prompt + Haiku 优先降本 |
| 公众号排版升级 | P2 | `813aea5` | 科技杂志风格 |
| 接入 Hacker News | 中期 | `64df390` | 海外 AI 数据源 |

### 📋 待做

| 项目 | 优先级 | 工作量 |
|------|--------|--------|
| 配置文件统一（dataclass） | P1 | 3-4h |
| 类型提示完善（TypedDict + mypy） | P1 | 3-4h |
| 测试覆盖提升 | P1 | 4-6h |

### 教训：错误处理要成体系

- 异常层级要和业务域对齐（采集/管道/发布 各有自己的异常类）
- exit code 要有意义，shell 脚本靠 exit code 区分失败原因
- 入口脚本统一 try/except 模式：`News1Error → sys.exit(e.exit_code)`
- 废弃文件及时清理，之前已清完，这次确认没有遗留

---

## 十四、多数据源接入 + bug 修复记录（2026-04-05 下午）

### ✅ 新增数据源

| 源 | commit | 说明 |
|---|---|---|
| ArXiv | `cb37a64` | collectors/arxiv.py + fetch_arxiv_today.py，days_back=3 |
| GitHub Trending | `9b204c6` | collectors/github_trending.py + fetch_github_trending_today.py，HTMLParser 解析 |

现在数据源阵容：**微信9个 + HN + ArXiv + GitHub Trending = 4类12个源**

### ✅ Bug 修复汇总

| bug | commit | 教训 |
|---|---|---|
| fetch_wechat_today 遍历所有 source（含非微信） | `f3e258b` | list_sources() 要加 type 过滤 |
| mp_article 模型名格式错误（claude-haiku-4-20250414） | `d78018e` | 中转服务只识别 `claude-haiku-4-6` 格式 |
| 打标签44篇一次送 Claude → JSON 解析失败 | `8689c16` | 超过15篇必须分批，BATCH_SIZE=15 |
| 导读精选保底条目强制排前面，不按分数 | `391870f` | 保底只保证入选，排序统一按 score 降序 |
| items_flat 缺 source_type 字段 | `647ef16` | build_bundle 输出要包含所有下游用到的字段 |
| daily_run.sh 推 GitHub Pages 拉到旧 HTML | `95e688f` | 关键教训见下方 |

### ⚠️ 关键教训：daily_run.sh 推 GitHub Pages 的正确流程

**错误流程（之前）**：
```
生成 HTML → 切 main → git checkout dev -- today.html → 推送
```
这里 `git checkout dev -- today.html` 拉的是 dev 分支**已提交**的版本，不是刚生成的文件。

**正确流程（现在）**：
```
生成 HTML → 在 dev 提交 HTML → 切 main → git checkout dev -- today.html → 推送
```
步骤12.5：`git add today.html mp_article_preview.html archive/ && git commit` 必须在切换分支前执行。

### ✅ 导读精选多样性保底逻辑

精选8条 = **非微信源各保底1条**（HN/ArXiv/GitHub，共3条）+ **高分条目补齐**（score≥6）
- 所有候选条目**统一按 score 降序排列**，保底不强制排前面
- 保底条目放在 candidates 列表里一起排序，自然竞争位置

### ✅ 打标签分批处理

- 文章超过 ~20 篇时，Claude 返回的 JSON 容易因长度超限而解析失败
- 改为每批 BATCH_SIZE=15 篇，单批失败降级为关键词匹配，不影响其他批次
- 分批时 id 用全局编号（`id_offset + i + 1`），解析时转换回批内下标

### ArXiv 使用注意

- ArXiv 周末不发论文，days_back 设为3天才能在周末抓到周五的论文
- 默认 max_results=50 作为候选池，按关键词相关度 + 分类 + 会议接收情况打分，取前10篇

### GitHub Trending 使用注意

- 未登录状态约返回25个仓库（有时更少，周末约8个）
- 用标准库 HTMLParser 解析，无需 BeautifulSoup
- 页面结构：每个仓库是 `<article>`，今日 star 数在文本 "343 stars today" 中用 regex 提取

---

## 十五、RSS 接入记录（2026-04-05）

### ✅ 新增数据源

| 源 | commit | 说明 |
|---|---|---|
| TechCrunch AI | `b6a8f50` | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| MIT Technology Review | `b6a8f50` | `https://www.technologyreview.com/feed/` |
| The Verge AI | `b6a8f50` + `911c8b8` | 全站 RSS + 关键词过滤 |

技术栈：`feedparser`（标准 RSS/Atom 解析库），通用 `RssCollector` 类复用，无需针对每个站点单独处理格式。

现在数据源阵容：**微信9个 + HN + ArXiv + GitHub Trending + RSS×3 = 5类15个源**

### ⚠️ 教训1：分类专属 RSS URL 不一定可靠

- The Verge 的 AI 分类 feed（`/ai-artificial-intelligence/rss/index.xml`）返回不规范 XML，feedparser 报 `not well-formed`
- **正确做法**：用全站 RSS（`/rss/index.xml`），再靠 AI 关键词过滤，效果一样且格式规范
- 适用于其他站点：优先用全站或主频道 RSS，用关键词过滤代替依赖分类 URL

### ⚠️ 教训2：RSS published_at 时区差导致 build_bundle 日期过滤漏掉

- RSS 文章实际发布时间是美国时间（如4月4日下午），存入 DB 后 `published_at` = `2026-04-04T16:32:22+00:00`
- `build_bundle` 按今天（北京时间4月5日）过滤，导致所有 RSS 文章被漏掉（bundle 里 0 条）
- **正确做法**：`normalize_rss_item` 用 `datetime.now(timezone.utc)` 作为 `published_at`（与 GitHub Trending 保持一致）
- 原始发布时间保留在 `raw_content["published"]` 中备查
- commit: `5d50f1f`

### 精选策略调整（同步更新）

- 精选从 8 条 → **6 条**（降低读者负担）
- 保底范围：HN + GitHub Trending 各1条（ArXiv 去掉保底，靠分数自然竞争）
- commit: `db165ff`
