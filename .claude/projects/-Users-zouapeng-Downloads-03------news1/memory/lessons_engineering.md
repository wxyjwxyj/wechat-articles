# Claude Code 工程化 & 代码质量 — 经验教训

---

## 一、Claude Code 工程化配置

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
- 4 步：乱码检查 → 改动说明（等用户确认）→ 更新记忆 → 提交
- 详见 `.claude/skills/finish/SKILL.md`

### ✅ memory 文件分工
- `MEMORY.md` — 当前状态快照（版本、系统状态、近期改动、待做）
- `lessons_data.md` — 数据采集/管道/公众号经验
- `lessons_frontend.md` — 前端/分支/自动化经验
- `lessons_engineering.md` — 工程化/代码质量经验（本文件）
- `lessons_research_hub.md` — Research Hub 经验

### ✅ 测试维护
- 54 个测试全部通过（pytest tests/ -v）
- 测试覆盖：schema、normalize、dedupe、tagging、bundles、mp_article、api、rss、hackernews、arxiv、research hub
- 测试数据要跟着代码结构变化同步更新（如 sources → items_flat）
- **RSS 测试日期要用动态时间**，硬编码日期会被 days_back 过滤掉
- **web_search 测试**：加了 DuckDuckGo fallback 后无 key 不再抛异常，测试要跟着改

---

## 二、代码质量优化记录（2026-04-05）

### ✅ 已完成优化

| 项目 | 优先级 | commit | 说明 |
|------|--------|--------|------|
| AI 内容标注合规 | P0 | `770433f` | 文章末尾添加 AI 辅助生成标注 |
| 统一 logging | P1→P0 | `583bd29` | utils/log.py + 全项目 print→logger |
| 错误处理统一 | P0 | `76da0d7` | utils/errors.py 异常层级 + exit code 映射 |
| 采集失败通知增强 | P0 | `76da0d7` | daily_run.sh 捕获各步 exit code 通知原因 |
| pyproject.toml | P2 | `ec3bc0f` | 依赖声明 + pytest/mypy 配置 |
| LLM 编辑点评增强 | P2 | `529f8c8` | 有态度的 prompt + Haiku 优先降本 |
| 公众号排版升级 | P2 | `813aea5` | 科技杂志风格 |

### 📋 待做

| 项目 | 优先级 | 工作量 |
|------|--------|--------|
| 类型提示完善（TypedDict + mypy） | P1 | 3-4h |
| 测试覆盖提升 | P1 | 4-6h |

### 教训：敏感信息管理（2026-04-11）
- **密钥不能放 config.json**：即使 .gitignore 排除了，文件系统可读就是风险
- **统一用环境变量**：`utils/config.py` 的 `get_claude_config()` 环境变量优先，config.json 降级
- **daily_run.sh 要 source .env**：launchd 环境没有用户 shell 的环境变量

### 教训：SQLite 并发写入（2026-04-11）
- **多进程写同一个 SQLite 必须设 busy_timeout**：否则 `database is locked`
- **WAL 模式允许读写并发**：`PRAGMA journal_mode = WAL` + `PRAGMA busy_timeout = 5000`
- **Python sqlite3.connect 的 timeout 参数也要设**：双重保险

### 教训：网络请求必须有重试（2026-04-11）
- **requests 裸调用一次失败就挂**：用 `urllib3.util.retry.Retry` + `HTTPAdapter` 包装
- **Claude API 429 要单独处理**：捕获 `anthropic.RateLimitError`，指数退避重试
- **except Exception 太宽泛**：改为具体异常类型（APIError / JSONDecodeError / KeyError），避免吞掉 bug

### 教训：错误处理要成体系
- 异常层级要和业务域对齐（采集/管道/发布 各有自己的异常类）
- exit code 要有意义，shell 脚本靠 exit code 区分失败原因
- 入口脚本统一模式：`News1Error → sys.exit(e.exit_code)`

### 教训：daily_run.sh 健壮性（2026-04-11）
- **wrapper 的 echo 会覆盖 $?**：必须先 `EXIT_CODE=$?` 再 echo
- **git checkout 被脏文件阻塞**：切分支前 `git stash --include-untracked`，切回后 `stash pop`
- **bundle 失败后不能继续生成**：用 SKIP_GENERATE 标志跳过 HTML/草稿步骤，避免用旧数据
- **bundle 日期要校验**：防止用昨天的 bundle_today.json 生成今天的内容
- **模型名要用实际可用的**：`claude-haiku-4-6` 不存在，503 后 fallback 浪费时间，改为 `claude-haiku-4-5-20251001`

### exit code 含义
| code | 含义 |
|------|------|
| 10 | CDP Proxy 未运行 |
| 11 | 微信登录态过期 |
| 12 | 采集超时/网络错误 |
| 13 | AI API 调用失败 |
| 14 | 草稿提交失败 |
| 15 | 数据处理失败 |
| 78 | launchd EX_CONFIG，脚本未运行 |
