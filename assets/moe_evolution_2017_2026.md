# MoE（混合专家模型）纵向演进研究报告：2017--2026

> 整理时间：2026-04-28
> 覆盖范围：从 Shazeer et al. (2017) 到 Qwen3-Next / DeepSeek-V3.2 (2026.4)

---

## 一、时间线节点详细分析

### 1. Sparsely-Gated MoE (2017.01)

**机构**：Google Brain
**论文**：*Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer* (ICLR 2017)
**作者**：Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, Jeff Dean

#### 核心创新点

- **首次将稀疏 MoE 引入深度神经网络的语言建模任务**，证明可以在不显著增加计算成本的前提下将模型参数扩展到 1000 亿级别
- 提出了 **Noisy Top-K Gating** 路由机制：
  - `G(x) = Softmax(KeepTopK(H(x), k))`
  - `H(x)_i = (x * W_g)_i + StandardNormal() * Softplus((x * W_noise)_i)`
  - 两个可训练权重矩阵 W_g（主路由权重）和 W_noise（噪声项权重）
  - 每次 token 路由到 top-k 个专家（k 通常为 2-4）
  - 通过标准反向传播训练，不需 REINFORCE 强化学习
- **噪声项的作用**：加入高斯噪声增加探索性，防止模型过早收敛到少数专家

#### 负载均衡方案

| 损失函数 | 公式 | 作用 |
|---------|------|------|
| Importance Loss | w_importance * CV(Importance(X))^2 | 鼓励所有专家具有相等的重要性（基于门控输出值总和） |
| Load Loss | 附录 A 中详述 | 确保每个专家处理的 token 数量均衡，避免分布式硬件内存/性能问题 |

#### 分布式训练策略

- **混合数据并行 + 模型并行**：标准层和门控网络用数据并行，专家分布在不同设备上用模型并行
- **利用卷积性解决批次缩小问题**：在语言模型中 MoE 卷积式应用于所有时间步，合并为大批次
- 专家数量可随设备数量成比例增加，每设备内存/带宽需求保持恒定

#### 设计动机

- 解决稠密模型"参数增长必导致计算线性增长"的瓶颈
- 首次将 1991 年的 MoE 概念与深度学习规模化结合

#### 局限与代价

- 辅助损失函数设计与主任务损失存在梯度干扰折衷（aux loss 太大影响性能，太小负载不均衡）
- 静态 Top-K 路由缺乏对负载的动态感知
- 分布式通信开销大（All-to-All），当时未做硬件-算法协同设计
- 没有在大规模生产环境中验证

---

### 2. GShard (2020.06)

**机构**：Google Research
**论文**：*GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding*
**作者**：Dmitry Lepikhin, HyoukJoong Lee, Noam Shazeer 等

#### 核心创新点

- **首次成功将 MoE 规模化应用于 Transformer 架构**，训练了 600B 参数的多语言翻译模型
- **自动分片系统（GShard Annotation API）**：开发者只需标注 tensor 的分片策略，XLA 编译器自动生成 SPMD 并行代码，编译时间 O(1) 与设备数无关
- **Local Group Dispatching**：将输入 tokens 分为 G 个组，每组独立执行路由和派发，将 All-to-All 通信局限在组内，大幅降低跨设备通信开销
- **随机路由（Random Routing）**：Top-1 始终激活，Top-2 按门控权重概率激活，g2 很小时跳过第二个专家，节省计算和通信

#### 架构参数

| 参数 | 值 |
|------|-----|
| 总参数 | 600B |
| 专家数 | 最多 2048 个 / MoE 层 |
| Top-K | 2（第二个随机激活） |
| MoE 层替换方式 | 每间隔一个 FFN 替换为 MoE 层 |
| 硬件 | 2048 TPU v3 |
| 训练时间 | 4 天 |
| 任务 | 100 语言 -> 英语翻译 |

#### 设计动机

- 解决稠密模型的内存墙问题——单设备放不下 600B 参数
- 将参数规模与计算成本解耦：16x 参数增长仅需 3.6x 计算成本
- 算法-系统协同设计的首次大规模验证

#### 局限与代价

- Top-2 路由的随机性使行为不够可预测
- Expert Capacity 硬限制导致 token 溢出时信息丢失（通过残差连接绕过）
- 仅针对机器翻译验证，未验证语言建模等其他任务

---

### 3. Switch Transformer (2021.01)

**机构**：Google Brain
**论文**：*Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity*
**作者**：William Fedus, Barret Zoph, Noam Shazeer

#### 核心创新点

- **简化路由器为 Top-1（k=1）**：每个 token 只路由给概率最高的一个专家。核心洞察：Top-2 路由的第二个专家收益有限，但通信和计算开销翻倍
- **容量因子（Capacity Factor）概念**：`expert capacity = (tokens总数 / 专家数) * capacity_factor`
  - TPU 需要静态张量形状，容量因子调节每个专家处理 token 的上限
  - 实测低容量因子（1.0-1.25）表现已足够好
  - 溢出 token 通过残差连接跳过该 MoE 层
- **三条训练稳定性技巧**：
  1. Selective Precision：router 局部计算用 float32，通信用 bfloat16
  2. 缩小参数初始化：Transformer 默认初始化缩放因子缩小 10 倍
  3. Expert Dropout：微调时对 expert FFN 层用更高 dropout rate

#### 架构参数

| 模型 | 参数 | 专家数 | 加速比 (vs T5) |
|------|------|--------|----------------|
| Switch-Base | 3.8B | 64 | 7x |
| Switch-XXL | 395B | 64 | 4x |
| Switch-C | 1.6T | 2048 | 4x |

#### 设计动机

- 简化 Top-K 路由降低计算和通信成本
- 首次证明万亿参数 MoE 模型可稳定训练
- 使稀疏模型的速度-质量权衡优于稠密模型

#### 局限与代价

- Token dropping 机制导致信息损失（溢出 token 被完全跳过）
- 仅验证了 encoder-decoder T5 架构，未涉 decoder-only
- 辅助损失依然存在梯度干扰
- 微调阶段容易过拟合

---

### 4. GLaM (2021.12)

**机构**：Google
**论文**：*GLaM: Efficient Scaling of Language Models with Mixture-of-Experts* (ICML 2022)
**作者**：Nan Du, Yanping Huang, Andrew M. Dai 等

#### 核心创新点

- **首次在 decoder-only 语言模型中验证大规模 MoE**，定位为"通用语言模型"
- 确立了 **"总参数 >> 激活参数"** 的效率范式：1.2T 总参数，97B 激活

#### 架构参数

| 参数 | 值 |
|------|-----|
| 总参数 | 1.2T |
| 激活参数 | 97B（仅 ~8%） |
| MoE 层数 | 32 |
| 每层专家数 | 64 |
| Top-K | 2 |
| 训练数据 | 1.6T tokens |
| 硬件 | TPU v4 + GSPMD 编译器 |

#### 与 GPT-3 (175B 稠密) 对比

| 指标 | GLaM 1.2T | GPT-3 175B |
|------|-----------|------------|
| 训练能耗 | **1/3** of GPT-3 | 基准 |
| 推理 FLOPs | **1/2** of GPT-3 | 基准 |
| Zero-shot 优势 | **80%** 任务胜出 | -- |
| One-shot 优势 | **90%** 任务胜出 | -- |

#### 设计动机

- 证明 MoE 在 decoder-only 语言模型中可行且高效
- 回应"大模型碳排放"争议——MoE 可以用更少能耗实现更好性能

#### 局限与代价

- 1.2T 参数需要特殊硬件（TPU v4），社区无法复现
- 训练稳定性依赖 GSPMD 编译器，技术栈不开放
- 未开源模型权重
- 专家利用率分析不够深入

---

### 5. ST-MoE (2022.02)

**机构**：Google
**论文**：*ST-MoE: Designing Stable and Transferable Sparse Expert Models*
**作者**：Barret Zoph, Irwan Bello, Sameer Kumar, Nan Du, Yanping Huang, Jeff Dean, Noam Shazeer, William Fedus

#### 核心创新点

- **Router Z-Loss**：解决训练不稳定问题的最关键贡献

  ```
  L_Z(x) = (1/B) * sum_i [log(sum_j exp(x_j^(i)))]^2
  L_total = L_CE + c_B * L_B + c_Z * L_Z
  ```

  Z-Loss 惩罚 router 输出的大 logit 值，防止数值溢出导致的训练崩溃。在 269B 参数模型上实现了零不可恢复 loss spike。

- **系统性稳定性消融实验**：
  - 去掉 GEGLU 或 RMSNorm scaling 改善稳定但显著损害质量
  - Input jitter 和 dropout 也有稳定效果但引入质量退让
  - Z-Loss 是唯一**既不损害质量又显著提升稳定性**的技术

#### 架构参数

| 参数 | 值 |
|------|-----|
| 总参数 | 269B |
| 激活参数 | 等效 32B 稠密 |
| Top-K | 2 |
| 容量因子 | 1.25 |
| MoE 层位置 | 每层一个 expert，中间插入 dense FFN |

#### 微调洞察

- 稀疏模型比稠密模型**更易过拟合**小数据集
- 微调时倾向**更小的 batch size 和更高的学习率**（与稠密模型相反）
- 稀疏模型在迁移学习上表现优秀

#### ST-MoE-32B 表现

- SuperGLUE: 91.2（SOTA）
- 摘要（XSum, CNN-DM）和闭卷 QA 任务均达 SOTA

#### 设计动机

- 解决此前 MoE 模型训练不稳定的核心痛点
- 为 MoE 的大规模产业化提供稳定训练配方

#### 局限与代价

- 三种 loss（CE + Balance + Z）的超参数调优复杂
- 仅 Google 内部复现，未开源实现
- Expert 数量固定（64），未探索更细粒度

---

### 6. GPT-4 MoE 传闻 (2023.03)

**机构**：OpenAI（未官方确认）

#### 背景

- 2023 年 6 月，George Hotz 在播客中爆料 GPT-4 是 8 个 expert 组成的 MoE
- 后续 Yam Peleg 泄露文档称是 16 个 expert，每个 ~111B 参数 MLP

#### 传闻架构参数

| 参数 | Hotz 版 | Peleg 版 |
|------|---------|----------|
| 总参数 | ~1.8T | ~1.8T |
| Expert 数 | 8 | 16 |
| 每 token 激活 | -- | 2 个 expert |
| 激活参数 | ~280B | ~280B |
| 层数 | -- | 120 |
| 训练 tokens | -- | ~13T |
| 训练成本 | -- | ~$63M |

#### 影响

- **GPT-4 的 MoE 架构传闻是 2023 年 MoE 开源爆发的催化剂**
- 直接催生了 Mistral AI 发布 Mixtral 8x7B（2023.12）
- 证明"MoE 不是学术玩具，能做出最强商业模型"

---

### 7. Mixtral 8x7B / 8x22B (2023.12 -- 2024.04)

**机构**：Mistral AI（法国）

#### Mixtral 8x7B (2023.12)

**核心创新点**：

- 首个**高性能开源 MoE 语言模型**（Apache 2.0 许可）
- 采用 **Sliding Window Attention + GQA + RoPE** 组合，创新点在"稀疏专家 + 高效注意力"的工程整合
- 证明了 MoE 可以在消费级硬件部署（FP16 约 90GB，4-bit 量化约 26GB）

**架构参数**：

| 参数 | 值 |
|------|-----|
| 总参数 | 46.7B |
| 激活参数 | ~12.9B |
| Expert 数 | 8 |
| Top-K | 2 |
| 层数 | 32 |
| hidden_size | 4096 |
| 上下文 | 32K（训练 8K，sliding window 扩展到 32K） |
| attention | GQA（32 Q heads / 8 KV heads） |
| Router aux loss coef | 0.001 |

**性能**：匹配/超越 GPT-3.5、Llama 2 70B，推理速度是 Llama 2 70B 的 6x

#### Mixtral 8x22B (2024.04)

**核心变化**：

| 维度 | 8x7B | 8x22B |
|------|------|-------|
| 总参数 | 47B | 141B |
| 激活参数 | 13B | 39B |
| 上下文 | 32K | 64K |
| 层数 | 32 | 56 |
| 每个 expert 规模 | ~7B | ~22B |

**设计动机**：将每个 expert 从 7B 扩到 22B（单个 expert 能力大幅增强），同时保持 8 expert 结构不变，实现"简单放大"

#### 局限与代价

- Router 设计简单（标准 softmax Top-2），无创新
- 辅助损失调优空间有限
- 后续 Mistral 转向 dense 密集模型（Large 2 123B），再回归 Granular MoE（Large 3 675B）
- 在 DeepSeek-V2 发布后性价比优势消失

#### Mistral 后续路线 (2024.07--2025.12)

| 时间 | 模型 | 架构 | 关键变化 |
|------|------|------|----------|
| 2024.07 | Mistral Large 2 | **Dense 123B** | 从 MoE 转向密集，追求稳定性 |
| 2024.11 | Mistral Large 24.11 + Pixtral Large | Dense 124B + 多模态 | 增加函数调用、长上下文 |
| **2025.12** | **Mistral Large 3** | **Granular MoE 675B** | 128 experts/层，256K 上下文，仅激活 41B |

Mistral 的 MoE 路线走了"往返"：MoE -> Dense -> 更先进的 Granular MoE。

---

### 8. DeepSeekMoE / DeepSeek-V2 / V2.5 (2024.01 -- 2024.09)

**机构**：DeepSeek（深度求索）

#### DeepSeekMoE 架构创新 (2024.01)

论文：*Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models*

**三大创新**：

**a) Fine-Grained Expert Segmentation（细粒度专家切分）**

传统 MoE 用少量大 expert（如 8 个 7B 的 expert）。DeepSeekMoE 将每个 expert 进一步切分为更多小 expert，保持总参数不变但增加组合灵活性：
- 更多可能的 expert 组合路径，每 token 激活组合的熵大幅增加
- 每个小 expert 更容易专精于窄领域

**b) Shared Expert Isolation（共享专家隔离）**

设定若干 expert 为"shared"（始终激活，不经 router），处理通用知识（语法、常识），让 routed expert 专注专业化：
- V1：1 shared + 63 routed（激活 1+7=8）
- V2：2 shared + 160 routed（激活 2+6=8）

**c) Auxiliary-Loss-Free Load Balancing（无辅助损失负载均衡）**

论文：*Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts* (2024.08)

核心思路：不在 loss 函数中加惩罚项，而是在 router 输出后、Top-K 选择前加**动态 expert-wise bias**：
- Expert 过载 -> bias -= u（降低被选概率）
- Expert 饥饿 -> bias += u（提高被选概率）
- Bias 仅影响路由，不影响最终加权输出
- **零梯度干扰**——不产生与语言模型主目标的冲突梯度

| 方法 | 负载均衡 | 梯度干扰 |
|------|---------|---------|
| 强 Aux Loss | 好 | 强 |
| 弱 Aux Loss | 差 | 弱 |
| **Loss-Free (DeepSeek)** | 好 | **无** |

#### DeepSeek-V2 (2024.05)

**架构参数**：

| 参数 | 值 |
|------|-----|
| 总参数 | 236B |
| 激活参数 | 21B |
| 共享 expert | 2 个 |
| 路由 expert | 160 个（激活 6 个） |
| 上下文 | 128K |
| 核心创新 | **MLA (Multi-Head Latent Attention)** |

**MLA（多头潜注意力）**：将 KV cache 压缩为低秩 latent vector，对比标准 MHA 减少 93.3%（等效 GQA-2.25 组，约为 GQA 的 1/3~1/7），推理吞吐提升 5.76x

**成本优势**：API 定价仅为 GPT-4 的约 1%（$0.14/$0.28 每百万 token）

#### DeepSeek-V2.5 (2024.09)

- Coder V2 和 Chat V2 合并为统一模型
- AlpacaEval 2.0: 50.5，ArenaHard: 76.2，MT-Bench: 9.02
- 安全综合得分 74.4% -> 82.6%
- MIT 协议开源

#### 设计动机

- 解决传统 MoE 的 knowledge hybridity（知识混叠）和 knowledge redundancy（知识冗余）
- Aux-loss-free 解决梯度干扰的根本矛盾
- MLA 解决长上下文的内存墙

---

### 9. DeepSeek-V3 / V3.1 / R1 / V3.2 (2024.12 -- 2026.04)

**机构**：DeepSeek（深度求索）

#### DeepSeek-V3 (2024.12)

论文：*DeepSeek-V3 Technical Report* (2024.12)

**核心创新**：

| 创新 | 说明 |
|------|------|
| **DeepSeekMoE (升级)** | 256 routed experts，激活 8 个 + 1 shared；Gating 从 Softmax 升级为 Sigmoid |
| **MLA** | KV cache ~70KB/token（同类模型的 1/4--1/7） |
| **FP8 混合精度训练** | 首个超大规模验证 FP8 训练的模型，显存和计算减半 |
| **Multi-Token Prediction (MTP)** | 同时预测多个未来 token，训练信号更密集；推理时 1.8x 加速（投机解码） |
| **DualPipe 算法** | 自定义流水线并行，计算-通信近乎完全重叠 |
| **Multi-Plane 网络拓扑** | InfiniBand + NVLink 混合，跨节点通信与计算重叠 |

**架构参数**：

| 参数 | 值 |
|------|-----|
| 总参数 | 671B |
| 激活参数 | 37B（~5.5%） |
| 共享 expert | 1 |
| 路由 expert | 256（激活 8） |
| 上下文 | 128K |
| 预训练 tokens | 14.8T |
| 硬件 | 2048 H800 GPU |
| **训练成本** | **~$5.58M**（仅 Llama 3 405B 的 ~1/15） |
| 训练稳定性 | 零不可恢复 loss spike，零回滚 |

#### DeepSeek-R1 (2025.01)

论文登上 *Nature* 封面 (2025.09)

**核心创新**：

- **GRPO（Group Relative Policy Optimization）**：替代 PPO，去掉价值网络。同一问题生成一组候选，组内相对排序计算优势值，训练复杂度大幅降低

- **R1-Zero 纯 RL 实验**：完全不用 SFT 数据，仅用规则奖励（准确+格式），模型自主涌现：
  - 自我反思（"Wait, that's an aha moment..."）
  - 自我验证（双重检查）
  - 多路径探索
  - 自适应思考时间

- **三阶段训练**：Cold Start SFT -> Reasoning RL -> 全场景对齐

**性能**：

| Benchmark | R1 得分 | 对比 |
|-----------|---------|------|
| AIME 2024 | 79.8% | 与 o1-1217 相当 |
| MATH-500 | 97.3% | 与 o1 持平 |
| Codeforces | Elo 2029 | 超 96.3% 人类 |

#### DeepSeek-V3.1 (2025.08)

- **混合推理架构**：单模型同时支持"思考"与"非思考"模式
- 输出 Token 数减少 20-50%，但性能持平
- Agent 能力飞跃：SWE-bench 45.4 -> 66.0 (+45%)，Terminal-Bench 5.7 -> 31.3 (5x+)
- 上下文扩展至 128K，支持 100+ 语言

#### DeepSeek-V3.2 (2025.12)

**核心创新**：

**a) DeepSeek Sparse Attention (DSA)**

将注意力复杂度从 O(L^2) 降至 **O(Lk)**（k=2048）：

| 组件 | 功能 |
|------|------|
| Lightning Indexer | 小 FP8 模块，对过往 token 打分 |
| Top-k Selector | 从 128K 上下文中仅选 k=2048 最相关 token |

- 128K 上下文计算量减少 84%，速度提升 1.8x，显存降低 40%

**b) 大规模 RL 扩展**

- RL 计算量 > 预训练 FLOPs 的 **10%**——远超历史比例
- 1800+ Agent 环境，85000+ 复杂指令，涵盖代码/搜索/通用 Agent

**c) V3.2-Speciale**

- IMO 数学奥赛 35/42 金牌，IOI 信息学奥赛 492/600 金牌
- AIME 2025: 96.0%，HMMT 2025: 99.2%

**成本**：$0.42-0.45/百万 token（GPT-5 的 1/25，Claude 4.5 Opus 的 1/62）

---

### 10. Qwen MoE 系列 (2024.07 -- 2026.02)

**机构**：阿里巴巴通义

#### Qwen2 (2024.07)

- 首次在 Qwen 系列引入 MoE + GQA
- Qwen2-57B-A14B：57B 总参数，14B 激活

#### Qwen2.5-MoE (2024.12)

- 优化的负载均衡 + 深度 RLHF 对齐
- Qwen2.5-Max：64 experts，激活子集。Arena-Hard 89.4，超 GPT-4o 和 Claude 3.5 Sonnet
- 支持 **1M 上下文**（渐进式 RoPE 频率插值 + 稀疏注意力）

#### Qwen3-MoE (2025.04-05)

| 模型 | 总参数 | 激活参数 | 特点 |
|------|--------|----------|------|
| Qwen3-30B-A3B | 30B | 3B | 轻量边缘 |
| Qwen3-235B-A22B | 235B | 22B | 128 experts，8 激活 |

**关键架构变化**：

| 维度 | Qwen2.5-MoE | Qwen3-MoE |
|------|-------------|-----------|
| Shared Experts | 有 | **移除** |
| QKV Bias | 有 | **移除** |
| Attention Norm | 标准 | **QK-Norm** |
| 负载均衡 | Per-layer aux loss | **Full-batch global balance loss** |
| Thinking 模式 | 不支持 | **Hybrid Thinking/Non-Thinking** |

**Hybrid Thinking** 四阶段训练：

1. Long-CoT Cold Start（数学/代码问题 + 详细步骤 SFT）
2. Reasoning RL（GRPO，~4000 题）
3. Thinking Mode Fusion（混合 SFT + 特殊 chat template token）
4. General RL（20+ 任务类型全覆盖）

预训练数据：36T tokens（119 语言），蒸馏 pipeline：235B teacher -> 小 student

#### Qwen3-Next / Qwen3-Coder-Next (2025.09 -- 2026.02)

**核心创新：Gated DeltaNet + 超高稀疏 MoE**

**a) 3:1 混合注意力布局**

| 层类型 | 比例 | 机制 |
|--------|------|------|
| Gated DeltaNet (GDN) | ~75% 层 | 线性/循环注意力 O(L*d) |
| Gated Attention | ~25% 层（每 4 层 1 个） | 标准 Softmax 注意力 |

**b) Gated DeltaNet 更新公式**

```
S_t = S_{t-1} * [alpha_t * (I - beta_t * k_t * k_t^T)] + beta_t * v_t * k_t^T
```

- alpha_t（继承 Mamba-2）：门控衰减，全局记忆清除
- beta_t（继承 DeltaNet）：delta 规则更新，精确选择性记忆写入
- S_t：压缩隐状态矩阵（快权重记忆）

**c) 超高稀疏 MoE**

| 参数 | Qwen3-Coder-Next | Qwen3.5 |
|------|------------------|---------|
| 总参数 | 80B | 397B |
| 激活参数 | 3B（~3.7%） | 17B（~4.3%） |
| Expert 数 | 512 | 512 |
| 每 token 激活 | 10 routed + 1 shared | 10 routed + 1 shared |
| 上下文 | 256K | 1M |

**d) 训练稳定性创新**

- Zero-Centered RMSNorm：减去均值再做 RMS 归一化
- 全局负载均衡损失（跨并行组同步统计）
- GSPO/SAPO：序列级/软门控 token 自适应策略优化

**训练成本**：仅等效 dense 模型的 ~9.3%

#### 设计动机

- 从 "MoE vs Dense" 转向 "如何处理 Attention" 为核心架构问题
- 线性注意力解决 O(L^2) 的长文本瓶颈
- 极高稀疏度（3-5% 激活率）最大化 intelligence-per-FLOP

---

### 11. xAI Grok MoE (2024.03 -- 2025)

**机构**：xAI（Elon Musk）

#### Grok-1 (2024.03 开源，Apache 2.0)

| 参数 | 值 |
|------|-----|
| 总参数 | 314B |
| 激活参数 | ~86B |
| Expert 数 | 8 |
| Top-K | 2 |
| 层数 | 64 |
| hidden_size | 6144 |
| attention | 48 Q heads / 8 KV heads |
| 上下文 | 8192 |
| 训练框架 | JAX + Rust 自定义堆栈 |

#### Grok-2 (2025 开源)

| 参数 | 值 |
|------|-----|
| 总参数 | ~270B |
| 激活参数 | ~115B |
| Expert 数 | 8 |
| Top-K | 2 |
| 上下文 | 128K |
| **新增** | Shared FFN 层（类似 DeepSeekMoE） |
| hidden_size | 8192 |

#### 设计特点

- 架构保守：一直保持 8 expert / Top-2 结构，核心 MoE 设计无重大创新
- 差异化在训练数据（X/Twitter 实时数据）和基础设施（孟菲斯 10 万 H100 集群）
- Grok-2 引入 Shared FFN 是对 DeepSeekMoE 策略的跟随

---

### 12. MoE 推理框架演进 (2023--2026)

#### 核心挑战

MoE 推理的特殊难点：
- **内存**：所有权重都要加载（671B），远超单 GPU 显存
- **通信**：All-to-All 跨 expert 通信是瓶颈
- **负载不均衡**：热门 expert 过载，冷门 expert 闲置
- **批处理效率**：小 batch 时 MoE 的稀疏优势消失

#### 三大框架对比 (2025--2026)

| 框架 | 核心技术 | MoE 优化亮点 |
|------|---------|-------------|
| **vLLM** | PagedAttention, Continuous Batching | EP+DP 混合并行，FP4/FP8 量化，V1 架构升级 |
| **SGLang** | RadixAttention (前缀缓存), 结构化生成 DSL | FlashInfer TRT-LLM MoE Runner，前缀缓存 2-5x 吞吐 |
| **TensorRT-LLM** | TensorRT 编译器, In-flight Batching | FP8/FP4 全量化，EP 效率 85-90%，B200 原生优化 |

#### 并行策略演进

```
全 TP -> DP + 小 EP -> DP + 大 EP -> PD 分离 + PP
```

- **Expert Parallelism (EP)**：关键创新。将不同 expert 分布在不同 GPU，token 路由时触发 All-to-All 通信
- **Prefill-Decode Disaggregation**：将 Prefill 和 Decode 分到不同硬件，可带来 6.4x 吞吐提升

#### DeepSeek-V3 部署实测 (H800/H20)

| 框架 | 吞吐 (tokens/s) |
|------|----------------|
| vLLM (2025 初) | ~2K |
| SGLang | ~2K -> 大幅优化 |
| TensorRT-LLM (2025 中) | 11.2K |
| 腾讯一念 (2025) | 14.6K |

---

## 二、完整时间线节点列表

| # | 时间 | 事件 | 机构 | 总参数 | 激活参数 | 专家 | Top-K | 关键创新 |
|---|------|------|------|--------|----------|------|-------|----------|
| 1 | 2017.01 | Sparsely-Gated MoE | Google Brain | 137B | -- | 4-256 | 2-4 | Noisy Top-K Gating, Aux Loss 负载均衡 |
| 2 | 2020.06 | GShard | Google | 600B | -- | 2048 | 2 | 自动分片, Random Routing, Local Group Dispatch |
| 3 | 2021.01 | Switch Transformer | Google | 1.6T | -- | 2048 | **1** | Top-1 简化, 容量因子, Selective Precision |
| 4 | 2021.12 | GLaM | Google | 1.2T | 97B | 64 | 2 | Decoder-only 验证, 1/3 GPT-3 能耗 |
| 5 | 2022.02 | ST-MoE | Google | 269B | ~32B | 64 | 2 | **Z-Loss**, 稳定训练, 微调配方 |
| 6 | 2023.03 | GPT-4 (传闻) | OpenAI | ~1.8T | ~280B | 8-16 | 2 | 商业验证 MoE 可做出最强模型 |
| 7 | 2023.12 | Mixtral 8x7B | Mistral AI | 47B | 13B | 8 | 2 | **首个开源高性能 MoE**, Apache 2.0 |
| 8 | 2024.01 | DeepSeekMoE | DeepSeek | 1.9B-16B | 0.24B-2.8B | 64-160 | 6-8 | Fine-grained segmentation, Shared Experts |
| 9 | 2024.03 | Grok-1 开源 | xAI | 314B | 86B | 8 | 2 | 开源 314B MoE (Apache 2.0) |
| 10 | 2024.04 | Mixtral 8x22B | Mistral AI | 141B | 39B | 8 | 2 | Expert 规模从 7B 扩到 22B |
| 11 | 2024.05 | DeepSeek-V2 | DeepSeek | 236B | 21B | 160 (+2 shared) | 6 | **MLA**, Aux-loss-free, 成本 = 1% GPT-4 |
| 12 | 2024.07 | Qwen2 | 阿里 | 57B | 14B | -- | -- | Qwen 系列首次 MoE |
| 13 | 2024.08 | Aux-Loss-Free Paper | DeepSeek | -- | -- | -- | -- | 动态 bias 替代 aux loss |
| 14 | 2024.09 | DeepSeek-V2.5 | DeepSeek | 236B | 21B | 160 (+2 shared) | 6 | Chat + Coder 合并 |
| 15 | 2024.12 | DeepSeek-V3 | DeepSeek | 671B | 37B | 256 (+1 shared) | 8 | **FP8**, MTP, DualPipe, $5.6M 训练 |
| 16 | 2024.12 | Qwen2.5-MoE | 阿里 | -- | -- | 64 | -- | 1M 上下文 |
| 17 | 2025.01 | DeepSeek-R1 | DeepSeek | 671B | 37B | 256 | 8 | **GRPO**, 纯 RL 推理涌现, Nature 封面 |
| 18 | 2025.04 | Qwen3-MoE | 阿里 | 235B | 22B | 128 | 8 | QK-Norm, Hybrid Thinking, 36T tokens |
| 19 | 2025.08 | DeepSeek-V3.1 | DeepSeek | 671B | 37B | 256 | 8 | 混合推理架构, Agent 能力飞跃 |
| 20 | 2025.09 | Qwen3-Next | 阿里 | 80B | 3B | 512 | 10 | **GatedDeltaNet** 混合注意力 |
| 21 | 2025.12 | Mistral Large 3 | Mistral AI | 675B | 41B | 128 | -- | **Granular MoE**, 256K 上下文 |
| 22 | 2025.12 | DeepSeek-V3.2 | DeepSeek | 671B | 37B | 256 | 8 | **DSA 稀疏注意力**, RL > 10% 预训练 FLOPs |
| 23 | 2026.02 | Qwen3-Coder-Next | 阿里 | 80B | 3B | 512 | 10 | 代码专用, SWE-bench 70.6% |

---

## 三、核心技术趋势总结

### 1. Router 演化

```
Noisy Top-K (2017) -> Top-1 简化 (2021) -> Top-2 回归 (2022+) -> Aux-loss-free bias (2024)
```

从"在损失函数里加惩罚"逐步演进为"在路由机制层面自然平衡"。

### 2. Expert 粒度演化

```
4-8 大 expert (2017-2021) -> 64 expert (2021-2022) -> 160 expert (2024) -> 256-512 expert (2024-2026)
```

"更多更小 expert -> 更灵活组合 -> 更专精"是持续趋势。

### 3. 激活比率持续下降

```
~8% (GLaM 2021) -> ~5.5% (V3 2025) -> ~3.7% (Qwen3-Next 2025)
```

"总参数持续增长，激活参数相对稳定"是核心范式。

### 4. 注意力机制的二次革命

```
标准 Self-Attention (2017-2024)
  -> MLA (DeepSeek, 2024): 压缩 KV cache
  -> DSA (DeepSeek, 2025): O(L^2) -> O(Lk)
  -> GatedDeltaNet (Qwen, 2025): O(L^2) -> O(L*d), 线性注意力
```

MoE 只是解决 FFN 层的稀疏化；注意力层的稀疏/线性化是 2025-2026 的新战场。

### 5. 训练成本数量级下降

| 模型 | 年份 | 训练成本 |
|------|------|----------|
| GPT-3 175B (dense) | 2020 | ~$12M |
| DeepSeek-V3 671B (MoE) | 2024 | **~$5.6M** |
| Qwen3-Next 80B | 2025 | **~9.3% 等效 dense** |

### 6. 开源 vs 闭源格局

- Google (2017-2022)：核心技术创新，但**从未开源**
- Mistral (2023-2025)：**首个开源高性能 MoE**，开创生态
- DeepSeek (2024-2026)：**开源 MoE 技术最前沿**，从 V2 到 V3.2 全开源
- 阿里 Qwen (2024-2026)：**开源最广语言覆盖** MoE
- xAI Grok (2024-2025)：开源但架构偏保守
- OpenAI (2023)：闭源，MoE 细节成谜

---

## 四、参考文献

1. Shazeer et al. "Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer." ICLR 2017. arXiv:1701.06538
2. Lepikhin et al. "GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding." 2020. arXiv:2006.16668
3. Fedus et al. "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity." 2021. arXiv:2101.03961
4. Du et al. "GLaM: Efficient Scaling of Language Models with Mixture-of-Experts." ICML 2022. arXiv:2112.06905
5. Zoph et al. "ST-MoE: Designing Stable and Transferable Sparse Expert Models." 2022. arXiv:2202.08906
6. DeepSeek-AI. "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model." 2024. arXiv:2405.04434
7. DeepSeek-AI. "DeepSeek-V3 Technical Report." 2024. arXiv:2412.19437
8. DeepSeek-AI. "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning." 2025. arXiv:2501.12948
9. DeepSeek-AI. "DeepSeek-V3.2." 2025. arXiv:2512.02556
10. Qwen Team. "Qwen3 Technical Report." 2025.
11. Qwen Team. "Qwen3-Next: Gated DeltaNet + Ultra-Sparse MoE." 2025.
12. xAI. "Grok-1 Open Release." 2024. github.com/xai-org/grok-1
