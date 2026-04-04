# 微信公众号 AI 日报自动化系统

## 项目概述

自动采集微信公众号 AI 新闻 → 去重打标签 → 生成公众号稿件 → 提交草稿箱 → 推送 GitHub Pages，全链路自动化。

## 主链路

```
fetch_wechat_today.py（采集）→ content.db
  → build_bundle.py（去重 → 打标签 → bundle）→ bundle_today.json
  → generate_html.py + generate_mp_article.py（输出）
  → publish_to_mp.py（封面图 + 草稿箱）
  → daily_run.sh 步骤13（推 GitHub Pages）
```

## 一键执行

```bash
./daily_run.sh        # 全自动（launchd 每天 9:57 调用）
./run.sh              # 交互式执行
```

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `fetch_wechat_today.py` | CDP Proxy + 同步 XHR 采集今日文章 |
| `scripts/build_bundle.py` | 标准化 → Claude 去重 → 打标签打分 |
| `generate_html.py` | 生成 today.html 完整版 |
| `scripts/generate_mp_article.py` | 生成公众号发布稿 JSON |
| `scripts/publish_to_mp.py` | 封面图生成+上传 → 草稿箱提交（`--dry-run`） |
| `scripts/seed_sources.py` | 初始化公众号 sources 表 |

废弃脚本列表见 `.claude/rules/deprecated.md`

## 开发规范

详细规则在 `.claude/rules/` 下，按需自动加载：

| 规则文件 | 内容 |
|----------|------|
| `code-style.md` | PEP 8、模块职责边界、技术要点 |
| `git.md` | 提交格式、分支约定、GitHub Pages 流程 |
| `deprecated.md` | 废弃脚本列表 |

### 文件读取原则
- 大文件（>200行）分段读取，先看结构再看细节

### 开发工作流
1. 需求不清晰时先问清再动手
2. 跨多文件改动先列方案
3. 代码改完后主动执行收尾（测试→提交→更新记忆）

## 关键配置

- CDP Proxy：`http://localhost:3456`（config.json 可覆盖）
- 主数据源：`content.db`（SQLite）
- GitHub Pages：https://wxyjwxyj.github.io/wechat-articles/
- **index.html 是手写门户页，不能覆盖！**

## 压缩指令

When compacting, preserve:
- 修改过的文件完整列表
- 未完成的任务和下一步计划
- 关键决策和原因
- 遇到的错误和解决方式

## 项目历史

详见 `.claude/projects/-Users-zouapeng-Downloads-03------news1/memory/project_wechat_lessons.md`
