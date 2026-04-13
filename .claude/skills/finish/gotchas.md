# 收尾流程常见坑

## 流程纪律

### 不要跳步
- 质量检查（测试+乱码）→ Code Review → 改动说明 → MEMORY → 提交，按顺序
- 质量检查没过不做 Code Review

### 并行阶段的回退规则
- 测试和乱码检查同时启动，不串行等待
- 任一失败 → 修复 → 两个都重跑（修复可能引入新问题）
- Code Review 发现问题修复后 → 回退步骤 1，不能只重跑 Review
- 同一阶段回退超过 2 次 → 停下来重新审视

### 改动说明是唯一等用户的点
- 之前的步骤（测试、乱码、Code Review）全自动
- 之后的步骤（MEMORY、提交）全自动
- **不要反问"需不需要更新 MEMORY"、"要不要提交"**

### 代码改完后自动触发
- 开发完成后应主动调 finish，不等用户说"收尾"
- 不要改完代码就停下等指示

## Code Review

### 必须派 subagent，不要自审
- 自己审查自己写的代码容易盲区
- subagent 不需要会话历史，只需变更范围

### 发现问题先修再继续
- 不要把问题留到改动说明里让用户判断
- 修完回退步骤 1 重跑

### subagent 反馈不合理时可以推回
- 用技术理由推回，不盲目接受

## 测试

### 必须派 test-runner subagent
- 不要在主对话直接跑 pytest
- 全量范围：`tests/`，不能只跑改动文件的测试
- 修复后必须重新派 subagent 验证

## 乱码检查

### 中文项目特别注意
- 每个含中文的改动文件都要检查
- 大段中文用 Edit 修改时最容易出乱码，优先用 Write 整文件重写
- grep 示例行中的 `�` 不算乱码

## 提交

### 不要 git add -A
- 只 add 本次改动相关的文件
- `git add -A` 可能把 .env、content.db、cover_today.png 等不该提交的文件加进去

### commit message 格式
- 用 HEREDOC 传递，避免引号转义问题
- type 只用：feat / fix / refactor / test / docs

### 只提交一次
- 所有改动（代码 + 文档）一次性提交
- 不要分多次 commit

## Claude API Prompt

### 所有 prompt 指令部分必须用英文
- cckeys.top 代理会拦截中文指令性 prompt，返回无关内容（"I can't discuss that" 或 "I'm Kiro..."）
- 受影响的场景：翻译、去重、评分、query 扩展等所有调用 Claude API 的地方
- **输出内容可以是中文**（如"翻译成中文"、"写中文点评"），但 prompt 的指令框架要用英文
- **"You are..."角色扮演句式也会被拦截**，改为直接描述任务（如 "Write brief comments..." 而不是 "You are the chief editor..."）
- 排查方法：加 `logger.info("原始响应: %s", raw[:300])` 看代理实际返回了什么

### 已修复的文件
- `pipeline/dedupe.py` - 去重 prompt
- `scripts/build_bundle.py` - 翻译 prompt
- `research/claude_scorer.py` - 评分 prompt
- `research/topic_searcher.py` - query 扩展 prompt

## MEMORY 更新

### 不要写重复内容
- 先读 MEMORY.md 现有内容，确认没有重复再写
- 只记录稳定的经验，不记录临时状态
- 有新的主题就创建独立文件，在 MEMORY.md 索引里加链接
