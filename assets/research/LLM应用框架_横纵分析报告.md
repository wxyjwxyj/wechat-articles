# LLM 应用框架横纵分析报告

> 从 LangChain 到 Dify，从 Chain 到 Agent，从"写代码编排"到"拖拽搭建"，LLM 应用框架如何定义了什么叫做"AI 原生应用"。

---

## 一、一句话定义

LLM 应用框架是**为构建基于大语言模型的应用程序而设计的开发工具和运行时环境**。它的核心矛盾在于：底层的 LLM API 只提供"一问一答"的能力，但真实的应用需要检索、记忆、工具调用、多步推理等复杂编排——框架在这个"API 的简单性"和"应用的复杂性"之间架起桥梁。

> 🎯 **读完这篇你能**：在 LangChain、LlamaIndex、Dify 之间做出合理的框架选型，理解代码编排式框架和可视化搭建式平台各自的适用场景与能力边界。

---

## 二、技术背景

### 核心矛盾：LLM API 太简单，应用太复杂

2022 年末 ChatGPT 引爆浪潮后，开发者很快发现一个尴尬的事实：**裸调 OpenAI API 能做演示，但做不了产品。**

一个真实的 AI 应用需要的远不止"发送 prompt → 接收回复"：

- **RAG**：从大量文档中检索相关内容
- **工具调用**：让 LLM 能搜索、计算、查询数据库
- **记忆管理**：多轮对话的上下文保持
- **Agent 循环**：LLM 自主决定下一步做什么
- **评估**：如何判断输出质量

这些能力分散在不同技术栈中，每个都需要大量基础设施代码。LLM 应用框架的出现就是把这些"通用基础设施"标准化，让开发者把精力放在业务逻辑上。

> 前置知识请参考独立文档 [《LLM应用框架_前置知识》](LLM应用框架_前置知识.md)，涵盖 Agent、Pipeline、Memory、Tool 等基础概念的通俗讲解。

---

> **📚 关联报告**
> - [AI Agent](./AI%20Agent_横纵分析报告.md) — Agent 是 LLM 应用框架从 Chain 向 Agent 演化的核心驱动力
> - [Prompt Engineering](./Prompt_Engineering_横纵分析报告.md) — 框架通过模板和提示管理封装了 Prompt Engineering 的最佳实践
> - [RAG](./RAG_横纵分析报告.md) — RAG 是几乎所有 AI 应用中的检索基础设施，框架集成的主要能力
> - [Context Engineering](./Context_Engineering_横纵分析报告.md) — 上下文管理是框架的核心难题，Context Engineering 提供系统方法论

## 三、纵向分析：从 Chain 到 Agent 的演化

### 3.1 萌芽期：做第一个"LLM 应用"的人（2022.10-2023.03）

LLM 应用框架的历史起点非常精确——2022 年 10 月，Harrison Chase 发布了 LangChain。

当时的背景：GPT-3.5 刚发布，ChatGPT 尚未推出（2022.11），开发者群体刚刚开始尝试用 LLM API 构建应用。Harrison Chase 当时在机器学习初创公司 Robust Intelligence 工作，他发现每次构建 LLM 应用都要重复写 prompt 模板、上下文管理、工具集成这些代码——为什么不做成一个库？

几乎同时（2022.11），Jerry Liu 发布了 GPT Index（后更名为 LlamaIndex），最初定位极为专注——**解决"怎么把私有数据喂给 LLM"这个具体问题**。当时 GPT-3 的 4K 上下文窗口放不进一份完整的公司文档，LlamaIndex 做的就是文档分块、索引、检索。

这两者在起点的差异埋下了后来分工的种子：**LangChain 做"流程编排"，LlamaIndex 做"数据检索"。**

**2023 年 3-4 月**是融资爆发期。LangChain Inc. 注册成立，一周内先后获得 Benchmark 的 1000 万美元种子轮和 Sequoia Capital 的 2000 万美元 A 轮，估值至少 2 亿美元。这在当时是一个令人瞠目的估值——LangChain 才发布了 4 个月，没有任何收入。

同期，德国的 **deepset** 公司把 Haystack 从传统 NLP 框架转向 LLM 应用框架——Haystack 早在 2020 年就开源了，最初服务于 BERT 时代的检索和 QA 场景。2023 年的 LLM 浪潮对它来说是一次"老树发新芽"。

**Microsoft** 也在这时入局，发布 Semantic Kernel —— 一个与 Azure 生态和 M365 Copilot 深度绑定的 AI 编排 SDK。

### 3.2 扩张期：框架的"圈地运动"（2023-2024）

2023 年是框架快速迭代、疯狂扩展的一年。

**LangChain** 的 LCEL（LangChain Expression Language）在 2023 年 Q3 推出。LCEL 的宣言式链定义替代了早期命令式的 chain 构建——用 `|` 操作符把组件串在一起。这是一个重要的设计决策：**框架不应该让开发者写大量胶水代码来组合 LLM 能力。**

2023 年 10 月，LangChain 发布 LangServe（部署工具）和 LangGraph（Agent 编排模块）——前者把 LCEL 代码部署为 REST API，后者引入了循环图（Cyclic Graph）来处理 Agent 的"推理→行动→推理"循环。

**LangGraph 是 2024-2026 年间 LangChain 最重要的产品决定。** 它意识到 DAG（有向无环图）链无法处理 Agent 逻辑——Agent 本质上是一个 LLM for-loop，需要循环能力。StateGraph 模块让开发者定义状态对象，节点返回更新，支持 override 和 append 两种模式。

**2024 年 1 月**，LangChain v0.1 稳定版发布，标志着 API 从快速迭代期进入稳定期。同月，LlamaIndex 也正式从 GPT Index 更名为 LlamaIndex（去 OpenAI 绑定），发布完整 RAG 管线支持。

**Dify** 在 2023 年开源发布，走上了完全不同的路——**可视化拖拽**。当 LangChain 和 LlamaIndex 在比谁集成更多、API 更灵活时，Dify 瞄准了一个被忽视的群体：不会写代码的业务团队和产品经理。它的 Prompt IDE、拖拽 Workflow、内置 LLMOps 构成了一套"开箱即用"的完整平台体验。

**Dify 的增长曲线从 2023-2024 年就已经开始加速**——不是因为它的技术更先进，而是因为 AI 应用的决策者不只是工程师，还包括需要快速验证想法的产品团队和业务负责人。

这个阶段形成了 LLM 应用框架的"三国格局"：
- **LangChain**：编排之王，生态最大，Agent 最强
- **LlamaIndex**：检索之王，文档处理最深
- **Dify**：低代码之王，用户量增长最快（2024 年已接近 5 万 stars）

### 3.3 Agent 化：所有框架都在"长出 Agent"（2024-2025）

2024-2025 年是框架的"Agent 化"浪潮。**单次问答已经不够了——框架都在向 Agent 的方向演进。**

**LangGraph** 发布于 2024 年 1 月，成为 LangChain 生态的 Agent 核心。2025 年 5 月，LangGraph Platform GA——提供托管基础设施，用于部署长时间运行、有状态的 Agent。引入 Deep Agents（支持规划、子 Agent、虚拟文件系统）。LangGraph 的 Pregel 式架构（受 Google 图计算模型启发）成为 Agent 编排的事实标准。

**Microsoft 的双框架合并**：2025-2026 年，微软的 AI 编排策略发生重大变化。Semantic Kernel 正式更名为 **Microsoft Agent Framework（MAF）**。AutoGen（微软研究院的多 Agent 对话框架）进入维护模式，新用户直接使用 MAF，现有用户走迁移指南。这是微软内部的一次框架收敛——不再让两个框架竞争，统一到一个企业级产品。

**LlamaIndex** 推出了 Workflows（2025）——它的 Agent 编排模块。LlamaCloud/LlamaParse 商业平台包括 LlamaAgents（端到端文档 Agent 构建）。LlamaParse 支持 130+ 格式，到 2026 年处理了超过 10 亿文档。

**CrewAI**（2024 年发布）走了一条轻量级的多 Agent 协作路线，50k+ stars，独立于 LangChain 实现。它的设计理念是"多 Agent 角色扮演"——每个 Agent 有角色、目标、背景故事。简单得有些"玩具感"，但它的快速增长说明**多 Agent 模式的入门需要比 LangGraph 更低的门槛**。

### 3.4 平台化与收敛：Dify 超越 LangChain，新玩家涌入（2025-2026）

**2026 年是框架格局剧烈变化的年份。**

最令人意外的事件：**Dify 以 140k GitHub Stars 超越 LangChain（103k）**，成为 LLM 应用框架星数第一。Dify 的关键动作：

- **v1.6.0（2025.07）**：开始支持 MCP 协议，是最早一批原生集成的框架之一
- **v1.12.x（2026.Q1）**：推出摘要索引——解决 RAG 检索"断章取义"问题
- **v1.13.0（2026）**：Human-in-the-Loop 人机协作标准——企业级 AI 的关键能力
- **v1.14.0-rc1（2026.04）**：Agent × Skills + 工作流实时协作
- **企业版 + 私有部署**：被大量 GCC（政府/央企）开发者采用，500 万+ 下载量

**LangChain** 在 2025 年 9 月发布 **LangChain 1.0 Alpha**——框架有史以来最大架构重构。新增 Middleware（Agent 中间件层——生产级 Agent 的可观测/拦截/治理）、统一 Content Block（标准化多模态内容表示）、完整的模块化重写。2026 年 Q1 正式 GA。同时，**Deep Agents v0.5** 引入了 Async Subagents（异步子 Agent）、Planning（规划）、Context Isolation（上下文隔离）、Virtual File System（虚拟文件系统）——这是 LangChain 生态在 Agent 能力上最重要的升级。

但 LangChain 的实际 Star 数增长放缓（截至 2026.04 约 103k），低于此前媒体报道的 135k——部分原因是**LangChain API 频繁变动**（v1 迁移涉及 27+ 项 breaking changes）以及**新进入者的分流**。

**2025 年最大的新变量：OpenAI 亲自入场做框架。** 2025 年 3 月发布 **Agents SDK**，10 月 DevDay 发布 **AgentKit**（将 ChatGPT 应用变成 Agent 平台的 SDK），2026 年 4 月升级到 v0.14.0——新增 Sandbox 沙箱环境和 Harness 架构。同期宣布 Assistants API v2 将于 2026 年 8 月关停，全面转向 Agents SDK。这对于所有第三方框架来说是一个明确的信号：**模型厂商正在从"提供能力"向"提供平台"延伸。**

**Google 也入局了。** 2025 年发布 **Agent Development Kit (ADK)**，2026 年 4 月 ADK 1.0 正式发布（Java/Python/Go），2.0 引入 5 种多智能体编排模式，与 Gemini 深度绑定。

**Microsoft 完成框架收敛。** Semantic Kernel → Microsoft Agent Framework (MAF) 1.0，AutoGen 进入维护模式。

**新玩家不断冒出**：Mastra（TypeScript Agent 框架，22k Stars，由 Gatsby 团队创建）、PydanticAI（类型安全 Agent 框架，v1.80+）、Vercel AI SDK 6（2026 年初，Agent Swarm、Streaming Protocol）、HuggingFace smolagents（26k Stars，"用代码思考"）。TypeScript/前端生态正在快速孵化自己的 Agent 框架，开始与 Python 生态的 LangChain/LlamaIndex 形成语言栈分流。

**Haystack** 在受监管行业保持稳定增长——Apple、Meta、NVIDIA、Databricks、Intel 都是企业客户。

**DSPy** 走独特路线——作为编译器而非框架，自动优化 prompt 和 few-shot 示例。学术认可度高（ICLR 2024 Spotlight），34k stars。

到 2026 年，框架格局已经不再是 2024 年的"三国"：

- **Agent 编排**：LangGraph 领先，但 OpenAI Agents SDK 和 Google ADK 在快速追赶
- **检索/文档处理**：LlamaIndex 领先
- **低代码/快速原型**：Dify 领先
- **监管行业**：Haystack 领先
- **企业 .NET 生态**：MAF 领先
- **Prompt 自动优化**：DSPy 独特路线
- **TypeScript/前端 Agent**：Mastra + Vercel AI SDK 崛起中
- **个人 Agent 平台**：OpenClaw（30 万+ Stars，定义新品类，详见 AI Agent 报告）

---

## 四、横向分析：竞争图谱

### 4.1 场景判断

LLM 应用框架是充分竞争市场（场景 C），六个主要框架各自主攻不同方向。

### 4.2 核心框架对比

| 维度 | LangChain | LlamaIndex | Dify | Haystack | MAF | DSPy | OpenAI SDK | Google ADK |
|------|:---------:|:----------:|:----:|:--------:|:---:|:----:|:----------:|:----------:|
| **发布时间** | 2022.10 | 2022.11 | 2023 | 2020 | 2023 | 2023 | 2025.03 | 2025 |
| **创建方** | Harrison Chase | Jerry Liu | LangGenius | deepset | Microsoft | Stanford | OpenAI | Google |
| **GitHub Stars** | 103k | 40k | **140k** | 20k | 30k | 25k | 26k | 20k+ |
| **核心定位** | 编排+Agent | 检索+文档 | 低代码平台 | 审计管线 | 企业.NET | Prompt 编译器 | 官方 Agent SDK | Gemini Agent 开发 |
| **可视化** | ❌ | ❌ | ✅ 拖拽 | ❌ | ❌ | ❌ | ❌ | ✅ (Vertex AI) |
| **Agent 能力** | **最强**(LangGraph) | 中(Workflows) | 强(FC/ReAct) | 中 | 强(多Agent) | 弱 | 强(Sandbox+Harness) | 强(5种编排) |
| **RAG 灵活度** | 高 | **极高** | 高 | 高 | 中 | 通过编译 | 低(依赖模型) | 中 |
| **学习曲线** | 中-高 | 中 | **低** | 中 | 中-高 | 高 | 中 | 中 |
| **商业模式** | LangSmith 付费 | LlamaCloud | Cloud+自托管 | 企业平台 | 微软内部 | 开源免费 | API 按量 | Cloud 绑定 |

### 4.3 Agent 框架详细对比

| 框架 | 发布时间 | 核心机制 | 多 Agent | 状态管理 | 生态关系 |
|------|:-------:|---------|:-------:|:-------:|:----------------:|
| **LangGraph** | 2024.01 | 图编排 (StateGraph) | ✅ | 内建持久化 | LangChain 生态核心 |
| **Dify Workflow** | 2024 | 拖拽 DAG + 代码节点 | ✅ | 可视化 | 独立平台 |
| **CrewAI** | 2024 | 角色扮演多 Agent | ✅ | 有限 | 独立于 LC |
| **OpenAI Agents SDK** | 2025.03 | Handoff + Sandbox + Harness | ✅ | 服务端 | OpenAI 生态 |
| **MAF** | 2023→2026 | Plugin + 流程框架 | ✅ | .NET 生态 | Microsoft 生态 |
| **Google ADK** | 2025→2026 | 5种编排模式 | ✅ | Vertex AI | Gemini 绑定 |
| **LlamaIndex Workflows** | 2025 | 事件驱动 Agent | 发展中 | 有限 | 独立 |
| **AutoGen** | 2023.08 | 多 Agent 对话 | ✅ | 有限 | 维护模式 |

### 4.4 企业能力对比

| 维度 | LangChain | LlamaIndex | Dify | Haystack | MAF |
|------|:---------:|:----------:|:----:|:--------:|:---:|
| 可观测性 | ✅ LangSmith | ❌ 弱 | ✅ 内置 | ✅ Enterprise | ✅ .NET |
| 可审计性 | ❌ 有限 | ❌ 有限 | ❌ 有限 | ✅ **核心优势** | ✅ Enterprise |
| 私有部署 | ✅ 企业版 | ✅ LlamaCloud | ✅ 企业版 | ✅ Enterprise | ✅ Azure |
| MCP 支持 | 发展中 | 发展中 | ✅ 原生 | ✅ Hayhooks | 发展中 |
| 治理/合规 | ❌ | ❌ | ❌ | ✅ | ✅ M365 Copilot |

### 4.5 用户口碑

**LangChain**：社区最大，文档最全，但"过度抽象"的抱怨一直没停过。"用 LCEL 写一个简单的问答都要 3 个 class，有时候直接调 API 更省事"（Reddit）。LangGraph 的 Agent 能力被认为是不可替代的优势。

**LlamaIndex**：检索精度和文档处理能力受认可。"用 LlamaIndex 处理 PDF 比 LangChain 的 Document Loader 好一个数量级"。但 Agent 能力不如 LangChain。

**Dify**：非技术团队的最爱。"我是产品经理，用 Dify 搭了个内部知识库机器人，没写过一行代码。" 但也有开发者抱怨："定制化需求深入一点就发现可视化节点的灵活性不够。"

**Haystack**：受监管行业的信仰之选。"在欧洲银行做 LLM 应用，Haystack 的可审计管线是合规团队唯一接受的方案。" 但社区活跃度不如 LangChain 和 Dify。

**DSPy**：评价两极分化。"用了 DSPy 后我们再也不用自己写 prompt 了" vs "学习曲线太陡，我们的团队适应不了。"

### 4.6 框架成本

| 平台 | 免费版 | 付费版 |
|------|-------|-------|
| **LangSmith** | 5k traces/月 | Plus $39/席位/月 |
| **LlamaCloud** | 400K 信用点/月 | Starter/Enterprise 定价 |
| **Dify Cloud** | 200 消息额度 | Pro $59/月, Team $159/月 |
| **Haystack** | 开源免费 | Enterprise 定制报价 |
| **MAF** | 开源免费 | Azure 费用 |

所有框架本身开源，付费版本主要提供云服务、可观测性、企业级支持。

---

## 五、横纵交汇洞察

### 5.1 Dify 超越 LangChain 意味着什么

2026 年最引人注目的格局变化是 Dify 在 GitHub Stars 上超越 LangChain。这个数字落在"低代码"而非"编排"的框架上，揭示了一个深层趋势：

**AI 应用的决策者和使用者正在从"工程师"扩展到"业务人员"。**

LangChain 的 135k stars 来自 AI 工程师——他们需要编排能力来构建复杂的 Agent 系统。Dify 的 140k stars 来自更广泛的群体——产品经理、业务分析师、GCC 开发者——他们需要的是"不给开发团队增加负担就能做出 AI 应用"的工具。

这不是"低代码取代代码"的故事，而是**AI 应用的需求面在迅速扩大**——能用 Python 写 LangChain 的人就那么多，但需要一个内部知识库机器人的团队有几千倍那么多。

### 5.2 LangChain vs LlamaIndex：分工的建立和模糊

纵向历史中最清晰的模式是 LangChain 和 LlamaIndex 从"重叠"到"分工"的演变。

2022 年末他们几乎是同时出现的，定位有大量重叠（都是 Python 框架、都做 RAG、都做 prompt 管理）。市场上出现了大量 "LangChain vs LlamaIndex" 的对比文章。

但到了 2024-2025 年，行业找到了自然的分工：

- **做检索、索引、文档处理** → 用 LlamaIndex（LlamaParse 的文档解析能力无可替代）
- **做编排、Agent、工具调用** → 用 LangChain/LangGraph

2026 年的状态是"组合式堆栈"——两个框架的兼容性持续改善，实践中常组合使用。LlamaIndex 处理数据后输出结构化的上下文，LangGraph 编排 Agent 流程。

### 5.3 Agent 框架的"收敛还是不收敛"——以及模型厂商的入场

2026 年，Agent 框架出现了一个有趣的分化：
- LangGraph 走"复杂编排"路线，面向需要深度定制的 Agent 系统
- CrewAI 走"简单易用"路线，面向快速原型
- Dify Workflow 走"可视化"路线，面向非技术人员
- **OpenAI Agents SDK + Google ADK 走"模型绑定"路线，面向各自生态内的开发者**

**最值得关注的新变量是 OpenAI 和 Google 亲自入场。** 当模型厂商开始做框架时，独立的第三方框架（LangChain、LlamaIndex、Dify）面临一个两难：跟模型厂商合作还是竞争？如果 OpenAI 的 SDK 足够好，开发者为什么还要用 LangChain？

2026 年的答案是：**因为 LangChain 做的是"模型无关的编排"，而 OpenAI SDK 做的是"OpenAI 最优"。** 企业在做 Agent 时需要的不仅是模型调用——还需要混合多模型（OpenAI + Anthropic + 开源模型）、审计管线、合规治理。这些不在 OpenAI SDK 的范围内。但 OpenAI 通过 Sandbox + Harness 正在逐步侵蚀框架层的价值。

三者面临的不是同一个市场——它们是同一需求的不同抽象层次。正如编程语言有底层（C）、中层（Java/Python）、高层（低代码平台）的层次，Agent 框架也在形成类似的分层：

| 抽象层次 | 典型框架 | 用户群体 |
|:-------:|---------|---------|
| 低级（细粒度控制）| LangGraph | AI 工程师 |
| 中级（声明式）| CrewAI | 全栈开发者 |
| 高级（可视化）| Dify Workflow | 业务人员 |
| 模型绑定（官方 SDK）| OpenAI Agents SDK, Google ADK | 单模型生态开发者 |

### 5.4 微软的"主动收敛"和它的启示

Microsoft 在 2025-2026 年的双框架合并（Semantic Kernel → MAF，AutoGen → 维护模式）是一个有力的对照案例——**当一个公司内部有两个竞争框架时，最可能的结果不是共赢，而是收敛。**

MAF 的定位明确：服务于 .NET 生态和 M365 Copilot 治理。它不打算跟 LangChain 比"谁集成的 LLM 多"，而是绑定 Azure/AI Search/M365——通过生态锁定创造差异化优势。

这给了其他框架一个重要启示：**在充分竞争的市场中，"全能"不如"有钉子的生态位"。** Haystack 选择了审计，MAF 选择了 .NET 企业生态，Dify 选择了视化 + 自托管——走生态位而非全能的路线，反而获得了稳定的增长。

### 5.5 三个未来剧本

**剧本一：框架分化为"模型无关"和"模型绑定"两条线（概率 55%）**

LangChain/Dify/LlamaIndex 守住"模型无关的编排+治理"地盘，OpenAI Agents SDK/Google ADK 在各自生态内成为"第一个试"的框架。企业的技术栈变成：用官方 SDK 做原型验证，用 LangGraph/Dify 做生产部署（需要多模型支持、审计、治理）。

**剧本二：MCP 协议让框架层变薄，竞争力转移到运行时和治理（概率 30%）**

MCP 已成为行业标准——工具和数据源的连接从"框架专用接口"变成"标准接口"。框架的连接器集成价值被稀释，竞争力转移到运行时效率和工作流编排质量。Dify 和 LangChain 1.0 的 Middleware 层适应这个方向，但 OpenAI/Google 通过 Sandbox 也在抢占运行时层面。

**剧本三：框架被 Agent 平台替代（概率 15%）**

抽象框架被更具体的 Agent 平台替代——开发者不再用 LangGraph 代码搭建 Agent，而是用 Agent 平台配置。框架退居"Agent 平台的基础技术提供商"位置。OpenClaw 的爆发和 OpenAI Workspace Agents 的发布都在指向这个方向。

### 5.6 第一性原理追问

LLM 应用框架的终极问题是：**当 LLM 能力足够强时，框架还有必要吗？**

如果未来的 LLM 有 10M token 上下文、原生支持工具调用、内置记忆管理和规划能力——那么今天的框架封装的"让 LLM 能用工具、能检索、能记忆"的功能，会不会变得冗余？

2026 年的答案是：**不会完全消失，但框架的形态会变。** 今天的框架是"给 LLM 补能力"（模型做不到的框架来补），未来的框架是"给 LLM 做治理"（模型能做了，但怎么控制它、审计它、管理它——框架来做）。

这跟数据库的历史类似——SQL 查询优化器越来越强，但 ORM 框架没有消失，而是从"帮你写 SQL"变成了"帮你管理数据模型和迁移"。**框架的演进方向是从"增强能力"到"管理复杂度"。**

---

## 六、信息来源

### 框架官方来源

| 来源 | URL | 访问时间 |
|------|-----|---------|
| LangChain GitHub | github.com/langchain-ai/langchain | 2026-04-30 |
| LangGraph 博客 | blog.langchain.dev | 2026-04-30 |
| LlamaIndex GitHub | github.com/run-llama/llama_index | 2026-04-30 |
| LlamaIndex 网站 | llamaindex.ai | 2026-04-30 |
| Dify GitHub | github.com/langgenius/dify | 2026-04-30 |
| Dify 官网 | dify.ai | 2026-04-30 |
| Haystack GitHub | github.com/deepset-ai/haystack | 2026-04-30 |
| deepset/Haystack 关于页 | deepset.ai/about | 2026-04-30 |
| Semantic Kernel GitHub | github.com/microsoft/semantic-kernel | 2026-04-30 |
| DSPy GitHub | github.com/stanfordnlp/dspy | 2026-04-30 |
| CrewAI GitHub | github.com/crewAIInc/crewAI | 2026-04-30 |
| AutoGen GitHub | github.com/microsoft/autogen | 2026-04-30 |

### 其他来源

| 来源 | URL | 访问时间 |
|------|-----|---------|
| OpenAI Agents SDK 升级 (Sandbox+Harness) | openai.com | 2026-04-30 |
| Google ADK 1.0 发布 | infoq.com | 2026-04-30 |
| LangChain 1.0 Alpha 发布 | langchain.com/blog | 2026-04-30 |
| Dify v1.14.0-rc1 发布 | github.com/langgenius/dify/releases | 2026-04-30 |
| Mastra GitHub | github.com/mastra-ai/mastra | 2026-04-30 |
| PydanticAI v1 | pydantic.dev | 2026-04-30 |
| Vercel AI SDK 6 | vercel.com/blog/ai-sdk-6 | 2026-04-30 |
| MCP 捐赠给 Agentic AI Foundation | anthropic.com/news | 2026-04-30 |
| Forbes AI 50 (2025) | forbes.com | 2026-04-30 |
| HuggingFace smolagents | github.com/huggingface/smolagents | 2026-04-30 |

---

*本文是横纵分析系列的第 17 篇报告。研究方法论参考了由数字生命卡兹克（Khazix）提出的横纵分析法，融合语言学历时-共时分析、社会科学纵向-横截面研究设计、以及竞争战略分析的核心思想。*
