# RoPE 旋转位置编码 横纵分析报告

> 一个没有 PhD 的中国独立研究者，一篇发布在个人博客上的文章，一个业余时间推导的数学公式——然后被 Meta 的 LLaMA 团队注意到，成为 GPT-NeoX、Falcon、Mistral、Qwen、DeepSeek、Gemma 几乎所有现代 LLM 的标配。RoPE 可能是 AI 时代"好想法来自任何地方"最有力的证明。

---

## 一、一句话定义

RoPE（Rotary Position Embedding，旋转位置编码）是苏剑林 2021 年提出的一种位置编码方法——将 Q、K 向量的维度对在复数空间旋转与位置成正比的角，使 Attention 内积自然只依赖相对距离。它形式上像绝对位置编码一样方便（直接作用在向量上），数学上等价于相对位置编码（内积只依赖位置差）。到 2026 年，几乎所有主流 LLM 都使用 RoPE 或其变体。

> 🎯 **读完这篇你能**：理解 RoPE 为什么"一个人一篇博客就能穿透行业"，能画出位置编码的完整族谱，能说出 PI/NTK/YaRN/LongRoPE 各自解决了什么问题，能判断下一个位置编码的方向。

---

### 阅读指南

**5 分钟**：一句话定义 + 阶段 3.3（LLaMA 转折点）+ 横纵交汇（三个剧本）

**25 分钟**：加技术背景 + 纵向各阶段开头 + 横向对比表

**专业**：全文

---

## 二、技术背景

> 前置知识请参考 [《RoPE 前置知识》](./RoPE_前置知识.md)

位置编码的核心矛盾：**绝对位置编码方便但无法外推，相对位置编码可外推但实现复杂。** RoPE 的优雅在于用一个旋转操作同时实现了两者的优势。

RoPE 的数学关键：高维空间的旋转可以分解为多个独立的 2D 平面旋转。Q 和 K 向量的每两个连续维度看作一个 2D 向量，按频率 θ_d = base^(-2d/D) 旋转。不同频率分量捕获不同尺度的位置依赖——高频（旋转快）捕获近距离，低频（旋转慢）捕获远距离。旋转后的 Q、K 内积只依赖位置差 (m-n)，形成自然的相对位置编码。

---

> **📚 关联报告**
> - [LLM 大模型](./LLM大模型_横纵分析报告.md) — RoPE 是现代 LLM 架构的标准组件
> - [Transformer](./Transformer_横纵分析报告.md) — RoPE 是对 Transformer 原始位置编码的改进
> - [长上下文技术](./长上下文技术_横纵分析报告.md) — PI/NTK/YaRN 是长上下文扩展的核心技术

---

## 三、纵向分析：一个人，一篇博客，一个行业标准

### 3.1 前史（2017-2020）三种方案各有短板

- **Sinusoidal PE**（Vaswani et al., 2017）：固定正弦/余弦。理论上可外推，实践中差
- **Learned PE**（BERT/GPT, 2018）：可学习但长度固定
- **Relative PE**（Shaw et al., 2018; T5, 2019）：可外推但计算复杂

三角矛盾持续到 2021 年。

### 3.2 苏剑林与 RoPE（2021.04）

苏剑林追一科技的 NLP 研究员，个人博客"科学空间"已写了十年。从复数乘法和 2D 旋转矩阵出发，推导出了一个同时满足"绝对形式的便利 + 相对形式的自然外推"的位置编码方案。

2021 年 4 月，他把推导过程发表在博客上，同时上传 arxiv 论文 "RoFormer: Enhanced Transformer with Rotary Position Embedding" (2104.09864)。论文里的模型只有几亿参数——他没有大 GPU 集群。但这不影响想法的质量。

6 月 HuggingFace 合并了 RoFormer，7 月 EleutherAI 发表介绍博文 "Rotary Embeddings: A Relative Revolution"，8 月 GPT-NeoX-20B 成为第一个大规模采用 RoPE 的模型。

同月，Press et al. 发表了 ALiBi。ALiBi 更简单——一行代码，零参数，天然外推。2022 年 BLOOM-176B 用了 ALiBi。此时 RoPE 和 ALiBi 的竞争还不明朗。

### 3.3 LLaMA 的选择（2023.02）——转折点

Meta 在设计 LLaMA 时对比了多种 PE 方案，选了 RoPE。

LLaMA 的成功让 RoPE 产生了不可逆的网络效应。所有基于 LLaMA 微调和衍生的模型自动继承 RoPE。FlashAttention、vLLM、llama.cpp 对 RoPE 做了极致优化——用 RoPE 意味着免费获得这些优化。

ALiBi 最大的背书 BLOOM 性能远不如同期模型。ALiBi 在之后的新模型设计中几乎绝迹。

### 3.4 扩展方案爆发（2023.06-2025）

原版 RoPE 在训练长度外推理退化严重。一系列扩展方案密集出现：

- **PI**（Meta, 2023.06）：等比例缩小所有旋转角
- **NTK-aware**（社区, 2023.07）：高频少缩、低频多缩，社区驱动的天才优化
- **Dynamic NTK**（社区, 2023.07）：根据当前长度动态调整
- **YaRN**（2023.09, ICLR 2024）：PI + NTK + 温度调优，当前主流
- **LongRoPE2**（微软, 2025.02, ICML 2025）：进化搜索最优频率，近乎无损 128K+

这些方案最有趣的特点是——NTK-aware 和 Dynamic NTK 完全来自社区（Reddit 帖子、llama.cpp 讨论），没有论文。

### 3.5 未来可能：NoPE 与混合方案

2024 年 NoPE（无位置编码）论文发现 Causal Attention 本身就包含隐式位置信息。2025 年 NeurIPS 提出 RoPE/NoPE 混合——浅层用 NoPE 捕获长程依赖，深层用 RoPE 精细区分位置。2025 年 Transformer 原作者团队尝试完全丢弃位置编码预训练。RoPE 可能不是位置编码的终点。

---

## 四、横向分析

### 4.1 位置编码完整谱系

| 方法 | 时间 | 类型 | 有参数？ | 外推 | 代表模型 | 现状 |
|------|:---:|------|:---:|:---:|------|------|
| Sinusoidal | 2017 | 绝对 | 否 | 有限 | Transformer | 历史 |
| Learned | 2018 | 绝对 | 是 | 无 | BERT, GPT | GPT 系列仍用 |
| Relative (Shaw/T5) | 2018-19 | 相对 | 是 | 有限 | T5 | 编码器模型 |
| **ALiBi** | 2021.08 | 相对 | 否 | **优秀** | BLOOM, MPT | 基本被淘汰 |
| **RoPE** | 2021.04 | 绝对+相对 | 否 | 中→强(带扩展) | **几乎所有现代LLM** | **事实标准** |
| **NoPE** | 2024 | 无 | 否 | 有限 | 实验性 | 前沿探索 |

### 4.2 RoPE 扩展方案对比

| 方案 | 时间 | 扩展倍数 | 需微调？ | 当前地位 |
|------|:---:|:---:|:---:|------|
| PI | 2023.06 | 2-4x | 推荐 | 基础方案 |
| NTK-aware | 2023.07 | 2-4x | 否(零样本) | 社区首选 |
| Dynamic NTK | 2023.07 | 4-8x | 否 | Qwen/DeepSeek 采用 |
| YaRN | 2023.09 | 8-16x | 推荐(少量) | **当前主流** |
| LongRoPE2 | 2025.02 | 32-128x | 需微调 | 学术前沿 |

### 4.3 谁用 RoPE？（2026 年 5 月）

**用**：LLaMA 1/2/3/4, Mistral 全系, Qwen 全系, DeepSeek 全系, Gemma, Falcon, Yi, GPT-NeoX, Grok-1, Claude

**不用**：GPT-3/4（Learned PE）, BLOOM/MPT（ALiBi）, T5（Relative Bias）, RWKV（非 Transformer）

2023 年之后训练的大模型几乎全部 RoPE。

---

## 五、横纵交汇洞察

### 5.1 一个人的论文，一条不可逆的网络效应

RoPE 的成功路径：个人博客 → arxiv → EleutherAI 背书 → GPT-NeoX 采用 → LLaMA 采用 → **临界点**。每一步升级都是社区"主动选择"的——苏剑林自己没有去游说 Meta。用他的话说："RoPE 被大规模采用，主要是 LLaMA 的功劳。"

这反过来也说明：在 2023 年后的 LLM 生态里，**位置编码的选择已经不是一个独立的技术决策，而是生态绑定**——选 RoPE 意味着所有推理框架零成本支持；选别的就得自己写 kernel。

### 5.2 ALiBi 的反面教材

ALiBi 的问题是：它确实简单，但过于简单了。一个自由度的固定线性惩罚，表达力上限太低。BLOOM 选 ALiBi 是 2022 年的合理判断（当时 RoPE 只在小模型验证过），但 BLOOM 自己没成功，ALiBi 失去了最有力的背书。到 2024 年 RoPE + YaRN 能把上下文扩到 128K 且质量几乎不损失时，ALiBi 的"免费外推"优势也不复存在。

### 5.3 三个剧本

**剧本一（60%）**：RoPE + YaRN/LongRoPE2 继续统治。生态惯性太大。

**剧本二（25%）**：RoPE + NoPE 混合成为新标准。NeurIPS 2025 方向进一步验证。

**剧本三（15%）**：新架构（SSM/线性注意力）不需要位置编码——因为本身状态空间就包含了位置。

---

## 六、信息来源

| 来源 | URL | 发表时间 |
|------|-----|:---:|
| 苏剑林博客：旋转式位置编码 | spaces.ac.cn/archives/8265 | 2021.04 |
| RoFormer 论文 | arxiv.org/abs/2104.09864 | 2021.04 |
| EleutherAI: Rotary Embeddings | blog.eleuther.ai | 2021.07 |
| ALiBi 论文 | arxiv.org/abs/2108.12409 | 2021.08 |
| LLaMA 论文 | arxiv.org/abs/2302.13971 | 2023.02 |
| PI 论文 | arxiv.org/abs/2306.15595 | 2023.06 |
| YaRN 论文 | arxiv.org/abs/2309.00071 | 2023.09 |
| LongRoPE2 论文 | arxiv.org/abs/2502.20082 | 2025.02 |
| NoPE 论文 | arxiv.org/abs/2404.12224 | 2024.04 |
| Rope to Nope and Back (NeurIPS 2025) | arxiv.org/abs/2501.18795 | 2025.01 |

---

*本文是横纵分析系列的第 40 篇报告。*
