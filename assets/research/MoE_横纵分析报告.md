# MoE（混合专家模型）横纵分析报告

> 从 1991 年的"分而治之"到 2026 年 4 月的开源模型"日更"时代，MoE 如何从一个边缘想法变成大模型时代的核心架构选择，又如何在一周之内被敲了四次天花板。

**研究对象**：Mixture of Experts（混合专家模型），AI 模型架构

**类型**：技术/算法

**研究时间**：2026 年 4 月

**方法论**：横纵分析法 — 纵向沿时间轴追溯技术演进，横向对比当下主流 MoE 模型的架构选择

---

### 阅读指南

**如果你只有 5 分钟**：读[一句话定义](#一一句话定义) + [横纵交汇洞察](#五横纵交汇洞察)的最后的话。

**如果你想理解 MoE 但不碰技术细节**：读[技术背景](#二技术背景) + [纵向分析·阶段划分](#311-纵向演进的核心脉络) + [竞争格局概况](#41-竞争格局概况)。

**如果你想读懂整份报告的所有技术概念**：建议先花 15 分钟读 [MoE 前置知识](./MoE_前置知识.md)（22 个概念，零基础友好），再回来看完整报告。

**如果你是研究者/工程师**：直接跳[架构对比表](#42-核心模型架构对比)和[性能对比](#44-性能对比)，纵向分析的 3.5（DeepSeek）和 3.8（中国 MoE 军团）是重点。

---

## 目录

1. [一句话定义](#一一句话定义)
2. [技术背景：读懂 MoE 需要知道的事](#二技术背景)
3. [纵向分析：MoE 三十年演进史](#三纵向分析)
4. [横向分析：2026 年 MoE 竞争图谱](#四横向分析)
5. [横纵交汇洞察](#五横纵交汇洞察)
6. [信息来源](#六信息来源)

---

## 一、一句话定义

**MoE（Mixture of Experts）是一种稀疏模型架构：把一个大模型拆成 N 个"专家"小模型，每个输入 token 只激活其中 K 个（K << N），用"分而治之"换取更高效的模型容量利用。**

它不是某种特定的模型，而是 Transformer 架构中 FFN（前馈网络）层的一种替代方案。MoE 替换了传统 Transformer 中"所有 token 走同一个 FFN"的做法，改为"Router 先看 token 是什么，再决定发给哪几个专家 FFN 处理"。

---

## 二、技术背景

> 这一章的目标是让没有机器学习背景的读者也能理解 MoE 的核心逻辑。如果你已经熟悉 Transformer 和 FFN，可以跳到第三节。

### 2.1 MoE 改了什么

任何大语言模型（GPT、Claude、DeepSeek）都基于 Transformer 架构。一个 Transformer 层由两步交替组成：

```
Token → Attention 层（理解上下文关系）→ FFN 层（存储知识、做变换）→ 下一层
```

Attention 负责"看上下文"——让模型理解"苹果"在"她吃了苹果"和"她买了苹果手机"里分别指什么。FFN 负责"存知识"——研究发现，模型学到的绝大多数事实性知识都存储在 FFN 的权重里。

**MoE 只替换 FFN 层，Attention 保持不变：**

```
原始 Transformer:    Attention → FFN（一个）
MoE Transformer:     Attention → Router → [FFN₁, FFN₂, ..., FFN_N]（N 个专家）
                                              ↓
                                    Router 选 K 个来干活
```

### 2.2 为什么要这么做

直觉很简单：没有人是什么都懂的。你去医院看病，不会一个人看完所有科室，而是挂号台（Router）根据你的症状（token 内容），帮你分配给内科或骨科（Expert）。

如果用传统的稠密（Dense）模型，每个 token 都要激活模型里的全部参数。一个 7B 的模型，处理任何一个词时，70 亿个参数全部参与计算。这很浪费——处理"微积分"这个词时，模型里存"莎士比亚"知识的那些权重也在跑。

MoE 的思路是：让模型容量大幅膨胀（可以有几百个专家），但每次只叫最相关的那几个出来干活。一个 685B 总参数的 MoE 模型，处理一个 token 时可能只激活 37B 参数。

### 2.3 代价

天下没有免费的午餐。MoE 的代价也很直接：

- **显存爆炸**：虽然推理时只算 K 个专家，但所有 N 个专家都必须加载在 GPU 显存里，因为你不知道下一个 token 会落到哪个专家。Mixtral 8x7B 总参数 47B，推理需要 ~94GB 显存，而同等推理速度的 13B 稠密模型只需要 ~26GB。

- **训练不稳定**：Router 和专家一起训练，容易出现"赢家通吃"——少数几个专家变得很忙，其他专家闲置。需要额外的负载均衡机制来防止。

- **通信开销**：在分布式训练中，不同专家分布在不同 GPU 上，token 的路由分发和结果收集会带来额外的通信代价。

- **微调困难**：稀疏模型 fine-tune 时更容易过拟合，量化也更复杂。

**一句话：MoE = 用显存放能力，用稀疏换速度。** 后续三十年的演进，本质就是不断探索如何放大"能力"那一端，同时压制"代价"那一端。

---

## 三、纵向分析

### 3.1 史前时代（1991-2016）：一个超前于时代的想法

MoE 的概念比深度学习本身的爆发早了二十多年。而且，它几乎拥有你能想到的最豪华的作者阵容。

#### 1991：MoE 的诞生

《Adaptive Mixtures of Local Experts》，作者是 Robert Jacobs、Michael Jordan（对，就是篮球界那个 Michael Jordan 的同名人，伯克利的机器学习大佬）、Steven Nowlan、以及 **Geoffrey Hinton**。

四位作者在论文里提出：不要训练一个大而全的神经网络，而是训练多个小"专家"网络，每个专家专注数据的不同子区域，再用一个可训练的"门控网络"（Gating Network）根据输入决定每个专家的权重。训练方法用的是 EM 算法（Expectation-Maximization）。

他们在日语元音识别上做了实验。结果很直白：MoE 模型达到目标准确率所需的训练轮次，大约是单一大型网络的一半。

这个想法在 1991 年是惊人的——"分而治之"比"一个大模型通吃"更快。但当时没人会用上千个 GPU 训练大模型，所以这个惊人的想法很快被遗忘在了论文堆里。

#### 1992-1995：理论框架的建立

1992 年，Hampshire 和 Waibel 发表了 Meta-Pi 网络，一个独立于 Jacobs 路线的并行多网络方案，用于语音识别。这说明"分而治之"的想法在 90 年代初不是孤立的一篇论文，而是一个方向。

真正的理论里程碑在 1994 年。Jordan 和 Jacobs 发表了《Hierarchical Mixtures of Experts and the EM Algorithm》，把 MoE 扩展成**树形层次结构**——专家不只有一层，而是多层嵌套。这篇论文从概率模型的框架重新解释了 MoE，并证明 EM 算法训练的收敛速度比梯度下降快约 10 倍。

1995 年，Jordan 和 Xu 给出了 MoE 训练的收敛性理论证明。到 90 年代中期，MoE 的理论基础已经相当完整——有架构、有训练算法、有收敛保证。但硬件跟不上理论。

#### 2001-2013：漫长的沉寂与偶然的尝试

在 90 年代后期到 2000 年代，MoE 基本处于休眠状态。2001 年 Collobert 和 Bengio 把 MoE 的门控思想扩展到了 SVM，证明这个框架不限于神经网络。但在那个 SVM 和随机森林统治机器学习的年代，MoE 依然是个飞地。

**2013 年是一个被低估的节点。** David Eigen、Marc'Aurelio Ranzato、Ilya Sutskever（后来 OpenAI 的联合创始人）发表了《Learning Factored Representations in a Deep Mixture of Experts》。这篇论文第一次尝试把 MoE 的门控机制嵌入到深度神经网络的每一层——本质上就是今天 Transformer MoE 的雏形。

但它失败了。核心问题出在"稀疏"上：当时的门控机制无法可靠地产生稀疏激活。Softmax 输出永远是"每个专家都有一点点贡献"，计算量和稠密模型没区别，MoE 的优势荡然无存。

与此同时，Yoshua Bengio 团队在 2013-2015 年间发表了一系列关于"条件计算"（Conditional Computation）的论文，核心思想是：网络的不同部分应该在需要时才激活。这和 MoE 的精神一脉相承，但 Bengio 的方案也没有实现真正的稀疏性。

这些失败有一个共同的技术原因：2013 年的优化器、GPU 显存、分布式训练框架，都不支持稀疏梯度的高效计算。想法对了，工具没跟上。

#### Shazeer 的铺垫（2016）

在 Google Brain，Noam Shazeer 并没有直接参与 2013 年的 MoE 尝试。他当时的主线工作是**大规模语言模型**。

2016 年，Shazeer 和 Jozefowicz 等人发表了《Exploring the Limits of Language Modeling》，把基于 LSTM 的稠密语言模型推到了当时的算力极限。这篇论文让他深刻体会到了稠密模型的扩展瓶颈：**参数每大一点，计算量就线性增长。想做个千亿参数的语言模型？先准备好电费账单。**

同一年，Shazeer 还做了"Sparse Non-negative Matrix Language Modeling"（2015）和"Swivel"词嵌入（2016）。这些工作虽然不直接涉及 MoE，但都围绕一个主题：**稀疏性**。他显然在找"怎么让模型只用一部分参数处理一个输入"的解法。

而解法已经在文献里沉睡了 25 年。

### 3.2 关键转折：Sparsely-Gated MoE（2017.01）

Shazeer 把 1991 年 Jacobs 等人的"用门控网络选专家"的思想、2013 年 Eigen 等人的"深度 MoE 层"的架构直觉、以及自己 2016 年从稠密语言模型 scaling 中得到的切肤之痛，融合成了一个新的方案。

2017 年 1 月，Shazeer 和 Azalia Mirhoseini、Quoc Le、Geoffrey Hinton、Jeff Dean 等 Google Brain 全明星阵容发表了《Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer》。这是 MoE 在大模型时代的开山之作，也是所有现代 MoE 模型（Mixtral、DeepSeek-V3、Qwen-MoE）的模板。

这篇论文提出了几个至今仍在使用的核心设计：

**稀疏门控（Sparsely-Gated）Router**：不只是一个简单的分类器，而是一个可学习的门控网络。对每个 token，Router 计算一个 softmax 分布，然后只选 top-K 个得分最高的专家。为了让不同 token 选不同的专家（而不是所有 token 都选同一个"最优"专家），引入了额外的噪声项。

**负载均衡**：作者意识到如果放任 Router 自己选，会出现可怕的"赢家通吃"——少数专家收到大部分 token，其余专家形同虚设。他们的解决方案是引入 auxiliary loss（辅助损失），在训练时惩罚"专家使用分布不均匀"的情况。

**层次化路由（Hierarchical Routing）**：当专家数量很大时（论文里有上千个专家），计算所有专家的 Router 分数本身就很贵。Shazeer 的方案是建一棵"专家树"，每层用一个小 Router 做粗选，走到叶子节点才是真正的专家。

实验结果令人震撼：用 Sparsely-Gated MoE 做语言模型，可以达到比同等计算量的 LSTM 模型好几个数量级的 perplexity 改善。但当时的主流程架还不是 Transformer，这篇论文也不是发表在 Transformer 的语境下。

然后，2017 年 6 月，Google 的另一组人（Vaswani et al.）发表了《Attention Is All You Need》，Transformer 诞生了。

### 3.3 Google 的 MoE 帝国时代（2018-2022）

从 2018 到 2022 年，Google 几乎是 MoE 领域唯一的玩家。他们内部显然认定了 MoE 是通向大模型的正确路线，投入了大量资源。

#### GShard（2020）：把 MoE 放进 Transformer

GShard 是第一个真正把 MoE 和 Transformer 结合起来训练的大规模系统。Lepikhin 等人用 MoE 替代了 Transformer 中每隔一层的 FFN，在机器翻译任务上训练了 600B 参数的模型。

GShard 的核心贡献不是算法创新，而是系统工程：它提出了一套把不同 expert 的权重分布到不同 TPU 设备上的策略（GShard = Giant Sharding），让训练巨大 MoE 模型成为工程上可行的目标。论文还引入了 expert capacity（专家容量）的概念——如果某个 expert 收到的 token 超过了容量上限，多余的 token 直接丢弃。这很粗暴，但在工程上有效。

#### Switch Transformer（2021）：更简单的 Router 反而更好

2021 年 1 月，Google 的 William Fedus 等人发表了 Switch Transformer。这篇论文做了一个现在看来有点反直觉的简化：把 Router 的 top-K 从常见的 K=2 改成 K=1。

他们的论证是：top-1 路由大幅简化了路由和合并的计算，减少了通信开销。模型为了补偿"只选一个专家"的信息损失，会学到更好的专家分工。引入的 capacity factor（容量因子）概念让负载均衡变得更可控——当 capacity factor = 1.0 时，一个 expert 最多处理 tokens / N 个 token（即刚好均分）；设为 1.5 则允许 50% 的溢出缓冲。

Switch Transformer 在 C4 数据集上预训练了从 8B 到 1.6T 参数的各种规模，展示了 MoE 的可扩展性。关键结论是：**MoE 的扩展效率优于稠密模型**——同样的计算量下，加更多专家 > 加更多层。

但 top-1 也有代价：每个 token 只走一个专家，失去了"不同专家从不同角度贡献"的机会。这也是为什么后来 DeepSeek 等模型又把 K 调回了更大的值。

#### GLaM（2021）：GPT-3 的 MoE 对标

2021 年底，Google 发布了 GLaM（Generalist Language Model），1.2T 总参数，激活 97B（64 个专家，top-2）。Google 声称在 29 个 NLP 基准上，GLaM 用 GPT-3 训练量 1/3 的能耗，达到了 GPT-3 的性能水平，部分任务上甚至显著超越。

但 GLaM 始终没有开源，也没有公开 API。它更像是一次内部技术验证和对外的 PR 宣示——"我们 Google 有比 GPT-3 更高效的架构"——但这没能阻止 OpenAI 在主流认知中领先。

#### ST-MoE（2022）：解决训练稳定性

2022 年 2 月，Google 的 Zoph 等人发表了 ST-MoE（Stable and Transferable MoE）。这篇论文直面 MoE 的两大痛点：

**训练不稳定**：提出了 Z-loss —— 在 Router 输出的 logit 上额外加一个正则化项，惩罚绝对值过大的 logit 值。这有效防止了 router 输出极端分布（所有 token 走同一个 expert）。

**专家丢弃问题**：当 expert capacity 不够时，token 被丢弃会浪费计算和训练数据。ST-MoE 提出用 random routing（随机路由）作为兜底——当优先 expert 满了，随机发到一个不那么忙的 expert，虽不最优但至少不浪费。

ST-MoE 还在实验中系统比较了 scaling MoE 的不同方式，发现增加 expert 数量 > 增加 expert 大小。这一结论直接影响了后来的 Mixtral 和 DeepSeek 的架构选择。

到 2022 年底，Google 的内部 MoE 技术栈已经相当成熟。但讽刺的是，这些技术几乎都停留在论文和内部系统里，真正把 MoE 带到开源社区和大众视野的，是一家法国小公司。

### 3.4 开源时代的开端：Mixtral 8x7B（2023.12）

2023 年 12 月，巴黎创业公司 Mistral AI 发布了 Mixtral 8x7B。

这不是第一个 MoE 模型，但它是第一个**真正好用的开源 MoE 模型**。8 个 expert，每个 7B 参数，top-2 路由，总参数 47B，每次激活 13B。它的推理速度和 13B 稠密模型相当，但性能接近 GPT-3.5。

更关键的是，Mistral 只发了一条推文附带 torrent 链接（甚至没写博客），扔出模型权重就走了。这个"不够正式"的发布方式反而引爆了社区——48 小时内，开发者们自己测、自己写 benchmark、自己在 Reddit 和 HuggingFace 上分享结果。开源社区第一次感受到：MoE 不是一个 Google 内部的实验室玩具，是我能在自己 GPU 上跑的东西。

2024 年 4 月，Mistral 又发布了 Mixtral 8x22B，把每个 expert 放大到 22B，总参数 141B，对标 GPT-4 的性能区间。

Mixtral 的路由策略有两个值得说的设计：

**Router bias toward high-norm**：Mistral 发现，训练过程中会出现某些 expert 输出向量的 norm 系统性地高于其他 expert。Router 倾向于选 norm 高的 expert（因为它们"声音更大"），但这其实是参数初始化带来的偏差，不是真正的专长分工。Mistral 的解法是在 router 里对输出 norm 做补偿。

**Token-choice routing**：每个 token 选专家。这是标准的 token-choice 路由方式，但跟后来一些研究讨论的 expert-choice（让专家选 token）形成对比。

### 3.5 DeepSeek 的架构革命（2024-2025）

如果说 Mixtral 是把 MoE 做成一个"大家都能用的产品"，那 DeepSeek 就是在这个基础上做了架构层面的重大创新。

#### DeepSeek-V2（2024.5）：三个关键创新

2024 年 5 月，DeepSeek 发布了 DeepSeek-V2，一个 236B 总参数（激活 21B）的 MoE 模型。这个模型对 MoE 架构做了三件事，每一件都影响深远：

**创新一：Fine-grained Expert Segmentation（细粒度专家切分）**

传统 MoE 的每个 expert 就是一个完整的标准 FFN。DeepSeek 的洞见是：打破 expert = 一个完整 FFN 的等式，把 1 个标准 FFN 切分成 m 个更小的"mini-expert"。比如原来 1 个 7B 的 expert，切成 4 个 ~1.75B 的 mini-expert。

为什么要这么做？更灵活的组合。标准 expert 太大，选 2 个就可能激活了太多参数。mini-expert 让 Router 可以更精细地激活——选更多 mini-expert，但每个更小，总和可控。DeepSeek-V2 用了 m=4 的切分。

**创新二：Shared Experts（共享专家）**

传统的 MoE 里，通用知识（语法、基本常识）需要在每个 expert 里冗余存储——因为每个 token 都要用到这些知识，但每次只走 2 个 expert，所以每个 expert 都得备一份。

DeepSeek 的方案：分出一小部分参数作为"共享专家"，所有 token 都必须经过它们。然后加上一些"路由专家"，按 token 内容选择性激活。DeepSeek-V2 的 236B 参数中，有 2 个共享专家（它们的输出在合并时权重固定），160 个路由专家（分为 4 组，每 token 激活 6 个）。

这个设计避免了知识的冗余存储。共享专家存"人人都需要的"（语法、常识），路由专家存"某一类问题需要的"（代码、数学、特定语言）。

**创新三：Auxiliary-Loss-Free Load Balancing（无辅助损失的负载均衡）**

前面提到，MoE 训练需要 auxiliary loss 来强制专家负载均衡。但 auxiliary loss 有一个根本问题：它和主任务的目标（降低 language modeling loss）是冲突的。你在强迫模型同时优化两个相互拉锯的目标。

DeepSeek 的方案很优雅：不用 auxiliary loss，而是在每个 expert 的 Router 分数上加一个动态 bias。如果某个 expert 最近太忙，bias 就减一点，让 token 不太愿意选它；如果太闲，bias 就加一点。这个 bias 不在梯度路径上——只影响前向选择，不参与反向传播。所以它不影响模型的优化目标，纯做负载均衡。

这三个创新组合在一起，DeepSeek-V2 做到了：236B 总参数，21B 激活参数，在大部分基准上超越了 Mixtral 8x22B（141B 总参数），而且训练成本不到同类模型的 1/3。

除了 MoE 架构层面的创新，V2 还引入了一项对推理成本影响深远的注意力机制创新——**MLA（Multi-Head Latent Attention，多头潜注意力）**。MLA 将 K/V 向量压缩到一个极小的"潜空间"，只存压缩后的潜向量，推理时再解压恢复。效果：每个 token 的 KV Cache 从标准 MHA 的 ~1.2MB 压缩到 ~70KB（仅为原来的约 6%，对比主流 GQA 也降到了约 1/3~1/7，等效 GQA-2.25 组），推理吞吐提升 5.76 倍。MoE 让 FFN 参数膨胀，MLA 让 Attention 显存收缩——这套"MoE + MLA"的组合拳，是 DeepSeek 能以 GPT-4 约 1% 价格提供 API 服务的关键工程基础。

#### DeepSeek-V2.5（2024.9）和 V3（2024.12）

V2.5 是一次迭代升级，加入了 DeepSeek-Coder 和 DeepSeek-Math 的能力融合，优化了数学和代码性能。

V3 才是真正的重磅升级。2024 年 12 月，DeepSeek 发布了 DeepSeek-V3，671B 总参数，37B 激活参数，256 个专家。

更让人震惊的是训练成本公开：V3 的训练仅花费约 557.6 万美元（2,788,000 H800 GPU 小时）。作为对比，同级别的 GPT-4 训练成本据估算超过了 1 亿美元。这不是因为 DeepSeek 穷，而是他们做了一系列极致的工程优化。

V3 在 V2 的三大创新基础上做了全面升级。MoE 架构上，路由专家从 160 个增加到 256 个，共享专家从 2 个精简为 1 个，门控函数从 Softmax 换成了 Sigmoid——每个专家的路由分数独立计算，不再互相挤压。工程层面的创新同样关键：**Multi-Token Prediction（MTP）** 让模型同时预测多个未来 token，训练信号更密集，推理时通过投机解码实现 1.8x 加速；**FP8 混合精度训练** 首次在大规模模型上验证可行，显存和计算量减半；自研的 **DualPipe 流水线并行** 算法实现了计算与通信的近乎完全重叠。

#### DeepSeek R1（2025.1）：推理能力的范式突破

2025 年 1 月，DeepSeek 发布了 R1，一个基于 V3-Base 的推理模型。这篇论文后来登上了 **Nature 封面**（2025 年 9 月），是全球首个经过同行评审的主流 LLM 研究成果。

R1 的核心创新是 **GRPO（群体相对策略优化）算法**。传统的 RLHF 用 PPO 训练，需要同时维护一个和策略模型同等规模的 Critic 模型，训练复杂度和显存开销都巨大。GRPO 去掉了 Critic 模型：对同一个问题生成一组候选答案，以组内平均得分为基线计算相对优势值。省了一个大模型的开销。

更惊人的是 **R1-Zero**：完全不用任何 SFT 数据，直接对 V3-Base 做纯强化学习训练，模型自己涌现出了"思考"行为——
- 自我反思："Wait, wait. That's an aha moment..."
- 自我验证：双重检查，交叉验证
- 自适应思考时间：简单题一笔带过，难题分多步推理

AIME 2024 得分 79.8%，MATH-500 达到 97.3%，Codeforces Elo 2029（超过 96.3% 人类选手）。而且推理成本仅为 OpenAI o1 的 3-4%。

R1 的影响超出了 benchmark：它证明了"推理能力可以通过纯 RL 从 Base 模型中涌现"，这个范式影响了后续几乎所有推理模型的训练方式。

#### DeepSeek V3.1（2025.8）：混合推理架构

2025 年 8 月，DeepSeek 发布了 V3.1。这次更新的核心是把 V3（非推理）和 R1（推理）合并成一个统一模型——通过"深度思考"按钮一键切换推理/非推理模式，不需要部署两套权重。

V3.1 的 Agent 能力大幅提升：SWE-bench Verified 从 V3 的 45.4 跃升到 66.0（+45%），Terminal-Bench 提升 5 倍以上。后续 V3.1-Terminus（2025.9）进一步将 SWE-bench 推到 68.4。

但 V3.1 也闹出了著名的"极"字 bug——模型会随机在输出中插入"极"字，甚至出现在 JSON 和代码里。社区分析怀疑是 tokenizer 中"极"（token ID 2577）和省略号"……"（token ID 2576）相邻，数据清洗时产生了 off-by-one 错误。这个 bug 在 V3.2 中被修复。

#### DeepSeek V3.2（2025.12）

V3.2 修复了"极"字 bug，引入了 **DeepSeek Sparse Attention (DSA)**——通过 Lightning Indexer 对过往 token 打分，从 128K 上下文中仅选 k=2048 个最相关 token，将注意力复杂度从 O(L²) 降至 O(Lk)。同时将 RL 训练的计算量提升到预训练 FLOPs 的 10% 以上，Agent 能力大幅提升。

V3.2-Specialized 专注数学/学术：IMO 数学奥赛 35/42 金牌，IOI 信息学奥赛 492/600 金牌。AIME 2025 达 96.0%。

#### DeepSeek V4（2026.4.24）：百万上下文时代的开源旗舰

V4 是 DeepSeek 迄今为止最大的架构跃迁。两个模型同时开源（MIT 协议）：

| 规格 | V4-Pro | V4-Flash |
|------|--------|----------|
| 总参数 | 1.6T | 284B |
| 激活参数 | 49B | 13B |
| 上下文 | 1M | 1M |
| 最大输出 | 384K | 384K |

V4 最核心的架构创新是 **Hybrid Attention（混合注意力）**，由两种互补的注意力机制组成：

**CSA（Compressed Sparse Attention）**：先用动态序列压缩减少 KV 条目数量，再对压缩后的注意力矩阵做稀疏化。相当于先"粗读"筛选相关信息，再"精读"处理关键部分。

**HCA（Heavily Compressed Attention）**：激进地将每 128 个连续 token 的 KV 压缩为一个条目，把 KV Cache 砍到原来的 1/128。适合处理长篇背景信息中不需要逐 token 精确检索的部分。

两种注意力机制在模型的不同层和不同位置自适应切换。结果：在 1M token 上下文下，V4-Pro 的单 token 推理 FLOPs 比 V3.2 降低 73%，KV Cache 显存降低 90%。

其他关键创新：
- **mHC（Manifold-Constrained Hyper-Connections）**：将残差连接的映射矩阵投影到 Birkhoff 多面体，信号放大从 3000 倍降至 1.6 倍，训练额外开销仅 6.7%
- **Muon 优化器** + FP4/FP8 混合精度训练
- 三种推理模式：Non-Think（快速）→ Think-High（显式思维链）→ Think-Max（384K+ 上下文深度推理）

性能基准：V4-Pro 在 SWE-bench Verified 达到 80.6%（匹配 Claude Opus 4.6），LiveCodeBench 93.5%（超越 Kimi K2.6），HMMT 2026 数学 95.2%。在 GDPval-AA（Agent 工作基准）上以 1554 Elo 排名开源模型第一。

API 定价：V4-Pro 输入 $1.74/M tokens，输出 $3.48/M tokens（缓存命中 $0.145/M）。比 GPT-5.5 Pro 便宜约 98%。

DeepSeek 的 MoE 模型开源策略，深刻改变了 AI 生态。从 V2 到 V4，所有模型都在 HuggingFace 上公开完整权重（MIT 协议）。vLLM 和 SGLang 两个主流推理框架都对 DeepSeek MoE 做了专门优化，华为昇腾 950 超节点和寒武纪芯片也实现了 Day 0 适配。

### 3.6 阿里 Qwen 的 MoE 路线（2024-2026）

阿里通义团队是另一个在 MoE 上投入巨大的玩家。他们的路线和 DeepSeek 不同，更注重生态完整性。

#### Qwen2.5-MoE（2025）

阿里的首次 MoE 公开亮相。14.3B 总参数，激活 2.7B——把 MoE 的"轻量部署"做到了极致。这个模型的定位是端侧和移动端部署，让 MoE 不再只是"大模型的玩物"。

#### Qwen3-MoE（2025-2026）

Qwen3-MoE 沿用了 DeepSeekMoE 的 fine-grained expert + shared expert 方案，但做了自己的路由策略优化。有多个规模版本，从端侧到云端覆盖。

#### Qwen3-Next（2026）

这是阿里 MoE 路线中最激进的设计。Qwen3-Next 不再是一个纯 Transformer 模型，而是把 GatedDeltaNet（一种新型线性注意力机制）和 MoE 结合在一起。512 个专家，用了一种新的路由器设计来管理超大规模专家池。

这个混合架构的动机是：传统的 Softmax Attention 在处理超长序列时计算量按序列长度的平方增长。用 GatedDeltaNet 替代部分层的 Attention，既能减少计算量，又能让 MoE 的专家专注于更重要的信息处理。

这个方向是否真能 work，还有待更广泛的验证。但 Qwen3-Next 代表了一个趋势：**MoE 不只是 Transformer 内的局部替换，而是可以和其他架构创新（新 Attention 变体、新层类型）组合使用的灵活工具。**

#### Qwen3.5（2026.2）：原生多模态 Early Fusion

2026 年 2 月，阿里发布了 Qwen3.5 系列。旗舰 Qwen3.5-397B：397B 总参数，17B 激活（仅 4.28%），512 路由专家 + 1 共享专家，每 token 激活 10 个。262K 上下文，可扩展至 1M+。

Qwen3.5 最大的架构创新是 **原生多模态 Early Fusion**——文本和图像在 token 级别共享同一表示空间，而不是"先把图 encode 成向量再拼到文本里"。27B 参数的多模态版本直接超越了上一代 235B 专用视觉模型。

性能基准：MMLU-Pro 87.8%，HumanEval 90.9%，GPQA Diamond 88.4%，AIME 2026 达 91.3%，MATH-500 达 98.2%，SWE-bench Verified 76.4%，LiveCodeBench v6 83.6%，IFEval 92.6%。在 Artificial Analysis Intelligence Index 中，开源权重排名 #3。

词表 250K，覆盖 201 种语言，中文推理和多轮对话能力在开源模型中保持领先。

#### Qwen3.6-Plus（2026.4.2）：Agentic Coding 发力

仅隔一个半月，阿里于 4 月 2 日发布 Qwen3.6-Plus——定位为"最强国产编程模型"。397B 总参数 / 17B 激活，1M token 上下文。

四个核心升级：
- **Agentic Coding**：不只是生成代码片段，而是全自主执行——自动修 bug、终端自动化、长链路任务规划。演示中用 8 分钟生成完整响应式企业网站，成本仅 ¥0.15
- **前端开发**：强化 React/Vue/Svelte 支持，从截图直接生成前端代码
- **1M 上下文**：支持整个代码库级别的理解和修改
- **原生多模态**：图像+文本混合推理，能识别 UI 截图中的元素坐标、颜色、层级

API 定价：输入 ¥2/百万 token，输出 ¥12/百万 token。

### 3.7 美国玩家的 MoE 态度（2024-2026）

#### OpenAI：GPT-4 真的是 MoE 吗

关于 GPT-4 是否是 MoE 架构，AI 圈的传闻从未断过。

2023 年 6 月，George Hotz（geohot）在播客中透露，他听到的说法是 GPT-4 用了 8 个 expert，每个 220B 参数。如果属实，GPT-4 就是一个 8x220B 的 MoE 模型，总参数约 1.8T（后来 OpenAI 否定了 1.8T 这个数字，但没有否认 MoE 架构）。

2024 年，一些间接证据指向 GPT-4 使用了某种形式的 MoE：API 定价中不同模型的推理速度差异、某些社区测试中发现的"有时慢有时快"的行为模式（符合不同 token 走不同专家的特征）。

但 OpenAI 官方从未正面确认或否认。直到 2025 年，奥特曼在一次访谈中被直接问到 MoE，他的回答是"不想公开架构细节"。这个模糊是有价值的——它暗示 MoE 至少是内部认真考虑过甚至已经使用的东西，否则大可以直接否认。

#### Google Gemini

Google 在 Gemini 上延续了 MoE 路线，但同样没有公开架构细节。从 DeepMind 团队的零星表态可以判断，Gemini 使用了某种形式的 MoE。给定的 Google 过去在 MoE 上的积累，这是最自然的路径。

不过值得玩味的是，Google 在 MoE 论文上领先了那么多年，但在真正让 MoE 产生商业影响力的比赛中，却输给了 Mistral 和 DeepSeek。"原创"和"落地"之间的差距，在 MoE 的故事里被放大了。

#### Anthropic：坚持 Dense 的少数派

在所有主流 AI 玩家中，Anthropic 是唯一一个旗帜鲜明地选择了稠密（Dense）架构的公司。Claude 3/4 系列全部是 Dense Transformer。

Anthropic 的推理很务实。他们认为：

1. **训练稳定性**：Dense 模型的训练远比 MoE 稳定，不需要 auxiliary loss、bias 调整、expert dropout 等额外机制。Anthropic 的 Scaling Monosemanticity（单义性研究）系列工作，对训练过程中的可解释性有极高要求，MoE 的路由行为会显著增加解释的难度。

2. **推理部署简单**：Dense 模型可以直接在标准 GPU 上推理，不需要处理 expert 分布、EP（Expert Parallelism）、KV Cache 跨设备通信等复杂问题。这对 API 的延迟稳定性很重要。

3. **Fine-tune 友好**：企业客户通常需要 fine-tune 模型。MoE 的稀疏激活在 fine-tune 时容易过拟合，而 Dense 模型的 fine-tune 经验成熟、效果可预期。

4. **安全对齐更容易**：Anthropic 把安全放在首位。MoE 的路由机制引入了新的攻击面——恶意输入可以操纵 Router 走向特定专家，产生不可预期的输出。Dense 模型没有这个攻击面。

Anthropic 的选择有代价：他们的模型单位参数效率可能不如 MoE。但他们的判断似乎是，对于他们真正在乎的维度（安全、可控、稳定），Dense 是更合理的选择。到目前为止，Claude 3.5/4 的性能在同等规模下不输给 MoE 模型，说明他们的折中至少目前是成立的。

#### xAI Grok：从保守 MoE 到激进辩论架构

Grok-1（2024.03）是一个 314B 的 MoE 模型（8 专家，top-2），基本沿用了 Mixtral 的设计。但 Grok 的后续演进出现了戏剧性的架构转向——详见 3.10 节。

### 3.8 中国 MoE 军团：小米、智谱、百度、字节（2025-2026）

2025-2026 年，中国 AI 公司在 MoE 上的投入出现了"百花齐放"的局面。不再只是 DeepSeek 和阿里的二人转。

#### 小米 MiMo-V2.5（2026.4.28）：手机厂商登顶开源榜首

2026 年 4 月 28 日（报告撰写当天），小米正式开源 MiMo-V2.5 系列。旗舰 MiMo-V2.5-Pro：1.02 万亿总参数，42B 激活，1M 上下文，**MIT 开源协议**。发布当天即登顶 Artificial Analysis 全球开源模型综合智能指数第一，Agent 专项能力开源第一，全球所有模型总榜前五。

架构上，MiMo-V2.5-Pro 采用滑动窗口注意力（SWA）与全局注意力（GA）以 6:1 交替使用，KV Cache 减少约 7 倍。多令牌预测（MTP）将推理吞吐量提升约 3 倍。预训练数据 27 万亿 token。

同步发布的 MiMo-V2.5（310B/15B）是原生全模态模型：文本、图像、视频、音频统一架构，配备 729M 参数的 ViT 视觉编码器。预训练数据 48 万亿 token。

在 GDPVal-AA（Agent 工作基准）和 Claw-Eval 等评测中，MiMo-V2.5-Pro 超越了 DeepSeek-V4-Pro。API 定价仅为国际闭源旗舰的约 2.5%。

生态方面，发布首日即完成与 7 家芯片厂商（阿里平头哥、AWS Trainium、AMD、百度昆仑芯、燧原、沐曦、天数智芯）和 SGLang/vLLM 两大推理框架的 Day 0 适配。小米同步启动"Orbit 百万亿 Token 计划"，30 天内向全球开发者免费发放 100 万亿 token。

**小米的入局标志着一个重要转折：手机厂商不再是 AI 的消费者，而是基础设施的建设者。**从 2025 年 12 月的 MiMo-V2-Flash 到 2026 年 4 月的 V2.5-Pro 登顶，迭代周期仅 4 个月。

#### 智谱 GLM-5.1（2026.4.8）：昇腾算力上训练的开源旗舰

智谱 AI 于 4 月 8 日发布并开源 GLM-5.1：744B 总参数，40-44B 激活，256 个专家（每 token 激活 8 个），200K 上下文，MIT 协议。

GLM-5.1 最引人注目的不是架构创新，而是**训练基础设施**：完全使用 10 万张华为昇腾 910B 芯片训练，未使用任何英伟达 GPU。在华为昇腾上实现了 Layer 级 MoE 绝对均衡，整体吞吐量提升 30%。这是"去英伟达化"路线上第一个真正具有国际竞争力的开源旗舰模型。

性能方面，SWE-bench Pro 达 77.8%，首次在代码评测上超越 Claude Opus 4.6（国产模型首次）。三项代码评测综合平均分：全球第三、国产第一、开源第一。

更惊人的是**长程自主任务能力**：能在单次任务中持续自主工作长达 8 小时，在 METR 榜单上是唯一达到 8 小时级别的开源模型。演示中在 8 小时内构建了完整的 Linux 桌面系统，执行超过 1200 步操作。

API 定价极具侵略性：输入 $1.00/M tokens，输出 $3.20/M tokens——约为 Claude Opus 4.6 的 1/15，达到其约 94.6% 的编码性能。发布当天同步上线华为云、壁仞科技、昆仑芯、摩尔线程等多家国产 GPU 厂商。

#### 百度文心 ERNIE 5.0（2026.1）：2.4 万亿参数的超稀疏 MoE

百度于 2026 年 1 月发布 ERNIE 5.0，是目前公开参数规模最大的 MoE 模型之一：2.4 万亿总参数，激活率不到 3%（每次推理仅激活约 700 亿参数）。

ERNIE 5.0 的核心路线是**原生全模态统一建模**——文本、图像、音频、视频在训练之初就在同一个 Transformer 框架中融合，不做后期拼接。采用"模态无关的专家路由"（Modality-Agnostic Expert Routing）——不为专家预设模态标签，专家在训练中自行涌现专业化分工，自动分化出视觉专家、文本逻辑专家和跨模态通才。

训练采用了"弹性训练"（Elastic Training）策略：一次预训练即可产出不同深度/宽度/稀疏度的子模型矩阵，无需重新微调。技术报告于 2026 年 2 月发布于 arXiv。

LMArena 文本能力国内第一（1460 分），数学能力全球第二（仅次于 GPT-5.2-High）。文心助手月活突破 2 亿，千帆平台累计开发 130 万+ Agent。

#### 字节跳动 Seed 2.0 / Seed3D 2.0

字节跳动的 LLM 路线相对保守。2026 年 2 月发布的豆包 Seed 2.0（Pro/Lite/Mini/Code 四个版本）在 HLE-text 得分 54.2，长上下文理解 Frames 榜单第一，但**未公开确认使用 MoE 架构**。

不过字节 Seed 团队在 MoE 研究上并不缺席。2026 年 1 月，他们联合中国人民大学提出了 **ERC（Expert-Router Coupling）损失**，用于解决 MoE 中专家专业化不足与路由不匹配的问题，在 3B 和 15B 参数 MoE-LLM 上验证有效。4 月发布的 **Seed3D 2.0**（3D 生成模型）则明确采用了 MoE 架构——通过稀疏专家路由机制在扩大参数量和分辨率的同时控制推理计算量。

### 3.9 MoE 推理生态的演进（2023-2026）

MoE 模型能不能实际使用，很大程度上取决于推理框架的支持。这部分演进时间线值得单列。

**2023**：MoE 模型还是少数派的玩具。大部分推理框架（包括初版 vLLM）对 MoE 支持很差。Mixtral 发布时，开发者用的是 transformers 库原生推理，用 HuggingFace 的 `device_map="auto"` 把不同 expert 分布到不同 GPU，效率极低。

**2024 上半年**：vLLM 0.4.x 加入了初步的 MoE 支持，主要是 Expert Parallelism（把不同 expert 分布到不同 GPU 上处理）。但 EP 的实现还很粗糙，通信开销大。

**2024 下半年**：SGLang 异军突起，对 MoE 的优化比 vLLM 更激进。DeepSeek-V3 发布后，SGLang 成了社区的默认推理选型——它在 MoE 上的吞吐量比 vLLM 高 30-50%。

**2025**：两个框架对 MoE 争夺进入白热化。vLLM 重新设计了 MoE 的 fused kernels，SGLang 引入了 RadixAttention + MoE 的联合优化。TensorRT-LLM 也加入了 MoE 的 Expert Parallelism 支持，在企业级部署上更有优势（更低的 P99 延迟）。

**2026**：MoE 推理已经成为每个框架的标配功能。社区总结出了几条公认的 MoE 推理优化法则：
- 小批量推理：Pre-fill（首次推理）受计算限制，EP 的通信开销不明显
- 大批量推理：Decode 阶段受 KV Cache 显存限制，EP 反而增加开销
- Expert 多卡分布时，all-to-all 通信是最大瓶颈

### 3.10 2025-2026：MoE 成为行业标配

#### Mistral 的"回归"：从 Dense 退回到 MoE（2025.12）

Mistral 在 2024 年 7 月发布了 Mistral Large 2（123B Dense），当时看来是对 MoE 的一次理性回归——这家以 Mixtral 成名的公司选择了更稳定的 Dense 架构来做旗舰模型。

但 2025 年 12 月，Mistral 发布了 Mistral 3 系列，又重新回到了 MoE 路线。Mistral Large 3 是一个 675B 参数的 Granular MoE 模型，128 个专家，激活约 41B（仅占总参数的 6%）。从 2024 年 Large 2 的 123B Dense 到 2025 年 Large 3 的 675B MoE，激活参数反而从 123B 降到了 41B。

这个"离开又回来"的轨迹说明了 MoE 的引力：当你想把模型做大，MoE 几乎是唯一可行的路线。Mistral Large 2 的 123B Dense 在性能上触到了天花板，而要突破这个天花板、同时保持推理经济性，MoE 是不可避免的选择。

到 2026 年 3 月，Mistral 又发布了 Small 4（119B 总参、仅 6.5B 激活、128 专家），把细粒度 MoE 推到了极致——激活比不到 5.5%。

#### Meta 入局：Llama 4 首款 MoE（2025）

Meta 在 Llama 系列上一直坚持 Dense 路线（Llama 3.1 405B 是纯 Dense）。但 2025 年发布的 Llama 4 转向了 MoE：

- **Llama 4 Scout**：109B 总参数，17B 激活，16 个专家。10M 上下文窗口是最大卖点。
- **Llama 4 Maverick**：400B 总参数，17B 激活，128 个专家。1M 上下文。

Meta 的 MoE 设计偏保守——Scout 只用了 16 个专家（远少于 DeepSeek 的 256），激活比也较高（15.6% vs DeepSeek V3 的 5.5%）。这说明 Meta 在 MoE 上的首要考量是训练稳定性和可预测性，而非极致效率。

#### Kimi K2 → K2.6：Agent Swarm 路线（2025-2026）

月之暗面（Moonshot AI）的 Kimi 系列是 MoE 路线上最激进的 Agent 实践者：

**Kimi K2**（2025.7）：首个开源 1T 参数 MoE 模型。384 路由专家 + 1 共享专家，激活 32B。引入 MuonClip 优化器——"ML 史上最平滑 loss 曲线"，收敛速度是 AdamW 的 1.4 倍。SWE-bench Verified 65.8%。

**Kimi K2.6**（2026.4.20）：Agent 能力的代际跃升。同样 1T/32B MoE 架构，但核心升级在 **Agent Swarm（智能体集群）**：扩展到 300 个子 Agent 并行执行 4000+ 步协调操作。演示中实现了 13 小时连续自主编码（修改 4000+ 行代码）、10 小时构建完整 SysY 编译器、5 天不间断自主运维。

K2.6 在 Terminal-Bench 2.0 达到 66.7（超越 GPT-5.4 的 65.4），BrowseComp 83.2，DeepSearchQA F1 92.5。Artificial Analysis 综合智能指数排名第四（仅次于 Anthropic/Google/OpenAI）。

API 定价相比 K2.5 上涨 58%：输入 $0.95/M tokens，输出 $4.00/M tokens——反映了 Agent 工作负载更高的 token 消耗。

#### xAI Grok 的激进 Scaling + 辩论架构

Grok-1（2024.03）是一个 314B 的 MoE 模型（8 专家，top-2），基本沿用了 Mixtral 的设计范式。但 Grok 的后续演进出现了戏剧性的架构转向：

**Grok-4.20 Beta**（2026.3）：不再是一个单一模型，而是**4 个专业化 Agent 的辩论系统**——Grok（协调者）、Harper（实时检索 X/Twitter 数据的研究员）、Benjamin（数学/代码逻辑验证）、Lucas（创意与表达优化）。四个 Agent 并行推理、实时辩论、达成共识后输出。"Heavy"模式可扩展至 16 个 Agent。

Grok-4.20 的非幻觉率达 78%（行业最高），上下文 2M token。在 Alpha Arena 股票交易测试中，Grok 是唯一盈利的 AI（$10K → $13.5K），而 OpenAI 和 Google 都亏损。HLE 50.7% 仍是业界标杆之一。

API 定价 $2/$6 每百万 token（输入/输出）。SuperGrok 订阅 $30/月（Heavy 16-Agent 模式）。

**Grok-5 预计 2026 年底达到 6-7T 参数**，训练集群 Colossus 2（55 万+ GB200/GB300 GPU）。

### 3.11 纵向演进的核心脉络

回头看 30 年的 MoE 演进史，有一条清晰的主线：

**第一阶段（1991-2016）**：想法超前于工程条件，MoE 存在于论文里但不具备实用条件。

**第二阶段（2017-2022）**：Google 建立了 MoE 的技术基础。稀疏路由、负载均衡、大规模训练、训练稳定化的核心技术都在这一时期被提出。但 Google 的 MoE 技术始终没有走出内部系统。

**第三阶段（2023-2024）**：开源改变了 MoE 的走向。Mistral 证明了"开源 MoE 好用"，DeepSeek 证明了"开源 MoE 可以比闭源更好"。MoE 从一个 Google 内部的技术栈变成了社区可参与、可改进的开放生态。

**第四阶段（2025-2026）**：MoE 进入"标配化"阶段。几乎所有主流模型都在用（或至少考虑用），Anthropic 的 Dense 选择反而成了特立独行。MoE 推理生态成熟，从少数派技术变成了基础设施。中国 AI 公司的 MoE 模型出现爆发式增长——DeepSeek V4、Qwen3.6、MiMo-V2.5、GLM-5.1、ERNIE 5.0——不再跟随 Google/Mistral 的路线，而是在架构创新、训练效率、开源策略上各走各路。

驱动这条演进主线的最核心矛盾始终是：**如何在给定的计算预算下，最大化模型能力？** MoE 的核心 trade-off（用显存放能力，用稀疏换速度）三十年不变，变得只是工程化程度和生态成熟度。

---

## 四、横向分析

对 2026 年 4 月当前时间点的 MoE 竞争格局进行全面横向对比。

### 4.1 竞争格局概况

当前的 MoE 世界可以分为五个阵营：

| 阵营 | 代表模型 | 策略 |
|------|---------|------|
| **开源旗舰** | DeepSeek V4-Pro、MiMo-V2.5-Pro | 架构创新 + 极致性价比 + MIT 开源 |
| **全面生态** | Qwen3.5/3.6、ERNIE 5.0 | 全尺寸覆盖（手机到云端）+ 多模态融合 |
| **Agent 专精** | Kimi K2.6、Grok-4.20 | Agent Swarm / 多 Agent 辩论，长程自主 |
| **闭源不透露** | GPT-5/Gemini 3.1 Pro | 用了但不说的"黑箱 MoE" |
| **Dense 少数派** | Anthropic Claude | 明确不做 MoE，走可解释性+安全路线 |

### 4.2 核心模型架构对比

| 模型 | 发布时间 | 总参数 | 激活参数 | Expert 数 | Top-K | 关键创新 | 开源 |
|------|---------|--------|---------|----------|-------|---------|------|
| Mixtral 8x7B | 2023.12 | 47B | 13B | 8 | 2 | 首个开源高性能 MoE | ✅ |
| Mixtral 8x22B | 2024.04 | 141B | 39B | 8 | 2 | expert 容量放大 | ✅ |
| DeepSeek-V2 | 2024.05 | 236B | 21B | 160+2 | 6+2 | 细粒度切分+共享专家+无aux loss | ✅ |
| DeepSeek-V3 | 2024.12 | 671B | 37B | 256+1 | 8+1 | Sigmoid门控、MTP、FP8训练、$5.6M | ✅ |
| DeepSeek R1 | 2025.01 | 671B | 37B | 256+1 | 8+1 | GRPO纯RL推理、Nature封面 | ✅ |
| DeepSeek V3.2 | 2025.12 | 671B | 37B | 256+1 | 8+1 | DSA稀疏注意力、RL>10% FLOPs | ✅ |
| **DeepSeek V4-Pro** | **2026.04** | **1.6T** | **49B** | 未公开 | 未公开 | **Hybrid Attention CSA+HCA、1M ctx** | ✅ |
| **DeepSeek V4-Flash** | **2026.04** | **284B** | **13B** | 未公开 | 未公开 | 轻量V4、384K输出 | ✅ |
| Qwen3-235B | 2025 | 235B | 22B | 128 | 8 | Hybrid Thinking | ✅ |
| Qwen3-Next | 2025.09 | ~80B | 3B | 512+1 | 10 | GatedDeltaNet + MoE 混合 | ✅ |
| **Qwen3.5-397B** | **2026.02** | **397B** | **17B** | **512+1** | **10** | **原生多模态 Early Fusion** | ✅ |
| **Qwen3.6-Plus** | **2026.04** | **397B** | **17B** | **512+1** | **10** | **Agentic Coding、1M ctx** | ✅ |
| **MiMo-V2.5-Pro** | **2026.04** | **1.02T** | **42B** | 未公开 | 未公开 | **SWA+GA混合注意力、开源榜首** | ✅ |
| **MiMo-V2.5** | **2026.04** | **310B** | **15B** | 未公开 | 未公开 | **原生全模态、48T token** | ✅ |
| **GLM-5.1** | **2026.04** | **744B** | **~42B** | **256** | **8** | **昇腾训练、8h长程任务、SWE-bench Pro 77.8%** | ✅ |
| **ERNIE 5.0** | **2026.01** | **2.4T** | **~70B** | 未公开 | 未公开 | **原生全模态、弹性训练、模态无关路由** | ❌ |
| Mistral Large 3 | 2025.12 | 675B | ~41B | 128 | 未公开 | Granular MoE、Dense→MoE回归 | ✅ |
| Mistral Small 4 | 2026.03 | 119B | 6.5B | 128 | 4 | 激活比5.5%、四合一 | ✅ |
| Llama 4 Scout | 2025 | 109B | 17B | 16 | 未公开 | Meta首个MoE、10M上下文 | ✅ |
| Llama 4 Maverick | 2025 | 400B | 17B | 128 | 未公开 | 1M上下文 | ✅ |
| Kimi K2 | 2025.07 | 1T | 32B | 384+1 | 8 | 首个开源1T MoE、MuonClip | ✅ |
| **Kimi K2.6** | **2026.04** | **1T** | **32B** | **256+1** | **8** | **Agent Swarm 300智能体、13h连续编码** | ✅ |
| GPT-4 (传闻) | 2023.03 | ~1.8T(传闻) | ~280B(传闻) | 16(传闻) | 2(传闻) | — | ❌ |
| Grok-1 | 2024.03 | 314B | ~86B | 8 | 2 | 大规模开源 | ✅ |
| **Grok-4.20** | **2026.03** | 未公开 | 未公开 | 未公开 | 未公开 | **4-Agent辩论、78%非幻觉率** | ❌ |
| Gemini 3.1 Pro | 2026.02 | ~万亿(传闻) | ~10% | 未公开 | 未公开 | TPU全自研、ARC-AGI-2 77.1% | ❌ |
| Claude Opus 4.6 | 2025-2026 | 未公开 | — | — | — | Dense，非 MoE | ❌ |
| **Gemma 4-26B** | **2026.04** | **26B** | **4B** | **128+1** | **8** | **Google首个开源MoE** | ✅ |

### 4.3 关键技术路线分化

当前 MoE 模型在三个关键设计维度上出现了明显的路线分化：

#### 路由方式

- **Token-choice（token 选专家）**：主流方案。每个 token 经过 Router 后，选 top-K 个得分最高的专家。Mixtral、DeepSeek、Qwen 都用这个方式。
- **Expert-choice（专家选 token）**：研究阶段的方案。让专家根据自身能力"挑选"擅长的 token。理论上可以实现更自然的专业化分工，但工程上复杂，目前没有主流模型采用。
- **Hash Routing**：用 hash 函数决定 token 去向。最极端的简化，不需要训练 Router。但完全无法实现语义相关的专家分工，目前只在小规模实验中出现。

#### 负载均衡

- **Auxiliary Loss（辅助损失）**：Mixtral 和大多数早期模型的选择。简单有效，但有损主任务优化。
- **Dynamic Bias（动态偏置）**：DeepSeek 的方案。不影响梯度，理论上更优。但增加了训练过程中的超参数（bias 调整的步长/频率）。
- **Expert Capacity + Drop**：GShard/Switch Transformer 的方案。工程上粗暴有效，但会丢弃 token 浪费训练数据。

#### Expert 组织结构

- **Flat（扁平）**：N 个平等专家，Router 直接选。Mixtral 的方式，简单但限制了专家数量的扩展。
- **Hierarchical（层次化）**：专家分多层树形结构，逐级路由。Sparsely-Gated MoE 的方案，降低大 N 时的路由计算复杂度。
- **Fine-grained + Shared**：DeepSeek 的方案。细粒度 mini-expert 增加组合灵活性，共享专家避免通用知识冗余。

### 4.4 性能对比

以下数据来自各模型的技术报告和社区评测，测试时间标注在括号内。不同评测设置下的分数不完全可比，仅作参照：

| 模型 | MMLU-Pro | HumanEval | AIME 2025 | SWE-bench | LiveCodeBench | 测试时间 |
|------|:--------:|:---------:|:---------:|:---------:|:------------:|---------|
| Mixtral 8x7B | — | 40.2% | — | — | — | 2023.12 |
| Mixtral 8x22B | — | 45.1% | — | — | — | 2024.04 |
| DeepSeek-V3 | 75.9% | ~78% | — | 45.4 | 39.2 | 2024.12 |
| DeepSeek R1 | — | — | 79.8%* | — | — | 2025.01 |
| DeepSeek V3.2 | — | 82.6% | — | 50.8 | — | 2025.12 |
| **DeepSeek V4-Pro** | **87.5%** | — | — | **80.6%** | **93.5%** | **2026.04** |
| Qwen3.5-397B | 87.8% | 90.9% | 91.3% (2026) | 76.4% | 83.6% | 2026.02 |
| Qwen3.6-Plus | — | — | — | — | — | 2026.04 |
| **MiMo-V2.5-Pro** | — | — | — | 未公开 | 未公开 | **2026.04** |
| **GLM-5.1** | — | — | — | **77.8% (Pro)** | — | **2026.04** |
| Mistral Large 3 | 73.1% | 92.0% | 73.6 | — | — | 2025.12 |
| Mistral Small 4 | 78.0% | — | — | — | — | 2026.03 |
| **Kimi K2.6** | — | — | **96.4% (2026)** | **80.2%** | — | **2026.04** |
| GPT-4 | — | 88.4% | — | — | — | 2023.03 |
| **Grok-4.20** | — | — | — | — | — | **2026.03** |
| Gemini 3.1 Pro | 89.5% | — | — | 80.6 | — | 2026.02 |
| Claude Opus 4.6 | ~88% (估) | — | — | 80.8 (估) | — | 2025-2026 |

**注**：不同模型的评测设置和时间不同，分数不完全可比。HumanEval 正在被社区弃用（饱和度过高），新模型倾向报告 LiveCodeBench / SWE-bench。AIME 2025 是数学推理的硬指标。"—"表示该模型未公开对应数据。标注"(估)"为间接推断值。**加粗行**为本次更新新增。`*` R1 的 AIME 数据来自 AIME 2024（79.8%），非 AIME 2025。

### 4.5 开源生态和社区采用

**截至 2026 年 4 月 28 日的竞争态势**：

**DeepSeek V4-Pro**（4 月 24 日发布）以 1.6T/49B 的规格和 Hybrid Attention 架构重新夺回开源标杆地位。SWE-bench 80.6% 匹配 Claude Opus 4.6，API 价格仅为其 1/20。但仅 4 天后（4 月 28 日），**小米 MiMo-V2.5-Pro** 就在开源榜单上与之并列第一。

**Qwen3.5/3.6** 在中文社区影响力巨大，从端侧到云端全覆盖。Qwen3.6-Plus 定位"最强国产编程模型"，¥0.15 生成完整企业网站的成本优势极具吸引力。但在全球开源榜单上被 DeepSeek V4 和 MiMo 压制。

**GLM-5.1** 的政治意义大于技术意义——用 10 万张华为昇腾 910B 训练出国际竞争力模型，证明"去英伟达化"路线可行。API 定价仅为 Claude Opus 4.6 的 1/15。

**Kimi K2.6** 在 Agent 能力上建立了差异化优势——300 智能体并行、13 小时连续编码、5 天自主运维——这些指标在开源模型中暂无对手。综合智能指数排名第四。

**Mistral Small 4**（119B/6.5B 激活）把细粒度 MoE 推到了极致，但社区反馈显存翻倍（从 Small 3.1 到 3.2）是个槽点。Mistral 的欧洲数据主权合规仍是独特卖点。

**Meta Llama 4** 的 MoE 设计偏保守（Scout 仅 16 专家），但 10M 上下文窗口是差异化卖点。许可证非 OSI-open（EU 限制）引发社区争议。

**Google Gemma 4-26B**（2026.4）是 Google 首个开源 MoE 模型——128 专家 + 1 共享，激活 8 个，26B/4B 激活。标志着 Google 开始重视开源 MoE 生态。

**Grok-4.20** 的 4-Agent 辩论架构是当前最激进的推理架构实验——不是让一个模型想得更深，而是让多个模型互相质疑。78% 非幻觉率是目前行业最高。

### 4.6 MoE 的五个未解决问题

尽管 MoE 在 2024-2026 年取得了巨大成功，但几个根本性问题还没有被完全解决：

**1. 推理显存**：所有 expert 必须常驻显存。一个 671B 的 MoE 模型推理需要至少 400GB+ 显存（FP8），而同等激活参数量的 Dense 模型只需要 ~80GB。EP（Expert Parallelism）缓解了这个问题，但增加了通信延迟。CPU offloading（把不常用的 expert 放 CPU 内存，用时加载）在 2025 年有一些进展，但离"好用"还有距离。

**2. 微调和量化**：MoE 模型的微调（尤其是 QLoRA）比 Dense 模型更容易过拟合。量化的难度也很大——每个 expert 的激活分布可能不同，做统一量化会损失精度，做逐个 expert 量化又太复杂。2025 年下半年有一些针对 MoE 的量化方案（如 SmoothQuant-MoE），但还不够成熟。

**3. 专家专业化的本质**：Router 到底学到了什么样的专家分工？理论上是"不同专家擅长不同领域"，但实际分析发现，专家的专业化并没有那么清晰——更像是"不同专家对不同 token 的响应模式不同"，而不是"专家 #3 擅长数学、专家 #7 擅长代码"这样语义可解释的分工。这也意味着我们还没有完全理解 MoE 内部到底在发生什么。

**4. 最优专家数量和 Top-K**：N 应该设多少？K 应该设多少？目前没有理论指导，只有实验经验。而且最优值似乎随模型规模和训练数据规模变化，没有稳定的规律。

**5. 安全对齐**：MoE 的路由机制引入了新的攻击面。研究发现，可以设计 adversarial input 来操纵 Router 走向特定专家，产生有害输出。目前没有专门针对 MoE 路由的安全对齐方案。

---

## 五、横纵交汇洞察

### 5.1 历史如何塑造了今天的竞争位置

把纵向演进和横向对比放在一起看，最反直觉的一点是：**Google 在 MoE 技术上领先了 7 年，但今天 MoE 的标杆是 DeepSeek，不是 Google。**

这是怎么发生的？

回头看 Google 的 MoE 论文系列（2017-2022），技术质量极高。Sparsely-Gated MoE 定义了路由框架，GShard 解决了大规模训练的工程问题，Switch Transformer 证明了简化 router 的可行性，ST-MoE 解决了训练稳定性。单论论文贡献，Google 是 MoE 无可争议的开创者。

但 Google 做了三件事，让这些技术积累没能转化为竞争优势：

**第一，所有技术都停留在内部系统。** 2022 年之前的 Google MoE 工作，没有任何一个公开了可用的模型权重或 API。研究者可以在论文里读到 Switch Transformer 的设计，但没有一个"开箱即用"的 Switch Transformer 让他们体验。

**第二，搜索业务主导的组织结构。** Google Brain 和 DeepMind 的 MoE 研究，首要目标是改善 Google 自己的搜索、翻译、广告等产品。公开论文和 API 是副产品，不是核心目标。这和 OpenAI 的"把 AGI 带到全世界"形成鲜明对比。

**第三，对开源的路径依赖式低估。** Google 习惯了用论文建立学术影响力，但 2023 年以后，AI 领域的游戏规则变了——开源模型比论文影响力更大。Mistral 用一条推文 + torrent 链接就在社区建立起了影响力，这是 Google 没有准备好的新战场。

DeepSeek 的崛起，恰恰是在 Google 的三个弱点上做了正确的事：全部开源（权重、技术报告、部分训练细节），组织目标是做出"世界上性价比最高的 AI 模型"而不是服务某个内部业务线，以及深度拥抱开源社区的传播方式。

### 5.2 Anthropic 的 Dense 坚持会是对的吗

横向看 MoE 阵营，几乎所有主要玩家都在用或考虑用 MoE。Anthropic 用 Dense 的选择显得格格不入。

但纵向看，Anthropic 的坚持有充分的历史理由：

2022 年，Anthropic 的人从 OpenAI 离开创立这家公司时，原动力之一就是安全。他们亲历了 GPT-3 训练中的不可控因素，也看到了 MoE 路由引入的新复杂度。在一个你已经无法完全理解内部机制的系统中再引入一个自动路由层，等于增加了一层不可预测性。

Anthropic 的"密集+安全"路线在 2025-2026 年得到了验证：Claude 3.5/4 在大部分 benchmarks 上不输给 MoE 模型，而且在安全对齐方面表现出了更一致的稳定性。

我的判断是：Anthropic 的 Dense 坚持在短期内（1-2 年）不会成为劣势。但随着 MoE 推理生态的进一步发展（EP、offloading、量化），MoE 的训练效率优势可能会越来越难被忽视。长期看（3-5 年），Anthropic 可能需要在某个节点做出选择——是否转向某种"受控的 MoE"（比如更少专家、更强的路由解释性、专门的安全对齐方案）。

### 5.3 DeepSeek V4 与 MiMo 的开源榜首之争

DeepSeek-V3 在 2024 年底获得的关注度接近于一个小型"Sputnik 时刻"。但到了 2026 年 4 月，竞争格局发生了深刻变化：

**架构创新已经被广泛模仿**。Fine-grained expert + Shared expert + 无 auxiliary loss 的组合，已经成为 Qwen、MiMo、GLM、Kimi 的标准配置。当所有人都用同样的架构方案时，架构就不再是护城河。

**开源榜首的持续时间急剧缩短**。DeepSeek-V3 在 2024.12-2025.8 独占开源榜首约 8 个月。而 DeepSeek V4-Pro（4 月 24 日发布）仅 4 天后就被 MiMo-V2.5-Pro（4 月 28 日）在 Artificial Analysis 上并列第一。开源模型的竞争节奏已经从"年"压缩到了"天"。

**训练成本优势被广泛复制**。V3 的 $5.6M 训练成本确实惊艳，但 GLM-5.1 用华为昇腾 910B（性能低于 H800）也训练出了国际竞争力模型，ERNIE 5.0 的弹性训练策略让"一次训练处处部署"成为可能。低成本训练正在从 DeepSeek 的独门绝技变成行业基本功。

**DeepSeek V4 的 Hybrid Attention（CSA+HCA）是一个真正的差异化优势**——73% FLOPs 降低、90% KV Cache 缩减——这是其他开源模型尚未复现的能力。但这个窗口期有多长？Qwen 的 GatedDeltaNet 和 MiMo 的 SWA+GA 混合注意力也在走类似的技术路线。

**开源的双刃剑依然锋利**。V4-Pro 的 MIT 开源让它获得了巨大的社区影响力，但也意味着任何人都能基于它做改进。华为昇腾、寒武纪的 Day 0 适配既是对 DeepSeek 生态地位的承认，也意味着这个模型不再只属于 DeepSeek。

### 5.4 2026 年 4 月的新变数

如果把时间切到 2026 年 4 月 28 日（报告撰写当天），有几个结构性变化值得标记：

**中国 MoE 开源力量已经形成了"集团军"**。DeepSeek V4、Qwen3.6、MiMo-V2.5、GLM-5.1、Kimi K2.6——五家中国公司在 2026 年 4 月同时拥有国际竞争力的开源 MoE 模型。这不是一家公司的胜利，而是一个生态系统的成熟。2024 年的 MoE 故事是"DeepSeek 单挑 OpenAI"，2026 年的故事是"中国开源 MoE 军团 vs 硅谷闭源阵营"。

**开源榜首的"日更"时代到来**。4 月 24 日 DeepSeek V4-Pro 登顶，4 月 28 日 MiMo-V2.5-Pro 并列第一。5 月谁会登顶？可能是 Qwen3.6-Max，也可能是 Kimi K2.7。"开源最强"这个称号的保质期正在从"月"变成"天"。

**Agent 能力成为新的差异化战场**。Kimi K2.6 的 300 Agent Swarm、Grok-4.20 的 4-Agent 辩论、GLM-5.1 的 8 小时自主任务——各自的 Agent 路线截然不同，但都指向同一个方向：不再比"模型知不知道"，而是比"模型能不能做事"。MoE 的稀疏激活天然适合多 Agent 并行——不同 Agent 走不同 expert，互不干扰。

**"去英伟达化"路线的可行性被验证**。GLM-5.1 用 10 万张华为昇腾 910B 训练出国际竞争力模型，ERNIE 5.0 用百度昆仑芯。这可能是 MoE 训练史上最被低估的事件——它证明 MoE 的训练不再需要英伟达 GPU 垄断。

### 5.5 未来推演：三个剧本

**剧本 A：最可能（MoE 开源生态多极化）——概率 55%**

到 2027 年，MoE 开源生态不再是 DeepSeek 一家独大，而是 DeepSeek / Qwen / MiMo / GLM / Kimi 五家争鸣，每家在不同维度建立优势（DeepSeek 架构创新、Qwen 语言覆盖、MiMo 端侧部署、GLM 国产算力、Kimi Agent 能力）。

闭源阵营（OpenAI/Google/Anthropic）在安全敏感和企业级场景保持优势，但开源 MoE 在性价比和可定制性上持续蚕食市场。MoE 推理生态完全成熟，Expert Offloading 和 FP4 量化让 1T+ MoE 模型能在消费级硬件上运行。

**剧本 B：最危险（MoE 同质化 + 价格战）——概率 25%**

架构创新窗口关闭。2026 年下半年到 2027 年，所有开源 MoE 模型都用同样的 Fine-grained + Shared Expert + Hybrid Attention 方案，差异化消失。竞争退化为价格战——API 定价降到接近电力成本。

DeepSeek、Qwen、MiMo 等依靠低价吸引用户但无法盈利，部分公司退出开源 MoE 市场或回归闭源。MoE 成为"大厂的游戏"——只有云厂商（阿里云、华为云、AWS）能靠基础设施利润补贴模型成本。

**剧本 C：最乐观（MoE 让 AI 能力民主化）——概率 20%**

MoE 的训练效率优势 + 开源生态的竞争，使训练 GPT-4 级别模型的成本降到 50 万美元以下（从 2024 年的 $5.6M 再降一个量级）。全球涌现出几十个高质量的开源 MoE 模型，覆盖不同语言、不同领域、不同文化背景。

在这个剧本里，MoE 的稀疏性不只是一种架构优化——它改变了"谁能做 AI"的经济模型。小公司甚至大学实验室可以训练"自己领域的 DeepSeek"，因为 MoE 让他们只需要增加 expert 而不需要线性增加计算量。AI 的能力不再是少数公司的垄断，而是一个开放的基础设施。

### 5.6 最后的话

MoE 的故事有一个迷人的内核：一个 1991 年提出的古老想法，经过 30 多年的兜兜转转，在 2023-2025 年突然成为 AI 架构的核心选择，然后在 2026 年 4 月进入了"日更"时代。

站在 2026 年 4 月 28 日看 MoE 的竞争格局，最震撼的不是某个模型的技术指标，而是**开源迭代的速度**。DeepSeek V4-Pro 发布 4 天后就被 MiMo-V2.5-Pro 追平。GLM-5.1 证明华为芯片能训练国际竞争力 MoE。Kimi K2.6 证明 Agent Swarm 不是科幻。Grok-4.20 证明让模型互相辩论能降低幻觉。

短短一周内，MoE 的天花板被敲了四次。

这让我们想起另一个花了 30 年才爆发的技术：神经网络本身。1986 年反向传播算法被提出，但直到 2012 年 AlexNet 才证明了它的价值。之间差的不是算法，是算力和数据。

但 MoE 的故事有一点不同：它不是在某个"天才时刻"爆发的，而是在无数工程师的持续优化中一步步验证的。从 Shazeer 2017 年的 Noisy Top-K Gating，到 DeepSeek 的无辅助损失负载均衡，到 MiMo 的混合注意力——每一步都是渐进式的工程改进。**伟大的技术革命不一定是天才的灵光一闪，更多时候是一群人在正确的方向上持续推了三十年。**

---

## 六、信息来源

| 来源 | 类型 | URL / 出处 |
|------|------|-----|
| Adaptive Mixtures of Local Experts (1991) | 论文 | Jacobs, Jordan, Nowlan, Hinton — Neural Computation 3(1) |
| Hierarchical Mixtures of Experts (1994) | 论文 | Jordan & Jacobs — Neural Computation 6(2) |
| Deep Mixture of Experts (2013) | 论文 | Eigen, Ranzato, Sutskever — arXiv:1312.4314 |
| Exploring the Limits of Language Modeling (2016) | 论文 | Jozefowicz, Shazeer et al. — arXiv:1602.02410 |
| Sparsely-Gated MoE (2017) | 论文 | https://arxiv.org/abs/1701.06538 |
| GShard (2020) | 论文 | https://arxiv.org/abs/2006.16668 |
| Switch Transformer (2021) | 论文 | https://arxiv.org/abs/2101.03961 |
| GLaM (2021) | 论文 | https://arxiv.org/abs/2112.06905 |
| ST-MoE (2022) | 论文 | https://arxiv.org/abs/2202.08906 |
| Mixtral 8x7B (2023) | 官方博客 | https://mistral.ai/news/mixtral-of-experts/ |
| Grok-1 (2024) | 官方博客 | https://x.ai/blog/grok-os |
| DeepSeek-V2 (2024) | 技术报告 | https://arxiv.org/abs/2405.04434 |
| DeepSeek-V3 (2024) | 技术报告 | https://arxiv.org/abs/2412.19437 |
| DeepSeek R1 (2025) | 论文 | Nature 封面 (2025.9) / arXiv:2501.12948 |
| DeepSeek V3.1 (2025) | 官方公告 | DeepSeek API Docs / 社区报道 |
| DeepSeek V3.2 (2025) | 技术报告 | arXiv:2512.02556 |
| DeepSeek V4 (2026.04) | 官方发布 | https://developer.nvidia.com/blog/build-with-deepseek-v4-using-nvidia-blackwell-and-gpu-accelerated-endpoints/ |
| DeepSeek mHC | 论文 | arXiv:2512.24880 |
| Qwen3-MoE / Qwen3.5 | 官方博客 | https://qwenlm.github.io/blog/ |
| Qwen3-Next | NVIDIA 博客 | https://developer.nvidia.com/blog/new-open-source-qwen3-next-models/ |
| Qwen3.6-Plus (2026.04) | 阿里云官宣 | https://developer.aliyun.com/article/1724039 |
| Xiaomi MiMo-V2.5 (2026.04) | 官方开源 | https://ai.zol.com.cn/1172/11726996.html / HuggingFace: Xiaomi-MiMo |
| Zhipu GLM-5.1 (2026.04) | 官方发布 | https://m.ithome.com/html/937186.htm |
| Baidu ERNIE 5.0 (2026.01) | 技术报告 | https://www.aitop100.cn/wenxin5.0 / arXiv:2602.04705 |
| Mistral Large 3 / Small 4 | 官方博客 | https://mistral.ai/ |
| Kimi K2 | GitHub | https://github.com/moonshotai/Kimi-K2 |
| Kimi K2.6 (2026.04) | 官方发布 | https://www.zdnet.com/article/moonshot-ai-kimi-k2-6-swarms-complex-tasks-collaborating-agents/ |
| Llama 4 Scout/Maverick | Meta 官方 | Meta AI 博客 |
| Google Gemma 4-26B (2026.04) | 官方发布 | Google AI 博客 |
| Gemini 3.1 Pro (2026.02) | ZDNET 等 | https://www.zdnet.com/article/google-gemini-3-1-pro-release-ai-model/ |
| Grok-4.20 Beta (2026.03) | 官方/社区 | https://www.eweek.com/news/grok-4-20-multi-agent-ai-debate-architecture/ |
| ByteDance Seed 2.0 (2026.02) | 官方博客 | https://seed.bytedance.com/zh/blog/seed2-0 |
| Anthropic Dense 选择 | 官方博客/访谈 | Anthropic 技术博客、Dario Amodei 公开访谈 |
| GPT-4 MoE 传闻 | 社区分析 | George Hotz 播客、SemiAnalysis |
| Artificial Analysis 开源排名 (2026.04) | 评测 | https://artificialanalysis.ai/ |
| vLLM MoE 支持 | 项目文档 | https://docs.vllm.ai/ |
| SGLang MoE 优化 | 项目文档 | https://sglang.readthedocs.io/ |
| Prem AI 2026 LLM 指南 | 评测 | https://blog.premai.io/12-best-open-source-llms-for-production-in-2026/ |

---

> 本报告采用**横纵分析法**（Horizontal-Vertical Analysis）撰写，融合语言学中的历时-共时分析、社会科学中的纵向-横截面研究设计、以及竞争战略分析的核心思想，由数字生命卡兹克（Khazix）提出。
