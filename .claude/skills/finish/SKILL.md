---
name: finish
description: >
  Run post-development pipeline: garbled check, change summary, memory update, and commit.
  Use when changes are complete and ready to finalize, or when the user says
  "收尾", "提交", "finish", or after completing a development task.
version: 1.0.0
argument-hint: "[optional description]"
---

# 收尾流程

代码改完后按序执行，不等用户指示。

## 1. 乱码检查

对所有改动文件检查乱码：

```bash
git diff --name-only | xargs grep -n '�' 2>/dev/null
```

发现乱码 → 立即修复 → 重新检查，通过才继续。

## 2. 改动说明（唯一等用户的点）

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

## 3. 更新记忆

检查是否需要更新 memory 文件（`.claude/projects/.../memory/`）：
- 有新的踩坑经验 → 更新对应主题文件
- 项目状态变化 → 更新 MEMORY.md
- 没有新经验 → 跳过，不要强行更新

## 4. 提交

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

## 注意事项

遇到问题参考 `gotchas.md`。
