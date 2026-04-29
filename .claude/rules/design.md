---
globs: "**/*.py,daily_run.sh"
---

# 设计决策文档

**原则：改动前先读这里，改动后如有新决策及时补充。**

---

## 可用模型与统一调用入口（2026-04-26 更新）

**背景：** 模型、API Key、Base URL 均从 `.env` 环境变量读取（`ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL`），config.json 降级兜底。

**决策：** 所有 Claude API 调用统一通过 `utils/claude.py` 的 `claude_call()` / `claude_stream()` / `get_client()`。模型名从配置读取，换代理只改 `.env`，代码不用动。不要直接创建 `anthropic.Anthropic` client。

**不要：** 在各模块里直接 `import anthropic` 创建 client，也不要硬编码模型名。

---

## 密钥管理：环境变量优先，config.json 降级（2026-04-11）

**背景：** claude_api_key 明文存在 config.json，虽然 .gitignore 排除了但文件系统可读。

**决策：** `utils/config.py` 统一读取，`ANTHROPIC_API_KEY` 环境变量优先，config.json 降级兜底。`daily_run.sh` 启动时 `source .env`。

**不要：** 把密钥放回 config.json，也不要在代码里直接读 config.json 的 claude_api_key。

---

## items 冲突键：content_hash 而非 url（2026-04-11）

**背景：** url 语义变化时（如 HN 从原文链接改为讨论页），旧数据无法被 upsert 覆盖，产生重复记录。

**决策：** `items` 表冲突键改为 `content_hash unique`，url 改为可更新字段。

**不要：** 用 url 做 upsert 冲突键，url 是可变的展示字段。

---

## SQLite 并发：WAL + busy_timeout（2026-04-11）

**背景：** daily_run.sh 同时跑 5 个采集脚本写 content.db，偶发 `database is locked`。

**决策：** `storage/db.py` 的 `get_connection()` 统一设置 `journal_mode=WAL` + `busy_timeout=5000` + `timeout=10`。

**不要：** 在各脚本里单独设置 PRAGMA，统一在 get_connection 一处管理。

---

## 网络请求：统一 retry session（2026-04-11）

**背景：** 采集脚本裸调 requests，网络抖动一次就整个失败。

**决策：** `utils/http.py` 的 `retry_session()` 返回带指数退避的 Session（3 次重试，覆盖 429/5xx）。所有 collector 用 `self._session`。

**不要：** 在各脚本里自己写重试逻辑，统一用 retry_session()。

---

## Claude prompt：全英文指令（2026-04-13）

**背景：** cckeys.top 代理会拦截特定 prompt 模式，返回 "I'm Kiro" 或 "I can't discuss that"。

**规律：**
- 中文指令性 prompt → 拦截
- `"You are [角色]..."` 角色扮演句式 → 拦截
- 英文直接描述任务（"Translate...", "Score..."）→ 正常
- 输出内容可以是中文，只要指令框架是英文

**不要：** 用中文写 prompt 指令，也不要用 "You are..." 开头。

---

## 深度研究：SSE 流式输出（2026-04-15）

**背景：** Claude API 生成横纵分析报告需要 1-3 分钟，同步等待体验极差。

**决策：** `/research/deep` 用 SSE（Server-Sent Events）流式推送，前端实时渲染 chunk，用户看到内容逐字出现。

**不要：** 用轮询或同步接口做深度研究，响应时间太长。

---

## f-string 里嵌 JS 代码的转义（2026-04-14）

**背景：** `result_renderer.py` 用 f-string 生成含 `<script>` 块的 HTML，JS 正则里的 `\n` 在 Python f-string 里是真实换行，导致 JS 语法错误。

**决策：**
- JS 正则中的 `\n` 写成 `\\n`
- `\*\*` 写成 `[*][*]`（避免无效转义）
- 用户输入嵌入 JS：`json.dumps(value).replace("</", "<\\/")` 防 `</script>` 注入

**不要：** 在 f-string 里直接写 JS 正则的 `\n`、`\*` 等转义序列。

---

## 手动跑脚本读不到 API key（2026-04-13）

**背景：** 项目用 `.env` 存密钥，直接 `python scripts/xxx.py` 时读不到 `ANTHROPIC_API_KEY`。

**正确姿势：**
```bash
set -a && source .env && set +a && python scripts/xxx.py
```

**不要：** 直接 `python scripts/xxx.py`，环境变量没注入。

---

## 翻译结果持久化到 DB（2026-04-19）

**背景：** 海外条目（HN/ArXiv/GitHub/RSS）每次 build_bundle 都要调 Claude 翻译 title/summary，重复跑浪费 API 额度且慢。

**决策：** 翻译结果写入 items 表的 `title_zh` / `summary_zh` 字段，下次 `build_bundle.py` 检测到已有翻译（`item.get("title_zh")`）直接跳过。重跑 bundle 秒级完成。

**不要：** 每次都重新翻译，也不要把翻译结果只存在 bundle JSON 里（重跑就丢了）。

---

## 并行采集：HN 直连，ArXiv/GitHub/RSS 走代理（2026-04-29 更新）

**背景：** 4 个非微信数据源互相独立，串行太慢。早期认为 ArXiv 直连更稳定，实测走代理反而更快（0.9s vs 11.2s），ArXiv API（export.arxiv.org）对代理 IP 未见额外限流。

**决策：** `daily_run.sh` 用 `&` 并行启动 4 个采集进程，`wait` 收集 exit code。HN 用 `env -u http_proxy` 去掉代理直连，ArXiv/GitHub/RSS 保留代理。

**不要：** 给 ArXiv 去掉代理（直连更慢），也不要串行跑采集（浪费时间）。

---

## ArXiv 候选池：max_results=100 保证筛选质量（2026-04-29）

**背景：** ArXiv 用 7 个分类（cs.AI/CL/CV/LG/MA/RO/stat.ML）做 3 天窗口筛选，候选池大小直接影响最终 top-10 质量。

**实验对比：**
| max_results | top-10 分数分布 | 最高分 |
|:---:|:---|:---:|
| 30 | 7,5,5,5,5,5,4,4,4,3 | 7分 |
| 50 | 7,7,6,6,5,5,5,5,5,5 | 7分 |
| 100 | 8,7,7,6,6,6,6,5,5,5 | 8分 |

**决策：** `fetch_arxiv_today.py` 传 `max_results=100`，ArxivCollector 默认值保持 30（仅供 research 模块搜索使用）。API 返回 200-250KB，网络开销跟 50 条几乎无差别（同一次 HTTP 往返）。同时 ArXiv 采集加 20-40s 随机 jitter，错开与其他并行采集的请求时间窗口，降低 429 概率。

**不要：** 为了省带宽降低 max_results（省了几 KB 但丢掉高质量论文）。

---

## 日志系统：stderr + 按天文件（2026-04-19）

**背景：** 需要实时看输出（stderr），也需要事后排查（文件）。

**决策：** `utils/log.py` 的 `get_logger()` 统一配置 root logger，同时输出到 stderr 和 `.claude/logs/YYYY-MM-DD.log`。格式 `[时间] 级别 模块名 - 消息`。`daily_run.sh` 自动清理 30 天前的日志。

**不要：** 在各模块里自己配 logging，统一用 `get_logger(__name__)`。

---

## claude_call 内置 429 限流重试（2026-04-19）

**背景：** Claude API 高频调用（批量打标签、翻译）容易触发 429 限流，单次失败就中断整个流水线。

**决策：** `utils/claude.py` 的 `claude_call()` 对 `RateLimitError` 单独做 3 次指数退避重试（2s/4s/8s），3 次都限流则抛出异常。这是 API 层重试，跟 `retry_session` 的 HTTP 层重试是两层独立机制。

**不要：** 在调用方自己写 429 重试逻辑，`claude_call` 已经内置了。

---

## build_bundle 并发翻译（2026-04-19）

**背景：** 海外条目翻译是 IO 密集型（等 Claude API 响应），串行翻译 20 条要 1-2 分钟。

**决策：** `build_bundle.py` 用 `ThreadPoolExecutor(max_workers=5)` 并发翻译，5 条同时发请求。这是进程内的线程级并发，跟 `daily_run.sh` 的进程级并行是两个层面。

**不要：** 串行翻译（太慢），也不要开太多 worker（容易触发 429）。

---

## 统一调度：schedule.yaml + scheduler.py（2026-04-22）

**背景：** 调度时间分散在 com.news1.daily.plist 和 com.news1.publish.plist 两个文件，改时间要改多处。

**决策：** `schedule.yaml` 是唯一的调度配置，`scripts/scheduler.py` 每5分钟被 launchd 触发，读 yaml 判断是否命中任务。`daily_run.sh` 支持 `--steps` 参数按需执行步骤子集。`.ran/` 目录存放"今天已跑"标记文件防止重复触发。

**不要：** 在 plist 里硬编码任务时间，也不要直接改 daily_run.sh 的执行时间。调度时间只在 `schedule.yaml` 一处维护。
