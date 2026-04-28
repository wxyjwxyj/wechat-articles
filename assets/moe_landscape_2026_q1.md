# MoE 模型横向对比研究报告（2026 年 4 月）

> 调研时间：2026 年 4 月 28 日
> 调研范围：主流 MoE 大模型的架构、性能、生态、商业定位

---

## 1. Mixtral 8x7B / 8x22B (Mistral AI)

### 最新版本
Mistral AI 的 MoE 产品线持续演进。最新旗舰为 **Mistral Small 4**（2026 年 3 月），小型模型也不再更新 Mixtral 品牌，统一用 Mistral Small/Medium/Large。

### 架构演进

| 模型 | 发布时间 | 总参数 | 激活参数 | Expert 配置 | 上下文 | 许可证 |
|------|----------|--------|----------|------------|--------|--------|
| Mixtral 8x7B | 2023.12 | 47B | 13B | 8 expert, Top-2 | 32K | Apache 2.0 |
| Mixtral 8x22B | 2024.04 | 141B | 39B | 8 expert, Top-2 | 64K | Apache 2.0 |
| Mistral Small 4 | 2026.03 | 119B | 6.5B | **128 expert, Top-4** | 256K | Apache 2.0 |
| Mistral Large 3 | 2025.12 | 675B | ~41B | MoE | 256K | Apache 2.0 |

### 核心创新
- **SMoE (Sparse Mixture of Experts)**：路由网络将每个 token 分发给 Top-K 专家处理，加权聚合输出
- **Mistral Small 4** 将四个功能（快速聊天、推理、多模态、编程 Agent）统一到一个模型中，通过 `reasoning_effort` 参数切换
- 推理速度优势：Mixtral 8x7B 比 Llama 2 70B 快约 6 倍

### 性能基准
- **Mixtral 8x22B**：MMLU 等基准超越 ChatGPT 3.5
- **Mistral Small 4**：MMLU-Pro 78.0%，MMLU（经典）社区测试 ~91-94%，HumanEval 未公开发布（改用 LiveCodeBench 等更新基准）
- **Mistral Large 3**：HumanEval 92，AIME 2024 73.6

### 优势与劣势
- **优势**：Apache 2.0 完全开源，欧洲数据主权合规（GDPR），推理速度快，模型体积可自部署
- **劣势**：没有 GPT-5/Claude 4 级别的最强旗舰，社区热度不如 Qwen/DeepSeek；Mistral Small 3.1→3.2 显存翻倍被社区抱怨

### 2025-2026 后续发展
- **Le Chat 2.0**（2025.07）：深度研究模式
- **Voxtral**：语音交互
- **Magistral**：多语言推理
- **Codestral 2501**：代码专用模型
- **2026**：未公开新旗舰路线图，当前重心在产品化（Le Chat 平台）

### 商业定位
- Le Chat 平台订阅制，API 定价中等
- 主打欧洲市场和注重数据主权的企业客户
- 开源策略：Apache 2.0，和 Qwen 一样是最宽松的开源许可

---

## 2. DeepSeek-V3 系列

### 版本演进

| 版本 | 发布时间 | 关键特性 |
|------|----------|----------|
| V3 | 2024.12 | 671B 总参数 / 37B 激活，256 路由专家 + 1 共享，Top-8 路由，MLA 注意力 |
| V3.1 | 2025 年中 | 推理增强，反思链（Chain-of-Refinement），门控置信度过滤 |
| V3.2 | 2025.12 | 无限透镜注意力（Infinite Lens Attention），FP8 训练引擎，动态专家共享，显存降 60% |
| V3.2-Specialized | 2025.12 | 专注数学/学术，嵌入符号计算专用核 |
| V4 (Preview) | 2026 年初 | **MoE++** 动态共享，128 专家池，单次激活 4 专家，百万 Token 上下文 |

### mHC 创新（2026.01）
DeepSeek 于 2026 年 1 月发布 mHC（Manifold-Constrained Hyper-Connections），核心思想：
- 将残差连接的映射矩阵**投影到 Birkhoff 多面体**（双随机矩阵流形）
- 通过 Sinkhorn-Knopp 算法约束矩阵每行/每列之和为 1
- **效果**：27B 模型训练中，信号放大从 3000 倍（HC）降至 1.6 倍（mHC），训练额外开销仅 6.7%
- mHC-lite（普林斯顿/UCLA）进一步改进，用 Birkhoff-von Neumann 定理避免 Sinkhorn 迭代

### 训练成本
- V3 训练成本公开报告约 **$5.576M**（278.8 万 H800 GPU 小时），仅使用 2048 块 H800 GPU
- 这一数字震惊业界，因为同级别模型（GPT-4/Llama 3 405B）训练成本估计在 $100M+ 级别

### 性能基准

| 基准 | DeepSeek-V3 | V3-0324 | V3.2 | GPT-4o | Claude 3.5 Sonnet |
|------|:----------:|:-------:|:----:|:------:|:-----------------:|
| MMLU | 85.3-89.2 | - | **88.5** | 87.2 | 88.3 |
| MMLU-Pro | 75.9 | 81.2 | - | - | - |
| HumanEval | 72.8-78.3% | - | **82.6%** | 80.5% | - |
| MATH-500 | 90.2 | 94.0 | **90.2%** | 74.6% | - |
| GPQA Diamond | 59.1 | 68.4 | - | - | - |
| AIME 2024 | 39.6 | 59.4 | - | - | - |
| LiveCodeBench | 39.2 | 49.2 | - | - | - |
| SWE-Bench | - | - | 50.8 | - | - |

### 社区反馈
- **正面**：性价比极高（成本约 GPT 的 1/10），代码能力公认最强开源模型之一，MIT 许可证
- **负面**：V3.1 出现严重"极"字 bug（`极` token 随机插入输出），引发了社区信任危机。官方回应后 V3.2 修复
- 指令遵循能力弱于 Claude（Reddit 用户反馈：要求只输出修改的代码，结果输出了整个文件 3 次）
- 事实性知识（SimpleQA 24.9%）弱于 GPT-4（38.2%）

### 开源生态
- MIT 许可证，HuggingFace 生态最活跃的模型之一
- Transformers v4.50+ 原生支持
- GGUF 量化版本社区维护活跃

### 商业定位
- 极低 API 定价：输入 $0.26/M tokens，输出 $0.39/M tokens
- 中国市场通过 DeepSeek 官网/App，国际通过 API

---

## 3. Qwen MoE 系列（阿里通义）

### 版本演进

| 代际 | 发布时间 | 旗舰模型 | 架构范式 |
|------|----------|----------|----------|
| Qwen2-MoE | 2024.07 | MoE 初代 | 基础 MoE 引入 |
| Qwen2.5-Turbo/Plus | 2024.12 | 细粒度 MoE | 模块化多模态 |
| Qwen3 | 2025.05 | 235B-A22B | Thinking/Non-Thinking 统一，128 专家 8 激活 |
| Qwen3-Next | 2025.09 | **80B-A3B** | 混合注意力（Gated DeltaNet + Gated Attention），512 专家 10 激活 |
| Qwen3.5 | 2026.02 | **397B-A17B** | 原生多模态 Early Fusion + GDN 线性注意力，512 专家 |

### 架构创新对比

| 维度 | Qwen3 (235B) | Qwen3-Next (80B) | Qwen3.5 (397B) |
|------|-------------|------------------|----------------|
| 总参数 | 235B | 80B | 397B |
| 激活参数 | 22B | **3B** | 17B |
| 激活比 | 9.4% | **3.75%** (极致) | 4.28% |
| 专家数 | 128 | 512 + 1 共享 | 512 + 1 共享 |
| 注意力 | GQA | 75% GDN + 25% Gated Attention | GDN + Gated Attention (3:1) |
| 上下文 | 128K | 262K | 262K (可扩展至 1M+) |
| 多模态 | 外挂式 | 纯文本 | **原生 Early Fusion** |
| 训练成本 | - | Qwen3-32B 的 **9.3%** | 成本再降 60% |
| 语言数 | 119 | 119 | **201** |

### 关键创新

1. **混合注意力（Gated DeltaNet）**：Qwen3-Next 首次将线性注意力（O(n) 复杂度）工业落地。3 个 GDN 层 + 1 个 Gated Attention 层交替，长文解码比纯 Transformer 快 19 倍
2. **极致稀疏 MoE**：Qwen3-Next 的 512 专家/3B 激活，激活比 1:50，业界新高
3. **Thinking Budget**：通过 `reasoning_effort` 参数控制推理深度，一个模型同时支持快速回答和深度思考
4. **原生多模态 Early Fusion**：Qwen3.5 的文本和图像在 Token 级别共享同一表示空间，27B 模型超越上代 235B 专用视觉模型

### 性能基准

| 基准 | Qwen3-Next-80B (Instruct) | Qwen3-Next-80B (Thinking) | Qwen3.5-397B |
|------|:------------------------:|:------------------------:|:------------:|
| MMLU | 79.7% | 88.7% | ~87.9% |
| MMLU-Pro | 80.6% | 82.7% | **87.8%** |
| MMLU-Redux | 90.9% | 92.5% | **94.9%** |
| HumanEval | 83.5% | 90.2% | **90.9%** |
| GPQA Diamond | 72.9% | 75.9-77.2% | **88.4%** |
| AIME 2025 | 69.5% | 84.3-87.8% | 91.3% (2026) |
| MATH-500 | - | - | **98.2%** |
| SWE-bench Verified | ~70% (Coder) | 未报告 | **76.4%** |
| LiveCodeBench v6 | 56.6% | 68.7% | **83.6%** |
| IFEval | - | 88.9% | **92.6%** |

### 中文能力优势
- 词表 250K（Qwen3.5），覆盖 201 种语言
- C-Eval 93.0%（Qwen3.5）
- 中文推理和多轮对话能力在开源模型中遥遥领先
- 119 语言支持（Qwen3），特别擅长中文、日文、韩文等亚洲语言

### 社区反馈
- Thinking 模式延迟增加 2-3 倍，thinking tokens 消耗 2000+ 获得 500 token 回答
- H100 上偶发 OOM，需降低 context 长度
- Tool calling 需要 Qwen-Agent 框架包装
- 总体口碑：最稳定的中等规模开源模型，Apache 2.0 许可证最友好

### 商业定位
- Apache 2.0 完全开源
- 阿里云 Model Studio API 可用
- Qwen3.5 开源权重排名 #3（Artificial Analysis Intelligence Index）

---

## 4. Google Gemini 的 MoE 策略

### Gemini 世代架构演进

| 版本 | 发布时间 | MoE 特征 |
|------|----------|----------|
| Gemini 1.0 | 2023.12 | 稠密 Transformer |
| Gemini 1.5 | 2024.02 | **首次引入 Sparse MoE**，推理成本降低 60%+ |
| Gemini 2.0/2.5 | 2025 | 动态专家选择，延迟压缩至 0.8s |
| Gemini 3 Pro | 2025.11 | **万亿参数级 MoE**，Top-2 激活，约 10% 神经元激活 |
| Gemini 3.1 Pro | 2026.02 | MoE 深度优化，约 90% 参数休眠 |
| Gemma 4 (26B) | 2026.04 | **开源 MoE**，128 专家 + 1 共享，激活 8 个 |

### 架构细节
- **门控网络**：轻量级 MLP（约 1 亿参数），与主网络联合训练
- **路由公式**：y = Sum(g_i(x) * E_i(x))，仅对 Top-K 专家求和
- **动态路由**：纯文本任务激活约 30% 专家，多模态任务激活率升至 85%
- **Gemma 4**：128 专家，激活 8 个，26B 总参/4B 激活

### 核心创新
1. **思维签名（Thought Signatures）**：Gemini 3 Pro 在推理关键节点生成加密 Hash，确保多步推理逻辑一致性，复杂代码 Debug 幻觉率降低 40%
2. **可配置思考深度**：`thinking_budget` 参数控制 Low（1-2s）/High（8-15s）模式
3. **原生多模态统一语义空间**：图像 Patch、视频帧、音频图谱与文本 Token 映射到同一向量空间
4. **百万级上下文（1M Token）**：环形注意力 + 之字形环形注意力，Needle In A Haystack 准确率 99%

### 性能基准

| 基准 | Gemini 3 Pro | Gemini 3.1 Pro |
|------|:-----------:|:-------------:|
| MMLU | 91.8% | 92.6% |
| MMLU-Pro | 89.5% | - |
| GPQA Diamond | 91.9% | **94.3%** |
| HLE | 37.5% | **44.4%** |
| **ARC-AGI-2** | 31.1% | **77.1%** (+148%) |
| SWE-Bench Verified | 76.2% | **80.6%** |
| Terminal-Bench 2.0 | 56.9% | **68.5%** |
| BrowseComp | 59.2% | **85.9%** |
| MCP Atlas (Agent) | 54.1% | **69.2%** |

> HumanEval 未公开（Google 改用 SWE-Bench、LiveCodeBench Pro 等更现代的基准）

### 基础设施
- 完全基于 Google 自研 **TPU Pods**，不依赖 NVIDIA GPU
- JAX + ML Pathways 框架
- API 定价：$2.00/M input tokens, $12.00/M output tokens（与 GPT-4o 同价）

### 与 DeepSeek/Mixtral 的差异
- Google MoE 是**闭源的**，但通过 Gemma 4 开始走开源路线
- 原生多模态（训练即融合）而非后期拼接
- 硬件全自研（TPU），不需要 NVIDIA GPU
- 推理时稀疏性更激进（~10% 激活 vs DeepSeek/Qwen 的 ~5-12%）

---

## 5. OpenAI GPT-4 的 MoE 传闻

### 泄漏信息（2023 年中）

**OpenAI 从未官方确认 GPT-4 架构。** 两大泄漏源：

**泄漏 1 -- George Hotz（2023.06）**
- GPT-4 是 **8 个 expert 模型，每个 220B 参数**
- 总参数约 1.76 万亿
- 16-iteration 推理

**泄漏 2 -- SemiAnalysis（2023.07）**
- **~1.8 万亿参数**，120 层 Transformer
- **16 个 expert**，每个约 111B（MLP）
- 每次前向传播路由到 **2 个 expert**
- ~55B 共享参数（注意力部分）
- 每次生成仅激活约 **280B 参数**（vs 1.8T 全量）
- 训练数据：~13 万亿 tokens
- 推理集群：128 GPU（8-way TP + 16-way PP）

### GPT-5 传闻（2025-2026）

搜索结果中有大量声称 GPT-5 发布的信息，但**来源可疑**（AI 生成的内容农场居多）：
- 声称 GPT-5 于 2025.08 发布
- 声称 GPT-5.4（2026.03）和 GPT-5.5（2026.04）已发布
- 这些信息**无法从可靠来源验证**，建议当作推测看待

### 保密原因
Hotz 和 SemiAnalysis 都认为 OpenAI 隐藏架构不是因为技术有多神奇，而是因为实现思路直白：**"花 8 倍的钱，你也能复制"**。

---

## 6. Anthropic 为何不用 MoE

### 官方立场
Anthropic **从未公开确认或否认 Claude 使用 MoE**，但从其技术路线和学术定位可以明确判断 Claude 全系列使用 **Dense 架构**。

### 核心理由分析

#### 1. 训练稳定性
Dense 架构不会出现 MoE 的经典"专家坍塌（Expert Collapse）"问题：少数专家垄断所有任务，多数专家闲置，路由失效。

#### 2. 输出连贯性
Claude 定位是**长文档分析、法律文本、学术写作、复杂逻辑推理**。Dense 架构全参数激活，所有参数协同工作，不会出现 MoE 中不同专家输出风格不一致导致的"拼凑感"。

#### 3. 安全对齐
Anthropic 以 Constitutional AI 闻名。Dense 架构在对齐方面有天然优势：
- 所有参数协同，便于全局 RLHF 微调
- MoE 中不同专家可能学出不同行为模式，对齐训练更困难
- Claude 3 Opus 在 "alignment faking" 研究中表现出独特的复杂对齐特性，这种特性在 Dense 架构中更容易研究和控制

#### 4. 工程简单性
Dense 架构成熟稳定，不需要解决路由设计、负载均衡、专家并行通信开销、推理动态批处理等 MoE 专有问题。对 Anthropic 这样重视安全性和可控性的公司，工程简单 = 更少不确定性 = 更低出错风险。

#### 5. 推理延迟
MoE 虽然激活参数少，但专家路由引入了额外延迟。Claude 需要保证长上下文的低延迟体验。

### 对比总结

| 维度 | Dense (Claude) | MoE (GPT-4/Mixtral/Qwen) |
|------|:-------------:|:------------------------:|
| 训练稳定性 | 高 | 需要额外负载均衡 |
| 输出连贯性 | 全局统一 | 可能有风格断层 |
| 推理速度 | 较慢（全激活） | 快（部分激活） |
| 工程复杂度 | 低 | 高 |
| 安全对齐 | 全局可控 | 专家间行为可能不一致 |
| 适用场景 | 深度推理、长文档 | 高吞吐、专业化任务 |

**结论**：Anthropic 选择 Dense 不是"技术落后"，而是**产品定位（深度推理安全）+ 技术判断（稳定性优先于效率）**的战略选择。

---

## 7. xAI Grok

### MoE 架构演进

| 模型 | 发布时间 | 总参数 | MoE 架构 | 关键数据 |
|------|----------|--------|----------|----------|
| Grok-1 | 2023.11 | **314B** | 8 expert, Top-2 | 8K ctx, Apache 2.0 |
| Grok-1.5 | 2024.03 | ~314B + Vision | 同 Grok-1 | 128K ctx |
| Grok-2 | 2024.08 | 未披露 | MoE | FLUX.1 + 自研 Aurora 图像生成 |
| Grok-3 | 2025.02 | **~2.7T** (估) | MoE | **1M ctx**, Think/DeepSearch |
| Grok-4 | 2025.07 | 未披露 | MoE | 计算量 = Grok-2 的 100x |
| Grok-4 Heavy | 2025.07 | 未披露 | **多 Agent 并行** | 4-5 Agent 协作 |
| Grok-4 Fast | 2025.09 | 未披露 | MoE 统一架构 | 2M ctx |
| Grok-4.1 | 2026.01 | 未披露 | MoE+Agent | 256K ctx，幻觉降低 65% |
| Grok-4.20 | 2026.03 | 未披露 | **4-Agent 辩论** | 2M ctx，行业最低幻觉 |

### 性能基准

| 基准 | Grok-3 | Grok-4 | Grok-4 Heavy | Grok-4.1 |
|------|:------:|:------:|:----------:|:------:|
| MMLU | 87.5% | ~86.6% | - | - |
| MMLU-Pro | 76.5-79.9% | 85-87% | - | **89.3%** |
| HumanEval | 90.9-94.5% | 85.7-92.7% | - | **93.2%** |
| AIME 2025 | 93.3% | 91.7-98.8% | **100%** | - |
| GPQA Diamond | 84.6% | 87.5% | **88.9%** | 67.8% |
| HLE | 5.1% | 25.4% | **50.7%** | - |
| LiveCodeBench | 42.5% | 79.0% | 79.4% | 48.9% |
| ARC-AGI-2 | - | 15.9-16.2% | - | - |
| SWE-Bench | - | 72-75% | - | 51.7% |

### 关键创新
- **多 Agent 辩论架构（Grok-4 Heavy/4.20）**：多个 Agent 并行推理，通过辩论达成共识
- **Scaling Law 践行者**：Grok-4 的计算量是 Grok-2 的 100 倍、Grok-3 的 10 倍
- **Colossus 超级计算机**：20 万 H100 GPU 集群训练 Grok-4
- Grok-4.20 非幻觉率达 **78%**（行业最高），幻觉降低 65%

### 路线图
- Grok-4.4/4.5（2026.05 计划）：1T-1.5T 参数
- **Grok-5（2026）**：6T-7T 参数，Musk 声称"将是 AGI"
- 训练集群：Colossus 2，55 万+ GB200/GB300 GPU

### 商业定位
- X Premium+ 订阅（Grok-4 标准版 $30/月）
- SuperGrok（Grok-4 Heavy $300/月）
- API 集成 Azure 和 Telegram
- Grok-4.20 API：每百万 token $2-$6
- 与 X/Twitter 深度绑定，实时信息检索是独特优势

---

## 8. 其他值得关注的 MoE 模型

### Meta Llama 4（2025.04）

| 模型 | 总参数 | 激活参数 | Expert | 上下文 | 许可证 |
|------|--------|----------|--------|--------|--------|
| **Scout** | ~109B | 17B | 16 | **10M** | Llama 4 CLA |
| **Maverick** | ~400B | 17B | 128 | 1M | Llama 4 CLA |

- Meta 首次拥抱 MoE，放弃 Llama 3 的 Dense 路线
- **iRoPE**：interleaved NoPE + Chunked RoPE 实现极长上下文
- Scout 单张 H100（int4）可运行
- 争议：Benchmark 刷榜嫌疑（LMArena）；许可证非 OSI-open（EU 限制）

### Kimi K2（月之暗面 Moonshot AI，2025.07）

| 指标 | 数值 |
|------|------|
| 总参数 | **1T**（首个开源万亿参数 MoE） |
| 激活参数 | 32B |
| Expert 配置 | 384 + 1 共享，8 激活 |
| 上下文 | 128K -> 256K |
| 许可证 | Modified MIT |

**关键创新**：
- **MuonClip 优化器**：矩阵级优化器，15.5T tokens 零 loss spike，"ML 史上最平滑 loss 曲线"，收敛速度 1.4x AdamW
- **Agentic-native 设计**：SWE-bench Verified 65.8%，AceBench 76.5%
- **Kimi K2 Thinking**：HLE 44.9%，BrowseComp 60.2%
- 原生 INT4 量化

### DBRX（Databricks，2024 初）

| 指标 | 数值 |
|------|------|
| 总参数 | 132B |
| 激活参数 | 36B |
| Expert | 16，Top-4 |
| 上下文 | 32K |

- 首个工业级开源 MoE（2024 年 MoE 浪潮的开端），但已被 2025 年模型全面超越
- 至今仍在 HuggingFace 有活跃的微调使用

### 新兴研究值得关注

1. **S'MoRE（Meta，2025.04）**：LoRA + 层级 MoE 树，16% 更少可训练参数获 +2.1% 精度
2. **Symphony-MoE（2025.11）**：多个独立预训练稠密模型融合为 MoE，无需重训
3. **ADRS/OpenEvolve（UC Berkeley，2025.10）**：AI 在 5 小时内发现新 MoE 负载均衡算法，比人类设计的快 5 倍
4. **Flash-MoE**：397B 参数模型在笔记本上运行（Strix Halo 128GB UMA）

---

## 9. MoE 推理框架生态

### 主流框架对比

| 框架 | 定位 | MoE 关键特性 |
|------|------|-------------|
| **vLLM** | GPU 推理"万金油" | PagedAttention、Continuous Batching、EPLB（专家并行负载均衡）、MRV2（2026.03） |
| **SGLang** | 激进缓存+前沿推理 | RadixAttention 前缀缓存、DeepEP 专家并行、FP4 MoE Kernel（Blackwell 领先） |
| **TensorRT-LLM** | NVIDIA 硬件性能天花板 | FP8/FP4 极致算子优化、In-flight Batching、Scaffolding 推理时计算框架 |

### 专家并行（Expert Parallelism, EP）实现

```
演进路径：
全 TP (Tensor Parallelism)
  → DP + 小 EP (减少 KV-cache 冗余)
     → 大 DP + 大 EP + PP (Pipeline Parallelism)
        → PD 分离 (Prefill/Decode Disaggregation)
```

**关键技术**：
- **EPLB**（vLLM）：动态复制热点专家并跨 GPU 分发
- **DeepEP**（SGLang）：使用 NCCL/RDMA All-to-All 通信，支持 FP8 压缩
- **PD 分离**（DistServe, OSDI 2024）：Prefill 与 Decode 分开部署，4.48x goodput 提升，延迟方差降低 20x

### FP4 MoE Kernel 突破（2026.01，HuggingFace 社区实测）

在单张 Blackwell B200 上运行 GPT-OSS-20B（32 专家 Top-4）FP4 推理：

| 框架 | 峰值吞吐 (BS=4096) | BS=128 延迟/层 | BS=1 延迟/层 |
|------|:-----------------:|:-------------:|:-----------:|
| **SGLang FP4** | **1262 TFLOPS** | 0.433ms | 206.9us |
| FlashInfer FP4 | 1225 TFLOPS | - | 481.9us |
| vLLM FP4 | 1117 TFLOPS | 0.604ms | 369.5us |

- SGLang 比 vLLM 快 **1.32x**（小批次），比 BF16 提升 **3.54x**
- 三个技术差异：Kernel 融合（7 次 kernel launch 降至 5 次）、Blackwell 专用 CUTLASS Schedule、自适应 Grid Sizing

### 2026 年重要新进展

| 进展 | 细节 |
|------|------|
| **vLLM MRV2**（2026.03） | Triton Kernel 直编 PTX，异步调度，输出吞吐 +56%，TPOT 降 6.3% |
| **AIConfigurator**（2026.01） | 跨框架无 GPU 配置搜索，MoE 性能最多提升 50% |
| **TensorRT-LLM Scaffolding** | 推理时计算框架（CoT/BoN/MCTS），三级并发 |
| **NVIDIA GB200 NVL72** | 72 GPU NVLink，130 TB/s 带宽，30TB 共享显存，Kimi K2 获 10x 性能提升 |

### 部署选择指南

| 场景 | 推荐框架 |
|------|----------|
| 通用部署、快速上手 | vLLM |
| 极致性能、前沿优化 | SGLang |
| NVIDIA 硬件极致压榨 | TensorRT-LLM |
| 需要 PD 分离 | SGLang + 自建 PD 分离 |
| Blackwell 硬件 | SGLang（FP4 领先） |

**核心洞察**：MoE 推理的整体 MFU（Model FLOPs Utilization）距理论上限仍有 **2-3 倍**差距，算子优化、显存管理、并行策略和调度算法四个方向在 2026 年仍将持续快速迭代。

---

## 综合对比总表

### 旗舰模型架构对比（截至 2026.04）

| 模型 | 公司 | 总参数 | 激活参数 | Expert 配置 | 上下文 | 架构 | 开源 | 发布 |
|------|------|--------|----------|------------|--------|------|------|------|
| **Qwen3.5-397B** | 阿里 | 397B | 17B | 512+1 / 10 激活 | 262K | MoE + GDN | Apache 2.0 | 2026.02 |
| **DeepSeek-V3.2** | DeepSeek | 685B | 37B | 256+1 / 8 激活 | 128K | MoE + MLA | MIT | 2025.12 |
| **Kimi K2** | 月之暗面 | 1T | 32B | 384+1 / 8 激活 | 256K | MoE + MuonClip | Modified MIT | 2025.07 |
| **Mistral Large 3** | Mistral | 675B | ~41B | MoE | 256K | MoE | Apache 2.0 | 2025.12 |
| **Mistral Small 4** | Mistral | 119B | 6.5B | 128 / 4 激活 | 256K | MoE + VLM | Apache 2.0 | 2026.03 |
| **Qwen3-Next-80B** | 阿里 | 80B | 3B | 512+1 / 10 激活 | 262K | MoE + GDN | Apache 2.0 | 2025.09 |
| **Llama 4 Maverick** | Meta | ~400B | 17B | 128 / 多激活 | 1M | MoE | CLA (受限) | 2025.04 |
| **Gemma 4-26B** | Google | 26B | 4B | 128+1 / 8 激活 | 256K | MoE + VLM | Apache 2.0? | 2026.04 |
| **Grok-4 Heavy** | xAI | 未披露 | 未披露 | MoE + Multi-Agent | 1M+ | MoE + Agent | 闭源 | 2025.07 |
| **Gemini 3.1 Pro** | Google | ~1T+ | ~100B | MoE / Top-2 | 1M | MoE + 多模态 | 闭源 | 2026.02 |
| **GPT-4** (传闻) | OpenAI | ~1.8T | ~280B | 16 / 2 激活 | 32K | MoE | 闭源 | 2023 |
| **Claude Opus 4.5** | Anthropic | 未披露 | 全量 | **Dense (非 MoE)** | 200K | Dense | 闭源 | 2025 |

### 关键基准性能对比（选择代表性最强版本）

| 模型 | MMLU-Pro | HumanEval | SWE-Bench | GPQA | AIME 2025 | HLE |
|------|:--------:|:---------:|:---------:|:----:|:---------:|:---:|
| **Gemini 3.1 Pro** | 89.5% | - | **80.6%** | **94.3%** | - | 44.4% |
| **Grok-4 Heavy** | ~86% | ~92% | ~74% | 88.9% | **100%** | **50.7%** |
| **Qwen3.5-397B** | 87.8% | 90.9% | 76.4% | 88.4% | 91.3% (2026) | - |
| **DeepSeek-V3.2** | - | 82.6% | 50.8 | - | - | - |
| **Qwen3-Next-80B (T)** | 82.7% | 90.2% | ~70% (Coder) | 77.2% | 87.8% | - |
| **Mistral Large 3** | 73.1% | 92% | - | - | 73.6 | - |
| **Mistral Small 4** | 78.0% | - | - | ~74% | 匹配 GPT-OSS 120B | 9.5% |
| **Claude Opus 4.5** | ~88% (估) | - | 72% (估) | ~85% (估) | - | - |

> 注意：不同时间点、不同测试条件下 benchmark 不可直接对比，以上数据仅供参考趋势。标注 `(T)` 为 Thinking 模式，标注 `(估)` 为间接推断值。

### 市场定位与定价对比

| 模型 | 开源 | API 定价 (每 M tokens) | 主要市场 |
|------|:----:|:----------------------:|----------|
| **DeepSeek-V3.2** | MIT | $0.26 in / $0.39 out | 中国 + 国际，极低价格 |
| **Qwen3.5-397B** | Apache 2.0 | 阿里云标准价 | 中国为主，全球开发者社区 |
| **Mistral 系列** | Apache 2.0 | 中等 ($1/6 in/out) | 欧洲，GDPR 合规 |
| **Gemini 3.1 Pro** | 闭源 | $2 in / $12 out | 全球，Google Cloud 生态 |
| **Grok-4** | 闭源 | $2-6 / M tokens | X/Twitter 生态，美国 |
| **Claude Opus 4.5** | 闭源 | $15 in / $75 out | 全球，安全/企业 |
| **Llama 4** | CLA (受限) | 自部署 | 全球，Meta 生态 |
| **GPT-4** | 闭源 | ~$10 in / ~$30 out | 全球，OpenAI 生态 |

---

## 关键趋势总结

1. **MoE 已成为主流架构**：2025 年所有重要的开源 LLM 发布（DeepSeek-V3、Qwen3、Llama 4、Kimi K2、Mistral）全部采用 MoE。Dense 架构在 30B 以上参数级基本上被抛弃（Anthropic 除外）。

2. **极致稀疏是方向**：激活比从 Mixtral 8x7B 的 28%（13B/47B）提升到 Qwen3-Next 的 3.75%（3B/80B），接近 30:1 的极致稀疏。

3. **线性注意力与 MoE 融合**：Qwen3-Next/3.5 的 Gated DeltaNet 代表了 MoE + 线性注意力的新范式，长文效率质的飞跃。

4. **"推理预算"控制**：Qwen3 和 Mistral Small 4 都引入 `reasoning_effort` 参数，统一快速模式和深度思考模式。

5. **Anthropic 是唯一的 Dense 坚守者**：这个选择不是技术落后，而是产品定位驱动的战略决策（安全性、连贯性优先于吞吐效率）。

6. **MoE 推理框架远未成熟**：MFU 距理论上限仍有 2-3 倍差距，未来 1-2 年将持续快速迭代。Blackwell 硬件的 FP4 原生支持和 NVLink 5 的高带宽将加速这一进程。

7. **开源 MoE 正在赶上闭源**：Qwen3.5-397B 的 SWE-bench 76.4% 已非常接近 Gemini 3.1 Pro 的 80.6%，而 DeepSeek-V3.2 的 MATH-500 90.2% 远超 GPT-4o 的 74.6%。

8. **训练成本大幅下降**：从 GPT-4（估计 $100M+）到 DeepSeek-V3（$5.6M）到 Qwen3-Next（Qwen3-32B 的 9.3%），MoE 架构本身就在降低训练成本。
