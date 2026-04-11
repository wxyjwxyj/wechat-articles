---
name: finish
description: >
  Run post-development pipeline: tests, code review, change summary, memory update, and commit.
  Use when changes are complete and ready to finalize, or when the user says
  "收尾", "提交", "finish", or after completing a development task.
version: 2.0.0
argument-hint: "[optional description]"
---

# 收尾流程

代码改完后按序执行，不等用户指示。

## 1. 质量检查（并行）

同时启动，不串行等待：

- 派 **test-runner** subagent：全量测 `tests/`，需看到 Status: PASS
- 乱码检查：`git diff --name-only | xargs grep -n '�' 2>/dev/null`

任一失败 → 修复 → **两个都重跑**。

## 2. Code Review

- 获取 `git diff --name-only` 变更文件列表
- 派 **code-reviewer** subagent，给它变更文件列表
- Status: PASS 才继续
- Status: FAIL → 修复问题 → **回退步骤 1 重跑**

## 3. 改动说明（唯一等用户的点）

向用户输出结构化总结，等确认：

```
### 本次改动

**类型**：feat / fix / refactor / docs
**改了什么**：
- 文件1：做了什么
- 文件2：做了什么

**为什么**：简要说明原因
```

用户确认后继续。改动说明之后的步骤全部自动执行，**不要反问"需不需要更新 XX"**。

## 4. 更新记忆

检查是否需要更新 memory 文件（`.claude/projects/.../memory/`）：
- 有新的踩坑经验 → 更新对应主题文件
- 项目状态变化 → 更新 MEMORY.md
- 没有新经验 → 跳过，不要强行更新

## 5. 提交

```bash
git add <相关文件>
git commit -m "<type>: <subject>

<body>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

注意：
- 只 add 本次改动相关的文件，不要 `git add -A`
- commit message 用 HEREDOC 传递
- type 只用：feat / fix / refactor / test / docs

## 回退规则

- 步骤 1 任一失败 → 修复 → 两个都重跑
- 步骤 2 发现问题 → 修复 → 回退步骤 1
- 同一阶段回退超过 2 次 → 停下来重新审视问题
- 必须派 subagent 做 review，不要自审

## 注意事项

遇到问题参考 `gotchas.md`。
