# AI 编程 / 代码智能 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉 AI 编程工具的基本概念，可以直接翻阅主报告。

> 🎯 **读完这篇你能**：区分 AI 编程的三个层级（补全 → 对话 → Agent），判断一个开发任务适合用哪一层工具，并能说出每层的技术边界和典型代表产品。

---

## 一、AI 编程工具是做什么的？

最简单的回答：**AI 编程工具 = 一个懂编程的 AI 助手，帮程序员写代码。**

但这背后有一个根本性的变化。传统上，写代码的流程是：

```
你在脑子里想好要做什么 → 手打代码 → 运行 → 修 bug → 再运行...
```

AI 编程工具改变了这个流程中的几个环节：

- **代码补全**：你写了一个函数名 `calculate_total`，AI 自动猜出你接下来要写什么，把整个函数体补全出来
- **对话式编程**：你用中文/英文说"帮我写一个用户登录页面"，AI 直接生成整段代码
- **Agent 编程**：你说"帮我重构这个模块，把数据库从 SQLite 迁移到 PostgreSQL"，AI 自主完成所有文件改动

三种模式的能力依次递增，也依次更难做好。

---

## 二、四个关键概念

### Code Completion（代码补全）

最常见也最成熟的 AI 编程功能。你在 IDE 里打字，AI 像输入法一样弹出灰色的代码建议，按 Tab 就接受。典型场景：

- 你写了一个函数签名 `def send_email(to, subject, body):`，AI 补全函数体
- 你写了一半的判断条件，AI 补全另一半
- 你写了 `for i in`，AI 补全 `range(len(items)):`

GitHub Copilot（2021 年推出；GitHub/Microsoft, 2021）把这种能力带给了全世界。

### Chat / 对话式编码

在 IDE 侧边栏里跟 AI 聊天。你问"这个函数是干什么的？"或"帮我把这段代码改成异步的"，AI 回答。比补全更灵活，但需要你手动把 AI 生成的代码粘贴到正确位置。

### Agent Mode（智能体模式）

AI 不再只是"回答你"，而是主动"做事"。你给一个任务，AI 自主决定：改哪些文件、执行什么命令、查什么文档。它可以看到整个代码库，不只是你当前打开的文件。

比如你说"给这个 API 加一个缓存层"，AI 会：
1. 找到所有 API 路由文件
2. 检查有没有缓存依赖
3. 在合适的文件里添加缓存逻辑
4. 运行测试确认没坏已有功能

2024-2025 年，Agent Mode 成为所有主流 AI 编程工具的标配。

### Vibe Coding（氛围编程）

2025 年 Andrej Karpathy 提出的概念，形容一种新的编程方式：**用户用自然语言描述需求，AI 生成代码，用户只看效果不提具体要求，不需要理解技术细节。** "Vibe" 指的不是编程本身的氛围，而是"我不直接写代码，但代码在被我间接创造"的那种状态。

这个词在 2025 年底到 2026 年初伴随着 Claude Code 的圣诞假期病毒式传播而出圈。Replit Agent、Claude Cowork 等产品专为这种"非程序员也能做软件"的场景设计。

---

## 三、四种产品形态

AI 编程工具从产品形态上分为四类：

### IDE 插件

在已有的代码编辑器（VS Code、JetBrains、Neovim）上安装插件。

**代表**：GitHub Copilot

**好处**：不用换编辑器，上手最快，用户基数最大（Copilot 2025 年累积 2000 万+用户）（GitHub/Microsoft, 2021）
**坏处**：功能受限于宿主编辑器的能力，Agent 模式不如原生 IDE

### Fork 式独立 IDE

把 VS Code 的源代码复制一份，在里面深度集成 AI 功能。

**代表**：Cursor、Windsurf

**好处**：AI 能力深度嵌入编辑器的每个角落，体验最丝滑
**坏处**：需要切换工具。VS Code 出新功能时，fork 版本需要手动同步。Cursor 在 2026 年会落后 VS Code 一个版本

### CLI Agent

在终端（命令行）里运行，不依赖图形界面。

**代表**：Claude Code

**好处**：适合自动化流程、CI/CD 集成，跟 Git 工作流无缝配合
**坏处**：没有图形界面，不直观，初学者门槛高
**适用**：资深开发者、DevOps 场景、远程服务器开发

### SaaS 平台/Agent

不本地安装，在浏览器里使用 AI 完成编码任务。

**代表**：Devin、Replit Agent

**好处**：零配置，浏览器即用，适合从零开始构建项目
**坏处**：不适合已存在的复杂项目，自主 Agent 的准确率不稳定

---

## 四、SWE-bench：衡量 AI 编程能力的"高考"

SWE-bench（Software Engineering Benchmark）是普林斯顿大学在 2023 年推出的基准测试（Jimenez et al., Princeton, 2024），用来衡量 AI 编程的真实能力。

**怎么测的**：从 GitHub 上找来 2,294 个真实的开源项目 Issue（Bugs 和 Feature Request），看 AI 能不能自动生成修复代码。

**一个具体的 Issue 长什么样**：

```
项目：django/django
Issue #12345：在管理后台创建用户时，密码字段没有正确校验
            如果密码包含特殊字符，会报 500 错误
测试：AI 需要找到正确的文件 → 修改代码 → 通过项目自带的测试
```

2023 年刚推出时，最好的 AI 系统只能解决不到 2% 的问题（Jimenez et al., Princeton, 2024）。到 2026 年 4 月，Claude Opus 4.7 能解决 87.6%（Verified 版本）（Anthropic, 2026）。这个进步速度本身就是一个故事。

**几个关键版本**：
- **SWE-bench**（原始版）：2,294 个 Issue
- **SWE-bench Verified**：从中精选 500 个，人工验证了问题描述清晰、有明确测试可验证
- **SWE-bench Live**：实时更新的版本，避免模型"刷题"

SWE-bench 分数是 AI 编程行业的"高考成绩"——每个新产品发布必报这个数。

---

## 五、为什么 SWE-bench 分数 100% 不等于 AI 能替代程序员？

这是一个重要的直觉：

SWE-bench 测的是"给定一个 Issue 描述，改一段代码让它通过测试"。它不测：

- **设计能力**：架构设计、技术选型、系统分解——这些是资深工程师的核心能力
- **跨功能协作**：跟产品经理讨论需求、跟设计师确认 UI、跟 QA 讨论测试策略
- **长期维护**：代码上线后出问题了怎么办、技术债怎么管理
- **上下文宽度**：一个 Issue 通常只涉及 1-3 个文件，但真实项目改一个功能可能要改 20 个文件

打个比方：SWE-bench 高分意味着 AI 是一个**极其熟练的修理工**——你来报修一个具体问题，它很快能修好。但一个修理工不等于你能把整个房子的设计、施工、监理全交给它。

---

## 六、主流产品速览

| 产品 | 开发商 | 形态 | 核心特点 |
|------|--------|------|---------|
| **GitHub Copilot** | GitHub/Microsoft | VS Code 插件 | 用户基数最大（2000 万+）（GitHub/Microsoft, 2021），微软生态，支持多模型 |
| **Cursor** | Anysphere | Fork IDE | 编辑体验最丝滑，多模型切换，2026 年估值 $60B（Anysphere，社区估算） |
| **Claude Code** | Anthropic | CLI Agent | Agent 能力最强，只调用 Claude 模型（Anthropic），开发者中最极客的选择 |
| **Devin** | Cognition | SaaS Agent | 全自主 AI 工程师，异步工作，出评测报告 |
| **Windsurf** | Cognition（原 Codeium）| Fork IDE | AI-native 编辑器，2025 年被 Cognition 收购 |
| **Replit Agent** | Replit | 在线 IDE | 浏览器即用，零配置，面向非程序员的 No-code 编程 |

---

## 七、一个简单的直觉框架

把 AI 编程工具放在两个维度上看：

```
自主程度
    ↑
全自主  |  Devin / Replit Agent
    |
半自主  |  Cursor Agent / Claude Code Agent
    |
辅助    |  Copilot / Cursor Tab
    |
起始    |  代码补全
         └────────────────────→ 产品深度
              插件        IDE      CLI
```

**越往右上角越强大，但也越不靠谱**。全自主 Agent 看起来很厉害，但可能在关键地方出错，而开发者要检查它做的每一件事——反而可能更累。2026 年的行业共识是：半自主（人在回路中审核）是最实用的模式。

---

## 参考来源

- **Evaluating Large Language Models Trained on Code** (Chen et al., OpenAI, 2021) — Codex 论文，首次提出 HumanEval 基准，开创了 AI 代码生成的系统性评测 — https://arxiv.org/abs/2107.03374
- **SWE-bench: Can Language Models Resolve Real-World GitHub Issues?** (Jimenez et al., Princeton, 2024) — AI 编程领域事实标准评测，用 2294 个真实 GitHub Issue 衡量模型修 Bug 能力 — https://arxiv.org/abs/2310.06770
- **GitHub Copilot** (GitHub/Microsoft, 2021) — AI 代码补全的开创者，2025 年累积 2000 万+ 用户 — https://github.com/features/copilot
- **Cursor** (Anysphere) — Fork 式独立 IDE，深度集成 AI 能力，2026 年估值 $60B — https://cursor.sh/
- **Claude Code** (Anthropic) — CLI Agent 形态，Agent 自主编程能力业界领先，与 Git 工作流无缝配合 — https://docs.anthropic.com/en/docs/claude-code
- **Devin** (Cognition) — 全自主 AI 软件工程师，异步工作模式，出评测报告 — https://www.cognition.ai/devin
