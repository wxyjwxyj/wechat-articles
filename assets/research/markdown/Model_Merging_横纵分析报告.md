# 模型合并 横纵分析报告

> 两三个微调模型的权重加在一起，得到一个同时会写代码和写小说的新模型——不需要数据、不需要 GPU、几秒钟完成。开源社区 2023 年底偶然发现了这件事，然后论文在半年后才追上来解释"为什么它不应该能工作却偏偏能"。模型合并可能是 AI 社区史上"实践倒逼理论"最极致的案例。

---

## 一、一句话定义

模型合并（Model Merging）是在不重新训练的情况下，将多个从同一基座微调而来的 LLM 权重通过算法组合成一个新模型的技术。核心操作单元是**任务向量**（Task Vector）= 微调后权重 - 基座权重——所有的合并方法本质上都是在做"如何安全地把多个任务向量加回基座权重"。

> 🎯 **读完这篇你能**：理解模型合并为什么能工作、TIES/DARE/SLERP/Evolutionary 各自解决什么问题、能判断一个合并模型用了什么配方、理解从"社区炼丹"到"学术化"的全过程。

---

### 阅读指南

**5 分钟**：一句话定义 + 阶段 3.4（转折点）+ 横纵交汇（三个剧本）

**25 分钟**：加技术背景 + 纵向分析各阶段开头 + 横向对比表 + 著名合并模型表

**专业**：全文

---

## 二、技术背景

> 前置知识请参考 [《模型合并前置知识》](./Model_Merging_前置知识.md)

所有微调模型共享同一个预训练基座。从权重角度看，它们都在基座附近的参数空间里——距离基座通常在数百到数千的 L2 范数，而基座权重本身的范数在百万级别。这意味着微调只改变了参数空间中极小的一块，且不同微调的改变之间大部分不重叠。

这解释了为什么合并能工作：**多个任务向量叠加时，它们之间的冲突（同一参数被不同方向拉扯）远少于直觉预期。** 但冲突确实存在。所有"高级"合并方法——TIES、DARE、Model Stock——本质上都在解决同一个问题：怎么处理那些被多个任务向量"往不同方向拉"的参数。

---

> **📚 关联报告**
> - [PEFT 参数高效微调](./PEFT_参数高效微调_横纵分析报告.md) — LoRA 微调是模型合并的主要源模型生产方式
> - [LLM 应用框架](./LLM应用框架_横纵分析报告.md) — MergeKit 是模型合并的事实标准工具

---

## 三、纵向分析：从偶然发现到学术显学

### 3.1 学术前史（2021-2023.06）

社区发现模型合并之前，学术界已经有零星探索，但都在视觉模型上，LLM 社区完全没注意到。Model Soups (Wortsman et al., ICML 2022) 证明了同一基座的不同微调模型简单平均能提升 CLIP/ViT 精度。Task Arithmetic (Ilharco et al., ICLR 2023) 提出了"任务向量"的代数框架。TIES-Merging (Yadav et al., NeurIPS 2023) 从数学上解释和解决了合并中的参数冲突问题。

这些论文后来成为模型合并的理论基石——但它们在发表时，对 LLM 社区的影响力几乎为零。

### 3.2 社区"偶然发现"（2023.09 - 2023.12）

2023 年 7 月 Llama 2 开源，社区开始大量微调。到 9-10 月，HuggingFace 上有了几十个针对不同用途微调的 Llama 2 变体。

**LostRuins**（koboldcpp 作者）写了第一个通用 LLM 权重合并脚本 LM-Mixer。**Digitous** 在此基础上加了 SLERP。**Undi95** 写了 SLERP-MergeTest 专门测试。Reddit r/LocalLLaMA 是核心传播阵地，HuggingFace Open LLM Leaderboard 提供了即时验证——合并完立刻跑 benchmark 看分数。

2023 年 11 月，**Goliath-120B**——两个 Llama 2 70B 拼成的 frankenmerge——轰动社区。它没有什么理论基础，就是"把模型拼起来"，但结果让人震惊。

同月，阿里巴巴达摩院发表了 DARE / "Language Models are Super Mario"——第一个专门针对 LLM 合并的论文。论文发现随机丢弃 90%+ 的 delta 参数，合并后性能不降反升。这说明微调产生的参数变化极度冗余。

### 3.3 工具化爆发（2024.01 - 2024.03）

**Charles Goddard** 创建了 mergekit，统一了所有社区合并方法到一个 Python 包。

**2024 年 1 月 8 日**，Maxime Labonne（mlabonne）发表了博客 "Merge Large Language Models with mergekit"。这篇博客用清晰可复现的代码教会了整个社区怎么合并模型。Labonne 同时发布了 Marcoro14-7B-slerp，成为最早在 Leaderboard 上引发关注的合并模型。

**2024 年 3 月是转折月。** 3 月 19 日，Arcee AI 收购 mergekit，Charles Goddard 加入 Arcee。同日，MergeKit 论文和 Sakana AI 的 Evolutionary Model Merging 论文同时上线 arxiv。这标志着模型合并从"社区炼丹"正式进入"有论文支撑的学术范式"。

Evolutionary Merging 的发现尤其惊人：用进化算法自动搜索最优合并配方，在多个 benchmark 上超越了人类手工调参的最好结果。这意味着——**连"怎么合最好"这件事，AI 也能比人做得好。**

### 3.4 学术化与主流化（2024.08 - 2026）

2024 年 8 月首个全面综述论文出现，整理了近 100 种合并方法。NeurIPS 2024 正式设立 LLM Merging Competition。2025 年安全合并、多模态合并、遗忘合并等新方向爆发。Sakana AI 的 M2N2（2025.08）引入"竞争与吸引"机制。2026 年 ICLR 收录多个合并论文。

### 3.5 阶段总结

| 阶段 | 时间 | 核心特征 | 标志事件 |
|------|------|---------|---------|
| **学术前史** | 2021-2023.06 | 视觉模型探索，LLM社区不知 | Model Soups, TIES-Merging |
| **社区爆发** | 2023.09-12 | 偶然发现，全民炼丹 | Goliath-120B, DARE论文 |
| **工具化** | 2024.01-03 | mergekit统一，学术化转折 | Labonne博客, Arcee收购, 进化合并 |
| **主流化** | 2024.08-2026 | 综述、竞赛、多模态 | NeurIPS竞赛, M2N2, 安全合并 |

---

## 四、横向分析：合并方法对比

### 4.1 总览表

| 方法 | 提出 | 核心思路 | 需要数据？ | 计算开销 | 合并质量 | 工具 |
|------|:----:|---------|:--------:|:---:|:---:|------|
| **Linear Soup** | 2023.Q3 | 权重直接平均 | 否 | 极低 | 中 | MergeKit |
| **SLERP** | 2023.Q4 | 球面大圆弧插值 | 否 | 低 | 中-高 | MergeKit |
| **Task Arithmetic** | 2022.12 | 任务向量加减 | 否 | 低 | 中 | MergeKit |
| **TIES** | 2023.06 | Trim→Elect→Disjoint | 否 | 中 | 高 | MergeKit |
| **DARE** | 2023.11 | 随机丢弃90%+delta, rescale | 否 | 低-中 | 高 | MergeKit |
| **DARE-TIES** | 2024.Q1 | DARE稀疏化后再TIES | 否 | 中 | **极高** | MergeKit |
| **Model Stock** | 2024.03 | 几何投影法,2模型逼N模型 | 否 | 中 | 高 | MergeKit |
| **Evolutionary** | 2024.03 | 进化算法自动搜索配方 | 是(评估数据) | 极高 | **最高** | Sakana |
| **Frankenstein** | 2023.11 | 按层拼装不同模型 | 否 | 极低 | 极不稳定 | MergeKit |

### 4.2 关键发现

**DARE-TIES 是社区最常用的生产级配方。** DARE 先稀疏化消除 delta 冗余，TIES 再消解符号冲突。HuggingFace Leaderboard 上绝大多数高分合并模型都采用这一组合。

**Evolutionary Merging 是质量上限最高的方法，但计算开销让大多数人望而却步。** 需要多轮进化评估。

**合并的质量高度依赖"选对源模型"。** 方法差异的影响远小于源模型质量差异。社区经验的共识："garbage in, garbage out."

### 4.3 著名合并模型

| 模型 | 时间 | 方法 | 意义 |
|------|------|------|------|
| **Goliath-120B** | 2023.11 | Frankenstein | 第一个轰动社区，120B |
| **Marcoro14-7B-slerp** | 2024.01 | SLERP | 第一个 Leaderboard 热门 |
| **Beyonder-4x7B-v2** | 2024.Q1 | frankenMoE | 4个7B拼成MoE |
| **Daredevil-8B** | 2024 | DARE-TIES | Llama 3 多微调版合并 |
| **Qwopus-GLM-18B** | 2026.04 | Frankenstein | 跨家族三合一，能力惊人 |

---

## 五、横纵交汇洞察

### 5.1 "为什么它不应该能工作，却偏偏能？"

回看整个纵向线，最诡异的地方在于：2023 年底社区狂热地合并模型时，没有一篇论文能解释为什么这能工作。学术界的 TIES-Merging 已经提出了参数冲突理论，但社区根本不知道这篇论文——他们纯粹是自己试出来"这样能行"的。

DARE 论文 2023 年 11 月才上线。社区在那之前几个月已经在大规模合并了。换句话说：**社区用"先干了再说"的方式，验证了后来论文才会解释的现象。**

### 5.2 合并正在从"技术"变成"产品"

Arcee AI 收购 mergekit，把模型合并嵌入企业产品线。Sakana AI 把进化合并发在 Nature Machine Intelligence。HuggingFace 上每天都有新的合并模型产生。模型合并正在从一种"开源社区的奇怪行为"变成"AI 工具链的标准一环"。

### 5.3 三个剧本

**剧本一（55%）**：合并成为微调后的标准后处理。微调完自动做 DARE-TIES 合并来组合能力，工具链全自动化。

**剧本二（30%）**：跨家族合并突破。目前所有方法都要求同基座。如果有方法能可靠地跨家族合并（Llama + Mistral + DeepSeek），格局会彻底改变。

**剧本三（15%）**：合并被下一代微调方法取代。如果 LoRA 的进化版天生支持多任务动态组合，就不需要合并了。

---

## 六、信息来源

| 论文/来源 | URL | 发表时间 |
|-----------|-----|:---:|
| TIES-Merging (NeurIPS 2023) | arxiv.org/abs/2306.01708 | 2023.06 |
| DARE / Super Mario (ICML 2024) | arxiv.org/abs/2311.03099 | 2023.11 |
| Model Soups (ICML 2022) | arxiv.org/abs/2203.05482 | 2022.03 |
| Task Arithmetic (ICLR 2023) | arxiv.org/abs/2212.04089 | 2022.12 |
| Model Stock (ECCV 2024) | arxiv.org/abs/2403.19522 | 2024.03 |
| Evolutionary Model Merging | arxiv.org/abs/2403.13187 | 2024.03 |
| MergeKit paper | arxiv.org/abs/2403.13257 | 2024.03 |
| Model Merging Survey | arxiv.org/abs/2408.07666 | 2024.08 |
| MergeKit GitHub | github.com/arcee-ai/mergekit | 2023.12 |
| Maxime Labonne blog | mlabonne.github.io | 2024.01 |
| Sakana AI evolutionary-model-merge | github.com/SakanaAI/evolutionary-model-merge | 2024.03 |

---

*本文是横纵分析系列的第 39 篇报告。*
