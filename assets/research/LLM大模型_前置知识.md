# LLM 大模型 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉语言模型的基本概念，可以直接翻主报告。

> 🎯 **读完这篇你能**：根据任务需求和预算约束，从参数量、上下文窗口、涌现能力三个核心维度评估和选择合适的大模型。

---

## 一、语言模型是什么？

语言模型就是"会预测下一个词的 AI"。

给它"今天天气真"，它预测"好"。
给它"今天天气真好，适合出去"，它预测"散步"。

这个"预测下一个词"的能力训练到极致后，模型开始涌现出理解、推理、对话、编程等能力。没人教过它"2+3=5"，但它在海量文本中见过无数次类似的模式，就能自己学会算术。

---

## 二、关键概念

### 参数（Parameter）

参数是模型内部的"可调节刻度盘"。参数越多，模型能存储的知识和模式越多。简单理解：

- **1亿参数** ≈ 小学课本厚度
- **10亿参数** ≈ 书架
- **1000亿参数** ≈ 图书馆
- **万亿级参数** ≈ 几个大图书馆

当前主流的 LLM 通常在 7B-671B 参数之间（1B = 10亿）。

### Token

模型不认字，只认 token。Token 是模型处理文本的最小单位：
- "Hello world" = 2 个 token
- "你好世界" = 4 个 token
- 100 个 token ≈ 75 个英文单词 ≈ 50 个中文字

### 涌现能力（Emergence）

小模型（<10B 参数）在很多 benchmark 上表现接近随机；当参数规模越过某个阈值后，能力突然跃升——这种现象叫**涌现**。

典型例子：算术推理、多步推理、代码生成、翻译——没人逐条教过模型这些规则，它从海量文本的统计模式中自发学会。

简单类比：**蚂蚁个体很简单，蚁群却很聪明**。单个神经元只能做简单的电信号转换，但 1750 亿个参数（GPT-3 的参数量）（Brown et al., OpenAI, 2020）组合在一起，涌现出了理解、推理、编程等复杂能力。这就是为什么大模型"突然变聪明"——不是有人教了新东西，而是规模带来了质变。

### 上下文窗口（Context Window）

模型一次能"看到"多少内容。从 GPT-1 的 512 token（Radford et al., OpenAI, 2018）到 Gemini 1.5 Pro 的 200 万 token（Google, 2024）——相当于从"只能看一句话"到"能看 20 本书"。

### Transformer

2017 年 Google 提出的神经网络架构（Vaswani et al., 2017）。几乎所有现代 LLM（GPT、Claude、Gemini、Llama）都基于它。

**注意力机制（Attention）** 是 Transformer 的核心创新。简单理解——把它想象成**查图书馆**：

- **Q（Query，查询）**：你的问题，比如"有哪些关于人工智能的书？"
- **K（Key，键）**：书脊上的标签，帮你判断一本书是否相关
- **V（Value，值）**：书的内容本身

模型计算 Q 和每个 K 的匹配度（注意力分数），匹配度高的 V 被重点读取，匹配度低的被忽略。一句话里每个词都有自己的 Q、K、V。

**Self-Attention（自注意力）**：让句子里每个词都能"看到"其他所有词。比如"小明把苹果给了小红，**她**很开心"——Self-Attention 帮模型理解"她"指的是"小红"而非"苹果"。传统模型只能看前文，Self-Attention 同时看整句话的所有位置，这是 Transformer 能理解复杂上下文的关键。

### KV Cache（KV 缓存）

推理时，模型每生成一个新 token，都要和前面所有 token 做 Attention 计算。如果不缓存，每步都得重算之前所有 token 的 Key 和 Value——这是指数级增长的计算浪费。

KV Cache 的做法：每算完一个 token 就把它的 K 和 V 存起来，下次生成直接取用，只需对新 token 做一次计算。

简单类比：你边看书边做笔记，每读完一章就把要点记下来，后面要回顾时看笔记就行，不用再把书重新翻一遍。

**为什么重要**：没有 KV Cache，LLM 推理速度会慢到不可用。这也是长上下文为什么贵——缓存越长，显存占用越大。

### 预训练（Pre-training）

把模型放在海量互联网文本上"读书"。学会语法、知识、推理模式。这步占模型训练成本的 95% 以上（Kaplan et al., OpenAI, 2020）。

### SFT（Supervised Fine-Tuning，监督微调）

预训练让模型"读完了整个互联网"，但此时的模型只会做一件事——预测下一个词。它不知道什么叫"聊天"、什么叫"问答"。

SFT 的做法：用人类写好的高质量"问答对"（比如"用户：光合作用是什么？/ 助手：光合作用是植物利用光能..."）给模型做微调。模型从中学会**对话的格式和风格**——什么时候该解释、什么时候该反问、什么格式用户看得舒服。

简单类比：预训练 = 学完所有课本知识，SFT = 老师教你"考试答题的规范格式"。知识还是那些知识，但表达方式被"格式化"了。

### MoE（混合专家，Mixture of Experts）

传统的 Dense 模型：每个 token 激活全部参数。
MoE 模型：模型内部被分成多个"专家"，每个 token 只激活其中几个。训练成本更低、推理效率更高。2024-2026 年几乎所有新模型都在转向 MoE。

### Few-shot Learning / In-Context Learning（上下文学习）

GPT-3（2020）证明了规模带来的一个重要能力：**不需要重新训练，给几个例子就能学会新任务**。

你不需要修改模型参数，只需在 prompt 里写几个示范（"Q: 苹果的英文是什么？A: apple。Q: 香蕉的英文是什么？A:"），模型就能"理解"当前任务的模式并正确回答。这在 GPT-2 时代几乎不存在，是参数规模突破 100B 后才出现的涌现能力。

简单类比：就像一个考试时能看例题的学生——例题不需要背下来，看两眼知道套路就能照做。这就是为什么 prompt 工程如此重要：你给的上下文就是模型的"例题"。

### 推理时计算扩展（Test-time Compute Scaling）

传统方式：模型一次推理直接给答案。
新方式（o1、DeepSeek-R1）：生成答案前先用更多计算"思考"——类似考试时打草稿。

---

## 三、如何评价一个模型？

| 基准 | 测什么 |
|------|--------|
| **MMLU** | 综合知识（57个学科，从物理到法律）（Hendrycks et al., 2021） |
| **MMLU-Pro** | MMLU 的加强版（更难的推理题）（Wang et al., 2024） |
| **HumanEval** | 写代码的准确率（Chen et al., OpenAI, 2021） |
| **SWE-bench** | 真实软件工程任务（修 Bug）（Jimenez et al., Princeton, 2024） |
| **Chatbot Arena ELO** | 人类主观评分（盲测对比）（Chiang et al., LMSYS, 2024） |
| **MATH/GSM8K** | 数学推理（Hendrycks et al., 2021 / Cobbe et al., 2021） |
| **AIME** | 数学竞赛级别 |

### RLHF（Reinforcement Learning from Human Feedback，基于人类反馈的强化学习）

模型预训练完之后，能力强了但行为不一定符合预期——比如用户问"怎么偷车"，它可能给你详细步骤。RLHF 就是"让模型学会做人"的方法。三步骤：

1. **收集偏好数据**：让人类标注者看 AI 给出的几个不同回答，选出哪个更好
2. **训练奖励模型**：用一个模型来学习"什么样的回答人类喜欢"
3. **PPO 优化**：用奖励模型的分数去更新原始模型参数

RLHF 是目前最主流的对齐方法——ChatGPT、Claude、Gemini 都用了它。但它很贵：训练时需要同时跑 4 个模型（Ouyang et al., 2022）。

### DPO（Direct Preference Optimization，直接偏好优化）

斯坦福 2023 年提出（Rafailov et al., 2023）。传统 RLHF 需要额外训练一个"奖励模型"来打分——训练成本高、过程不稳定。DPO 的核心思路：**跳过奖励模型，直接把"哪个回答更好"的偏好信号编码进模型的损失函数**。

效果与 RLHF 相当，但只需跑一个模型而非四个，训练更简单、更省显存。Llama 3、Qwen 2 等开源模型大量采用 DPO。

### GRPO（Group Relative Policy Optimization，组相对策略优化）

DeepSeek 在 2024 年提出的对齐方法。传统 RLHF 需要训练一个与策略模型同规模的 Critic（评论家）模型来评估好坏——显存直接翻倍。GRPO 的做法：**放弃 Critic 模型。同一道题让模型生成一组回答，组内比较——得分高于组平均的强化，低于组平均的抑制。**

简单类比：不用请老师打分，考完后班内排名，前一半加分，后一半减分。DeepSeek-R1 用 GRPO 训练出了强推理能力，训练成本远低于传统 RLHF。

### Constitutional AI（宪法 AI）

Anthropic 独创的对齐方法（Bai et al., 2022）。核心思路：不用人类标注，而是让 AI 自己对照一份"宪法"（行为准则）来评判自己的输出是否符合规范。比如宪法规定"回答应该无害、诚实、有帮助"，AI 生成回答后自己检查是不是违反了。这减少了对人类标注的依赖，也让对齐过程更可扩展。

---

### Omni（全模态）

"Omni" 来自拉丁语 "omnis"（所有/全部）。GPT-4o 的 "o" 就代表 omni——一个模型同时处理文本、图像、音频、视频。不再是"文本模型 + 图像模块"的拼接，而是从设计之初就把所有模态当作同一种 token 序列来处理。全模态在 2024 年被 GPT-4o 率先商用，到 2026 年已成为旗舰模型的标配。

---

## 四、主流模型一句话

| 模型家族 | 开发商 | 一句话 |
|---------|--------|--------|
| **GPT 系列** | OpenAI | LLM 的定义者和持续领跑者 |
| **Claude 系列** | Anthropic | 安全优先，编程最强，全面且可靠 |
| **Gemini 系列** | Google | 原生多模态，超长上下文（2M） |
| **Llama 系列** | Meta | 开源大模型的旗帜 |
| **DeepSeek 系列** | 深度求索 | 中国开源效率革命，训练成本仅为同级 1/10 |
| **Qwen 系列** | 阿里巴巴 | 中国最强开源多模态，迭代速度极快 |
| **Mistral 系列** | Mistral AI | 欧洲最强，参数利用率极高 |
| **Grok 系列** | xAI | 马斯克的"叛逆"AI，实时接入 X 平台 |

---

## 五、一个简单直觉

```
LLM 的进化史 = 从"鹦鹉学舌"到"能推理"

2018-2020（GPT-1→GPT-3）：能流畅说话了，但不懂逻辑
2022（ChatGPT）：会聊天了，能回答问题
2023（GPT-4）：通过律师考试了，能看懂图片
2024（GPT-4o/Gemini/DeepSeek-V3）：能实时语音对话，开源追平闭源
2025（R1/o1）：学会"思考"了——回答前先推理
2026 年的状态：
- 最强模型在大多数基准上超过人类平均水平
- 开源模型在各项能力上与闭源模型差距大幅缩小
- 推理成本持续下降，端侧部署日益可行
- 竞争焦点从"谁能做"转向"谁更安全、更可控、更便宜"
```

LLM 大模型在 2026 年是整个 AI 生态的基石——所有 AI Agent、AI 搜索、AI 编程、多模态应用，底层都是 LLM 在驱动。

---

## 参考来源

- **Attention Is All You Need** (Vaswani et al., 2017) — Transformer 架构的奠基论文，提出了自注意力机制和编码器-解码器结构 — https://arxiv.org/abs/1706.03762
- **Scaling Laws for Neural Language Models** (Kaplan et al., OpenAI, 2020) — 首次系统量化模型参数、数据量和训练算力之间的幂律关系 — https://arxiv.org/abs/2001.08361
- **Language Models are Few-Shot Learners (GPT-3)** (Brown et al., OpenAI, 2020) — 175B 参数 GPT-3 的技术报告，验证了规模带来的涌现能力 — https://arxiv.org/abs/2005.14165
- **Training language models to follow instructions with human feedback** (Ouyang et al., OpenAI, 2022) — InstructGPT / RLHF 的原始论文，奠定了基于人类反馈的强化学习对齐方法 — https://arxiv.org/abs/2203.02155
- **Constitutional AI: Harmlessness from AI Feedback** (Bai et al., Anthropic, 2022) — Anthropic 的宪法 AI 方案，用 AI 自监督替代人类标注进行对齐训练 — https://arxiv.org/abs/2212.08073
- **GPT-4 Technical Report** (OpenAI, 2023) — GPT-4 技术报告，包含 MMLU/HumanEval 等基准评测结果 — https://arxiv.org/abs/2303.08774
- **Measuring Massive Multitask Language Understanding (MMLU)** (Hendrycks et al., 2021) — 提出 MMLU 基准，覆盖 57 个学科的综合知识评测 — https://arxiv.org/abs/2009.03300
- **Measuring Mathematical Problem Solving With the MATH Dataset** (Hendrycks et al., 2021) — 提出 MATH 数学推理基准 — https://arxiv.org/abs/2103.03874
- **MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark** (Wang et al., 2024) — MMLU 加强版，推理题更难 — https://arxiv.org/abs/2406.01574
- **Evaluating Large Language Models Trained on Code** (Chen et al., OpenAI, 2021) — 提出 HumanEval 基准，开创 AI 代码生成系统性评测 — https://arxiv.org/abs/2107.03374
- **SWE-bench: Can Language Models Resolve Real-World GitHub Issues?** (Jimenez et al., Princeton, 2024) — AI 编程领域事实标准评测，用 2294 个真实 GitHub Issue 衡量模型修 Bug 能力 — https://arxiv.org/abs/2310.06770
- **Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference** (Chiang et al., LMSYS, 2024) — 基于人类盲测偏好的 LLM 评测平台 — https://arxiv.org/abs/2403.04132
- **Training Verifiers to Solve Math Word Problems (GSM8K)** (Cobbe et al., OpenAI, 2021) — 提出 GSM8K 小学数学推理基准 — https://arxiv.org/abs/2110.14168
- **Improving Language Understanding by Generative Pre-Training (GPT-1)** (Radford et al., OpenAI, 2018) — GPT-1 技术报告，首次验证大规模生成式预训练的有效性 — https://openai.com/research/language-unsupervised
- **Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context** (Google, 2024) — Gemini 1.5 技术报告，率先实现 1M+ token 上下文窗口 — https://arxiv.org/abs/2403.05530
