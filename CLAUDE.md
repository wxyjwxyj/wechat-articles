# 微信公众号 AI 日报自动化系统

## 项目概述

自动采集微信公众号 AI 新闻 → 去重打标签 → 生成公众号稿件 → 提交草稿箱 → 推送 GitHub Pages，全链路自动化。

## 主链路

```
fetch_wechat_today.py（微信9个公众号，需CDP）  ┐
fetch_hackernews_today.py（HN AI热门）         │
fetch_arxiv_today.py（ArXiv AI论文）           ├→ content.db
fetch_github_trending_today.py（GitHub Trending）│
fetch_rss_today.py（TechCrunch/MIT/The Verge） ┘
  → build_bundle.py（去重 → 打标签 → bundle）→ bundle_today.json
  → generate_html.py + generate_mp_article.py（输出）
  → publish_to_mp.py（封面图 + 草稿箱）
  → daily_run.sh 步骤13（推 GitHub Pages）
```

## 开发规范

### 本文件维护原则
- CLAUDE.md 只放**规范性内容**（规则、约定、工作流），不放参考信息
- 参考信息放到 MEMORY.md 或对应文档，通过链接引用
- 保持精简，避免上下文窗口被非规范内容占用

### 详细规范（按需自动加载）

规则文件在 `.claude/rules/` 下，Claude 访问相关文件时自动加载：

| 规则文件 | 内容 |
|----------|------|
| `code-style.md` | PEP 8、模块职责边界、技术要点 |
| `testing.md` | 测试命名、mock 路径、全量验证要求 |
| `git.md` | 提交格式、分支约定、GitHub Pages 流程 |
| `deprecated.md` | 废弃脚本列表 |

### 文件读取原则
- 大文件（>200行）分段读取，先看结构再看细节

### 开发工作流

1. **需求确认**：需求不清晰时先问清再动手，明确范围和验收标准
2. **方案设计**：跨多文件改动或新功能，先列方案，确认后再写代码
3. **开发**：编写/修改代码，每步改动尽量小且可验证
4. **收尾**：代码改完后**自动**使用 `finish` skill 一键完成收尾流程（测试→Code Review→改动说明→记忆→提交），不等用户指示

注意：每一步完成后再进入下一步，不要跳步。收尾流程中任何一步失败则停下修复。

## 错误处理

自定义异常层级在 `utils/errors.py`，所有入口脚本统一 `News1Error → sys.exit(e.exit_code)`：

| exit code | 含义 |
|-----------|------|
| 10 | CDP Proxy 未运行 |
| 11 | 微信登录态过期 |
| 12 | 采集超时/网络错误 |
| 13 | AI API 调用失败 |
| 14 | 草稿提交失败 |
| 15 | 数据处理失败 |

## 关键配置

- CDP Proxy：`http://localhost:3456`（config.json 可覆盖）
- 敏感配置：`.env`（API Key 等，不进 Git）
- 主数据源：`content.db`（SQLite，WAL 模式）
- GitHub Pages：https://wxyjwxyj.github.io/wechat-articles/
- **index.html 是手写门户页，不能覆盖！**

## 一键执行

```bash
./daily_run.sh        # 全自动（launchd 每天 11:30 调用）
./run.sh              # 交互式执行
```

## 压缩指令

When compacting, preserve:
- 修改过的文件完整列表
- 未完成的任务和下一步计划
- 关键决策和原因
- 遇到的错误和解决方式

## 项目历史

详见 `.claude/projects/-Users-zouapeng-Downloads-03------news1/memory/MEMORY.md`
