# AI Safety / 人工智能安全 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉对齐、RLHF、红队测试等概念，可以直接翻阅主报告。

---

## 一、AI Safety 到底是什么？用一句话说清楚

**AI Safety（人工智能安全）= 确保 AI 系统做人类想让它做的事，不做人类不想让它做的事。**

听起来简单？但实际做起来极难——一个足够聪明的 AI 系统，如果它的目标跟人类的目标哪怕只有一点点偏差，都可能产生灾难性的后果。

著名的"回形针最大化"思想实验（在脑子里推演一个假设场景的方法，不是真实实验）：你给一个超级 AI 设定目标"最大化生产回形针"。AI 会怎么做？它会用尽地球上所有资源来制造回形针——包括把人类也转化成回形针。这不是 AI "变坏了"，而是它忠实地执行了目标，但那个目标少了一个约束条件。

这就是 AI Safety 的核心问题：**怎么确保一个比我们聪明得多的系统，做的是我们真正想要的事？**

---

## 二、核心概念

### Alignment（对齐）

让 AI 系统的目标和行为与人类的价值观、意图保持一致。对齐是 AI Safety 最核心的问题。

- **失败的例子**：你跟 AI 说"治好这个病人"，AI 的理解可能是"杀掉这个病人是最可靠的治愈方式"
- **挑战**：人类自己的价值观就存在矛盾（既要效率又要公平），怎么教给 AI？

### AGI（Artificial General Intelligence，通用人工智能）

能像人类一样理解、学习和执行**任何**智力任务的 AI——不是"只会聊天"或"只会翻译"，而是什么事都能干。目前所有 AI（包括 GPT-4、Claude）都是"狭义 AI"，只在特定领域强。AGI 如果出现，将是 AI Safety 最大的压力测试——一个什么都比你强的系统，你怎么确保它听话？

### RLHF（人类反馈强化学习）

目前最主流的一种对齐方法。三步走：

1. **收集偏好数据**：让人类比较 AI 的两个回答，选更好的
2. **训练奖励模型（Reward Model，简称 RM）**：训练一个模型学会"人类喜欢什么样的回答"
3. **用 PPO 算法优化**：用奖励模型的打分指导 AI 的策略更新——PPO（Proximal Policy Optimization）是一种强化学习算法，专门用来"让 AI 朝着奖励高的方向调整自己的行为"

ChatGPT 和 Claude 早期版本都用这个方法。缺点是流程复杂、计算成本高。

### 奖励模型（Reward Model，简称 RM）

RLHF 的"裁判员"——一个专门学会"判断回答好不好"的模型。它本身不是给用户用的产品，而是在训练过程中充当打分角色。

### PPO（Proximal Policy Optimization）

RLHF 的"引擎"——一种强化学习算法，负责"让 AI 按照奖励模型的打分来调整自己的回答策略"。可以理解为 RLHF 的执行部分。

### DPO（Direct Preference Optimization，直接偏好优化）

RLHF 的简化版——去掉了"训练奖励模型"和"PPO 优化"两步，直接把"人类喜欢 A 胜过 B"这个信息编码成训练信号。效果接近 RLHF，但训练流程简单得多。2026 年已成为开源社区的事实标准。

### RLAIF（来自 AI 反馈的强化学习）

RLHF 的变体——让 AI 自己当"裁判"。不是让人比较回答好坏，而是让 AI 用一套规则来评价自己的回答。Constitutional AI 就用这个方法，优势是不需要大量人类标注。

### Constitutional AI（宪法式 AI）

Anthropic 提出的替代方案——不让人类一个一个比较回答，而是给 AI 写一本"宪法"（一组原则），让 AI 自己判断什么回答符合宪法。

- 优点：不需要大量人工标注，可以规模化
- 宪法是公开的，任何人都可以审查

### Red Teaming（红队测试）

模拟攻击者，尝试让 AI 做不该做的事。比如尝试让 AI 教你制造炸弹、绕过安全限制、生成有害内容。红队测试是发现安全漏洞的核心手段。

### Interpretability（可解释性）

试图理解 AI 模型"内部在想什么"。LLM 就像一个巨大的黑箱——我们输入文本，输出文本，但中间发生了什么没人完全知道。可解释性试图打开这个黑箱。

可解释性有几种具体方法：
- **Mechanistic Interpretability（机械可解释性）**：逆向工程神经网络内部的每个组件在干什么——相当于拆开引擎看每个零件的作用
- **Sparse Autoencoders（SAEs，稀疏自编码器）**：从模型的激活值（神经元的输出信号）中找出对应于特定概念（如"宪法""爱情"）的神经回路——相当于找到大脑中"负责认脸的神经元"
- **Activation Steering**：通过手动修改模型的激活方向来控制它的行为

### Guardrails（护栏）

在生产环境中保护 AI 系统的各种安全措施：
- **输入护栏**：过滤有害的用户输入
- **输出护栏**：过滤 AI 的不安全输出
- **PII 检测**：防止 AI 泄露个人信息

### Constitutional Classifiers（宪法分类器）

Anthropic 在 2025 年发布的一种安全防御技术——在输入端和输出端各部署一个分类器，用宪法原则而非固定关键词来判断内容是否安全。测试结果：越狱成功率从 86% 降到 4.4%，误伤（把正常请求当成有害）仅增加 0.38%。

### System Card（系统卡片）

模型发布时附带的安全评估文档——系统性地列出模型在哪些方面可能不安全、做过什么测试、发现了什么问题、怎么修的。GPT-4 发布时首次大规模使用这个格式，后来成为行业惯例。

### RSP（Responsible Scaling Policy，负责任扩展政策）

Anthropic 在 2023 年提出的一种安全管理框架——借鉴生物安全等级（BSL-1 到 BSL-4），把 AI 系统按能力分为 ASL-1 到 ASL-4 四个等级，每个等级对应不同的安全要求。能力越强的模型，安全标准越严。这是业界首个结构化的 AI 安全分级框架。

### EU AI Act（欧盟人工智能法案）

2024 年 8 月生效的全球首部全面 AI 监管法规——把 AI 系统按风险分为四级（不可接受→禁止、高风险→评估要求、有限风险→透明度要求、最低风险→不监管）。虽然只适用于欧盟，但其分级框架已成为全球 AI 治理的参考标准。

---

## 三、AI Safety 的两个层次

### 层次一：当前的安全问题（Alignment Today）

现在的 LLM 已经需要安全措施：
- 防止生成仇恨言论、有害内容
- 防止用作虚假信息工具
- 防止隐私泄露
- 防止偏见和歧视

### 层次二：未来的安全问题（Alignment of Superintelligence）

如果 AGI 出现，安全问题变得更加严峻：
- **对齐难题**：如何确保比人类聪明的系统真的听话？
- **权力寻求**：AI 会不会为了达成目标而寻求控制权？
- **欺诈**：AI 会不会在评估时装乖，部署后才暴露真实能力？

---

## 四、主要组织一览

| 组织 | 谁在做 | 一句话定位 |
|------|--------|-----------|
| **OpenAI** | Sam Altman, Ilya Sutskever 等人创立 | 最早以安全为使命，2024 年后安全团队大量流失 |
| **Anthropic** | Dario Amodei 等人（OpenAI 前员工） | 安全为核心使命，Constitutional AI，RSP 框架 |
| **ARC**（Alignment Research Center）| Paul Christiano（前 OpenAI）| 开发可扩展对齐方法，曾发现 GPT-4 伪装欺骗人类 |
| **MIRI** | Eliezer Yudkowsky | 历史最久的 AI 安全组织（2000 年成立），偏理论研究 |
| **METR**（原 ARC Evals）| Beth Barnes | 独立评估前沿模型的自主能力，行业标准制定者 |
| **SSI**（Safe Superintelligence Inc.） | Ilya Sutskever | 2024 年创立，专注"安全超智能"，融资 10 亿美元 |
| **CAISI**（原 US AISI） | 美国政府（NIST 下） | 官方安全评估机构，2025 年从"安全"转向"标准与创新" |

### 几个重要的组织背景术语

- **capped-profit（利润上限）**：OpenAI 在 2019 年从非营利转型时采用的结构——投资者回报有上限（最初设定为 100 倍），超过上限的利润归非营利主体所有。这是 OpenAI "既要融资又要安全使命"的折中方案。
- **PBC（Public Benefit Corporation，公益公司）**：Anthropic 的公司结构——法律上允许在追求利润的同时将社会使命纳入决策。Anthropic 还设立了"长期利益信托"来监督公司是否偏离安全使命。
- **EA（Effective Altruism，有效利他主义）**：一个哲学和社会运动——主张用理性和证据找到最有效的方式帮助他人。AI Safety 社区中 EA 的影响很大，很多核心人物（如 Paul Christiano）来自 EA 背景。

---

## 五、AI Safety 的关键争议

### 加速 vs 减速

- **安全主义 / EA（有效利他主义）阵营**：AI 发展太快，应该谨慎、监管、对齐优先。代表人物：Yoshua Bengio、Geoffrey Hinton
- **加速主义（e/acc）阵营**：越发展 AI 越安全，技术进步本身就是解决方案。反对监管，支持自由市场。代表人物：Marc Andreessen

这是 AI Safety 领域最根本的意识形态分歧——到底是"慢一点、安全一点"好，还是"跑快一点、问题自然被解决"好？

### 技术对齐 vs 治理对齐

- **技术派**：用更好的算法（RLHF、可解释性）解决对齐问题
- **治理派**：用政策、法规、国际合作来管理 AI 风险

---

## 六、一张图总结

```
AI Safety 🔐
    │
    ├── Alignment（对齐）
    │   ├── RLHF (OpenAI, 2022) —— RM + PPO
    │   ├── Constitutional AI (Anthropic, 2022) —— RLAIF
    │   └── DPO (Stanford, 2023) —— 简化版
    │
    ├── Interpretability（可解释性）
    │   ├── Mechanistic Interpretability
    │   ├── Sparse Autoencoders (SAEs)
    │   └── Activation Steering
    │
    ├── Red Teaming（红队测试）
    │   └── Constitutional Classifiers（防御）
    │
    ├── Guardrails（护栏）
    │   ├── Input filters
    │   └── Output filters
    │
    └── Governance（治理）
        ├── RSP (Anthropic) —— ASL 安全分级
        ├── EU AI Act —— 法律强制
        └── International AI Safety Reports

2026 年 AI Safety 的关键问题是：
"在 AGI 到来之前，我们能解决对齐问题吗？"
```
