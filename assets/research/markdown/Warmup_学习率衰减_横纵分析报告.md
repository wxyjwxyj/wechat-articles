# Warmup + 学习率衰减 横纵分析报告

> 它没有提出论文、没有首位作者、没有任何学术加冕——却在 2017 年 6 月被两个团队"独立发明"后，用三年长成了训所有大模型都离不开的基础设施。DeepSeek 用它省显存、GPT-3 用它稳住 175B 的训练、ICLR 2025 说"线性衰减比余弦好"——学习率调度可能是深度学习史上"实践跑在理论前面"最经典的故事。

---

## 一、一句话定义

Warmup（学习率预热）+ 学习率衰减是训练深度学习模型时控制学习率变化曲线的技巧：训练初期从很小线性增到最大值（热车），训练后期从最大值逐步衰减至零或接近零（刹车）。它不是一篇论文的产物，而是 2017 年两个团队几乎同时从不同场景中"踩出"的工程共识。

> 🎯 **读完这篇你能**：理解 warmup 为什么需要、三篇理论解释各自从什么角度出发、Cosine Decay 和 WSD 各自的适用场景、能判断一个训练任务该选什么 LR schedule。

---

### 阅读指南

**5 分钟**：读[一句话定义](#一一句话定义) + [横纵交汇洞察](#五横纵交汇洞察)的最后一部分（三个剧本）

**25 分钟**：加[技术背景](#二技术背景) + [纵向分析](#三纵向分析)的阶段开头 + [横向分析](#四横向分析)的对比表

**专业**：全文

---

## 二、技术背景

> 前置知识请参考 [《Warmup + 学习率衰减 前置知识》](./Warmup_学习率衰减_前置知识.md)

训练神经网络本质上是"调旋钮让错误变小"。学习率（LR）控制每次调多大幅度——太大直接跳过最优解甚至爆炸，太小永远到不了。Warmup 和衰减分别控制训练首尾两端的调节幅度。

需要 warmup 的根本原因在三个层面：
1. **Adam 的二阶矩冷启动问题**（RAdam 论文）：前几百步梯度统计不稳定
2. **Transformer 的梯度层间不平衡**（Xiong et al. 2020）：Post-LN 下浅层梯度远大于深层
3. **参数初始化的无方向状态**：随机初始化的参数需要少量小步探索再加速

---

> **📚 关联报告**
> - [大模型训练](./大模型训练_横纵分析报告.md) — LR 调度是训练超参中最重要的一个
> - [Post-training RL](./Post-training_RL训练基础设施_横纵分析报告.md) — RL 训练中 warmup 同样重要

---

## 三、纵向分析：从踩坑到标配

### 3.1 前史（2012-2015）：只有刹车，没有热车

AlexNet (2012)、VGG、ResNet (2015) 用的都是 **Step Decay**——学习率只能降不能升。ResNet 初始 lr=0.1，第 30 和 60 epoch 各自除以 10。

这个阶段的共识简单粗暴：**训练前期的模型最"可塑"，要用最大 lr 快速探索，越靠近收敛越要小步精调。** Warmup 的思想——训练刚开始用小 lr——和当时的直觉完全相反。

### 3.2 2017 年 6 月：两次独立的"发明"

**2017 年 6 月可能是深度学习训练史上最巧合的一个月。**

Goyal et al. (Facebook) 要干一件没人干过的事——用 8192 的 batch size 训练 ImageNet（常规是 256）。他们发现了 Linear Scaling Rule（batch size 大 K 倍，lr 也应大 K 倍），但这规则只在有 warmup 时才成立。论文里第一次出现 "gradual warmup" 这个说法——前 5 个 epoch，lr 从 0 线性增长到目标值。

同一月，Vaswani et al. (Google) 发布了 Transformer 论文。论文里的 Noam Scheduler 前 4000 步做了一模一样的事——lr 从小线性增长。论文没有解释为什么，只作为训练公式出现："We varied the learning rate over the course of training, according to the formula..."

两篇论文背后是完全不同的动机——Facebook 团队解决的是"大 batch size 不稳定"，Google 团队解决的是"新架构训不收敛"——但结论惊人一致。

### 3.3 BERT 与 GPT-3：Warmup 成为标配（2018-2020）

BERT (2018) 用了前 10000 步线性 warmup + 之后线性衰减到 0，让 "warmup + 衰减" 成为 NLP 训练的默认范式。

GPT-3 (2020) 在 175B 参数上验证了 **Warmup + Cosine Decay** 的组合方案，并成为此后四年所有大模型训练的"黄金标准"。参数量越大，warmup 占总训练步数的比例越关键。

### 3.4 理论的追赶：为什么需要 Warmup？（2019-2020）

实践已经用了三年，理论才终于在三条线上给出解释：

- **RAdam (Liu et al., ICLR 2020)**：Adam 的二阶矩 `v_t` 在样本不足时方差极大，warmup 在它稳定之前压低 lr。RAdam 甚至宣称——把 warmup 内建到优化器里，就可以去掉显式的 warmup 阶段。
- **Post-Norm vs Pre-Norm (Xiong et al., ICML 2020)**：原始 Transformer 的 LayerNorm 位置导致梯度在层间剧烈不平衡，前几层梯度可能达到后几层的几十倍。Warmup 用极小 lr 抑制这种不平衡。后来的 Pre-LN Transformer 降低了对 warmup 的依赖，但未完全消除。
- **训练不稳定的多因素分析 (Liu et al., EMNLP 2020)**：注意力层和 FFN 层的梯度贡献量级不同，warmup 让模型在早期建立合理的参数尺度。

这三篇论文加在一起，warmup 从"黑魔法"变成了"可解释的必要"。但也有人质疑——Ma & Yarats (2019) 证明把 Adam 的 β2 设大到 0.999，warmup 可以省掉。

### 3.5 WSD 与"直降到零"：范式转移（2024-2025）

2024 年，DeepSeek 和 MiniCPM 不约而同地在训练中用了 **WSD（Warmup-Stable-Decay）** 方案——warmup 后不急着衰减，保持恒定 lr 跑完大部分训练，只在尾段快速衰减。

WSD 解决了一个 Cosine Decay 的刚性缺陷：余弦衰减把"总共训多少步"锁死了。如果中途想加训，衰减已经到底。WSD 的中间稳定段随时可截断、评估、续训——对于"训训停停、中途评估、做 ablation 再继续"的大模型研发流程来说，这是质变。

2025 年 ICLR 一篇论文（Bergsma et al.）更激进——通过 scaling law 代理模型实验，证明**线性衰减到零系统性地优于余弦衰减**。如果这个结论被大规模验证，未来 LLM 训练的默认方案可能从 "warmup + cosine decay" 变成 "warmup + stable + linear decay to zero"。

### 3.6 阶段总结

| 阶段 | 时间 | 核心矛盾 | 关键事件 |
|------|------|---------|---------|
| **前史** | 2012-2015 | 只知道降、不知道升 | AlexNet/VGG/ResNet step decay |
| **双源"发明"** | 2017.06 | 大 batch + 新架构都不稳 | Goyal (FB) + Vaswani (Transformer) |
| **标配化** | 2018-2020 | 大模型必须 warmup | BERT → GPT-3 (warmup+cosine) |
| **理论解释** | 2019-2020 | 为什么 warmup 有效？ | RAdam, LN Position, Training Instability |
| **范式转移** | 2024-2025 | 余弦衰减太刚性 | WSD (DeepSeek), Linear to Zero (ICLR) |

---

## 四、横向分析：LR 调度策略对比

### 4.1 总览表

| 策略 | 提出 | 核心理念 | LLM适用性 | 采用度 |
|------|:----:|---------|:---:|:---:|
| **Step Decay** | ~2012 | 每隔 N 步除以 10 | 低 | 仅历史 |
| **Noam** | 2017.06 | warmup + 1/√step 衰减 | 中 | 中 |
| **Cosine Decay** | 2016 | 余弦曲线平滑退火 | 高（曾是标配） | 极高 |
| **Warmup + Cosine** | 2019-20 | warmup + cosine，GPT-3 方案 | 极高 | **极高** |
| **Linear Decay to Zero** | 2025 | warmup + 线性衰减到零 | **极高** | 上升中 |
| **WSD** | 2024 | warmup→stable→decay，可续训 | **极高** | 上升中 |
| **Constant + Cooldown** | 2024 | 全程恒定 + 尾段急刹 | **极高** | 上升中 |
| **ReduceLROnPlateau** | ~2017 | 验证 loss 不动就降 lr | 低（无验证集） | 微调 |
| **Cyclic LR / 1cycle** | 2015/2018 | lr 周期振荡 / 一周期超收敛 | 低 | CV |

### 4.2 关键发现

**Cosine Decay 在过去五年是"默认最优"——但它正在被取代。** 不是因为 cosine 不好，而是因为 WSD 和 Linear to Zero 在保持同等性能的同时提供了更多灵活性。

**LLM 训练中，没有人在用 Cyclic LR 或 ReduceLROnPlateau。** LLM 预训练的特点——一次过、无验证集、巨大 batch size——决定了只有预设固定步数的调度方案才适用。

**三段式结构已经成为新共识。** Warmup（稳定梯度）+ Stable（全速探索）+ Decay（精细收敛）这个框架是各方案的通式。差异只在 decay 阶段用什么函数（余弦/线性/多项式）、占多大比例。

### 4.3 主要 LLM 采用的方案

| 模型 | 年份 | 方案 | 备注 |
|------|:---:|------|------|
| GPT-3 | 2020 | Warmup + Cosine | 定义标准 |
| Chinchilla | 2022 | Warmup + Cosine | 算力最优 |
| LLaMA 1/2 | 2023 | Warmup + Cosine | |
| Llama 3 | 2024 | Warmup + Cosine | 仍保守 |
| DeepSeek V2/V3 | 2024 | **WSD** | 方案切换 |
| MiniCPM | 2024 | **WSD** | 小模型验证 |

---

## 五、横纵交汇洞察

### 5.1 Warmup 为什么没有提出者？

回看整个纵向线，warmup 最独特的性质是——**它不是被"想出来"的，而是被"撞到"的。**

2017 年 6 月两个团队在完全不同的场景下（一个加大 batch，一个换架构），遇到了完全相同的现象（训练初期 loss 爆炸），找到了完全相同的解决办法（前几步用小 lr）。这不是巧合——而是当时深度学习训练已经发展到"传统 step decay 不够用了"的临界点，多个场景同时触发了同一个工程需求。

Warmup 没有提出者，因为它本质上是一个**物理约束**——就像汽车不能零帧起步，神经网络也不能从随机初始化直接全速训练。

### 5.2 调度方案正在从"一条曲线"变成"三段式组装"

Cosine Decay 把 warmup、衰减速率、最终 lr 全部绑在一条曲线上。WSD 把它们拆成三个独立的、可单独配置的阶段。这个拆解的意义在于——不同的训练目标可以对不同阶段独立优化。数据量增加？延长 stable 段。需要更好的收敛？延长 decay 段。Continuous pre-training？直接从 stable 段开始。

### 5.3 三个剧本

**剧本一（60%）：Warmup + Stable + Linear Decay to Zero 成为新默认。** WSD 的灵活 + Linear Decay 的简洁 = 取代 cosine。

**剧本二（25%）：Warmup 在优化器层面彻底消除。** RAdam 方向的研究持续深入，未来的 Adam 变体内建 warmup 效果，训练代码里不再需要显式的 warmup 阶段。

**剧本三（15%）：新训练范式（如 Muon 优化器、分布式训练新方案）让 LR 调度的讨论完全更新。**

---

## 六、信息来源

### 核心论文

| 论文 | 来源 | 发表时间 |
|------|------|:---:|
| Accurate, Large Minibatch SGD (Goyal et al., 2017) | arxiv.org/abs/1706.02677 | 2017.06 |
| Attention Is All You Need (Vaswani et al., 2017) | arxiv.org/abs/1706.03762 | 2017.06 |
| SGDR: Warm Restarts (Loshchilov & Hutter, 2016) | arxiv.org/abs/1608.03983 | 2016.08 |
| RAdam (Liu et al., ICLR 2020) | arxiv.org/abs/1908.03265 | 2019.08 |
| On Layer Normalization (Xiong et al., ICML 2020) | arxiv.org/abs/2002.04745 | 2020.02 |
| Understanding Difficulty of Training Transformers (Liu et al., EMNLP 2020) | arxiv.org/abs/2004.08249 | 2020.04 |
| GPT-3 (Brown et al., 2020) | arxiv.org/abs/2005.14165 | 2020.05 |
| DeepSeek-V3 | arxiv.org/abs/2412.19437 | 2024.12 |
| MiniCPM | arxiv.org/abs/2404.06395 | 2024.04 |
| Straight to Zero (Bergsma et al., ICLR 2025) | arxiv.org/abs/2502.15938 | 2025.02 |
| Scaling Laws Beyond Fixed Durations (Hägele et al., NeurIPS 2024) | arxiv.org/abs/2405.18392 | 2024.05 |
| Why Warmup? (NeurIPS 2024) | arxiv.org/abs/2406.09405 | 2024.06 |
| Reducing Need for Warmup in GPT (Kosson et al., NeurIPS 2024) | arxiv.org/abs/2410.23922 | 2024.10 |

---

*本文是横纵分析系列的第 38 篇报告。研究方法论参考了由数字生命卡兹克（Khazix）提出的横纵分析法。*
