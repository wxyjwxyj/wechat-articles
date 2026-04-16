---
globs: "**/*.py,daily_run.sh"
---

# 设计决策文档

**原则：改动前先读这里，改动后如有新决策及时补充。**

---

## 可用模型：只有 claude-opus-4-6（2026-04-11）

**背景：** 本机 API 环境（cckeys.top 代理）不支持 haiku 模型，`claude-haiku-4-5` 均返回 `INVALID_MODEL_ID`。

**决策：** 所有 Claude API 调用统一用 `claude-opus-4-6`，不做 haiku fallback。

**不要：** 在代码里加 haiku 作为首选或 fallback，会直接失败。

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
