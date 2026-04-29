---
name: finish
description: >
  Run post-development pipeline: tests, code review, change summary, knowledge sync, and commit.
  Use when changes are complete and ready to finalize, or when the user says
  "收尾", "提交", "finish", or after completing a development task.
version: 3.0.0
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

## 3. 改动说明

向用户输出结构化总结，**不等确认，直接继续**：

```
### 本次改动

**类型**：feat / fix / refactor / docs
**改了什么**：
- 文件1：做了什么
- 文件2：做了什么

**为什么**：简要说明原因
```

输出后**立刻进入步骤 4**，不等用户回应。全流程 1→5 自动执行。

## 4. 知识同步（Knowledge Sync）

将代码改动同步到文档体系。分四步执行，参照 `references/sync-matrix.md`：

### 4a. Inventory — 盘文档
列出项目所有 `.md` 文件：
- `CLAUDE.md`
- `.claude/rules/*.md`
- `.claude/projects/*/memory/*.md`（记忆文件）
- `.claude/research/*.md`（研究文档）

逐个读取，输出当前文件清单。目的是发现所有可能受影响的文档，不遗漏。

### 4b. Change Impact Matrix — 判影响
根据 `git diff --name-only` 判断变更类型，对照 `references/sync-matrix.md` 确定需要更新的文档列表。

**如果矩阵未覆盖本次变更类型**，按常识推断波及范围：改了哪个模块→该模块的文档在哪里→这些文档是否需要更新。

### 4c. Apply — 执行同步
按顺序修改：

1. **项目级文档**：`CLAUDE.md`、`.claude/rules/*.md`
2. **记忆文件**：`.claude/projects/*/memory/*.md`
3. **研究文档**：`.claude/research/*.md`（如有）

编辑原则：
- **合并优于追加**：同类信息合并到一处，不分散到多个文件
- **删除优于保留**：过期信息、已完成的 todo、推翻的决策 → 删，不留
- **相对时间**（"今天"、"最近"）→ 转为绝对日期
- **先读再改**：改任何文件前先完整读一遍，确认当前状态

### 4d. Self-check — 自查清单
改完后逐项确认：

- [ ] 所有被波及的文档都更新了？
- [ ] 没有相对时间遗留（"今天"、"最近"、"前几天"）？
- [ ] 没有矛盾的内容（新旧决策同时存在）？
- [ ] 已完成的待办已删除？
- [ ] 重复内容已合并？
- [ ] 记忆文件索引（MEMORY.md）的 description 是否与内容一致？

全部通过才继续。不通过 → 回到 4c 修复。

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

遇到问题参考 `gotchas.md`，变更矩阵参考 `references/sync-matrix.md`。
