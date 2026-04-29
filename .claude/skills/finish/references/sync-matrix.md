---
name: sync-matrix
description: 代码变更类型 → 需同步的文档清单。用于 finish skill 的 Change Impact Matrix 步骤。
---

# 变更影响矩阵 — news1 项目

## 代码层变更 → 文档层变更

| 变更类型 | 需同步的文档 |
|---------|------------|
| **新增/修改 collector**（`collectors/`） | ➜ `CLAUDE.md` 主链路描述、`deprecated.md`（旧脚本需废弃）、memory（踩坑经验） |
| **新增/修改 pipeline**（`pipeline/` `scripts/build_bundle.py`） | ➜ `design.md`（对应决策：翻译/并行/去重/时区等）、`CLAUDE.md` 主链路、memory |
| **新增/修改 storage/DB**（`storage/`） | ➜ `design.md`（SQLite WAL、冲突键等决策）、`CLAUDE.md` 目录约定 |
| **修改 config/API/模型**（`.env` `config.json` `utils/claude.py` 等） | ➜ `design.md`（密钥管理、统一调用入口、模型配置） |
| **修改 schedule/launchd**（`schedule.yaml` `scripts/scheduler.py`） | ➜ `design.md`（统一调度） |
| **修改 HTML/前端**（`generate_html.py` `archive/`） | ➜ `git.md`（分支推送规则）、`CLAUDE.md` GitHub Pages 说明 |
| **新增/修改 utils 工具** | ➜ `design.md`（网络请求、日志、错误处理等对应决策）、`CLAUDE.md` 目录约定 |
| **新增依赖/修改 Python 包** | ➜ `CLAUDE.md`（环境管理）、memory |
| **修改 testing 相关** | ➜ `testing.md` |
| **新增功能/特性（跨多文件）** | ➜ 以上全部 + `CHANGELOG.md` |
| **新增术语/改命名** | ➜ 全局搜索旧术语替换 |

## 记忆层变更处理

| 情境 | 操作 |
|-----|------|
| 新的踩坑经验 | 创建新主题文件或更新已有文件 |
| 过期的经验/决策 | 更新对应文件，保留新事实 |
| 相对时间（"今天"、"最近"） | 转为绝对日期 |
| 重复记录 | 合并为一条，更新索引 description |
| 已完成的待办 | 直接删除 |
| 推翻的决策 | 删除旧条目，保留新决策 |
| 跨会话只用一次的临时上下文 | 删除 |

## 编辑原则

- **合并优于追加**：同类信息写到一处，不分散到多个文件
- **删除优于保留**：过期信息比没有信息更糟糕 — AI 读到过期内容会在错误的前提下做事
- **先读再改**：改任何文件前先完整读一遍，确认当前状态
