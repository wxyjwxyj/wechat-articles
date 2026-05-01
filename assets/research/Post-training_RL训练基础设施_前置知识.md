# Post-training / RL 训练基础设施 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉 RLHF（Reinforcement Learning from Human Feedback）、DPO（Direct Preference Optimization）、GRPO（Group Relative Policy Optimization） 等概念，可以直接翻阅主报告。

---

## 一、Post-training 是什么？

大模型的训练分为两个阶段：

1. **预训练（Pre-training）**：在海量文本上训练，让模型学会语言和知识。成本极高（数千万到数亿美元）。
2. **Post-training（训练后优化）**：在预训练好的模型上做进一步优化，让它"听话"、会推理。成本较低但极其复杂。

预训练让模型"有知识"，post-training 让模型"有能力"。

Post-training 包括：**指令微调**（让模型学会回答格式）、**对齐**（让模型输出符合人类偏好）、**推理训练**（让模型学会思考过程）。

---

## 二、对齐（Alignment）

模型预训练之后，能力已经有了但行为可能不符合预期。对齐就是"让模型做人类想让它做的事"。

**不对齐的例子**：用户问"怎么偷车"，模型回答详细步骤。
**对齐后的例子**：模型回答"偷车是违法行为，我不能帮你"。

对齐的主流方法有三代：

### 强化学习（Reinforcement Learning，RL）基础

强化学习是机器学习的一个分支。核心概念：智能体（Agent）在环境中做动作（Action），环境给它奖励（Reward）或惩罚作为反馈，智能体通过试错学习调整行为策略，目标是最大化累积奖励。

打一个直觉比方：训练狗。狗做对了（坐下），主人给零食（正奖励）；狗做错了（乱跑），主人说"no"。狗不是被告知"你应该怎么做"——它是通过"什么动作能得到奖励"自己总结经验。RL 训练大模型也是同一个逻辑：模型生成回答 → 打分 → 根据分数更新参数，让模型越来越偏向能得高分的回答。

### RLHF（Reinforcement Learning from Human Feedback）

2022 年 InstructGPT 提出的方法（Ouyang et al., 2022），三步骤：
1. 人类对模型的不同输出打分（偏好标注）
2. 训练一个奖励模型（Reward Model），学会预测人类会怎么打分
3. 用 **PPO（Proximal Policy Optimization，近端策略优化）** 算法优化原始模型，让它的输出获得更高奖励

PPO 是目前最常用的 RL 算法之一（Schulman et al., 2017）。它的核心思想是"小步更新"——每次只允许模型参数做微小的调整，防止模型"步子迈太大"导致崩溃或性能突然下降。打个比方：不是让狗一天学会所有指令，而是一个指令一个指令慢慢教，每次只奖励一点点进步。

**工程挑战**：训练时需要同时部署 4 个模型（策略模型、参考模型、奖励模型、价值模型）——显存需求极大。

### DPO（Direct Preference Optimization）

2023 年提出的简化方案（Rafailov et al., 2023），跳过"训练奖励模型"这一步，直接用偏好数据优化原始模型。

**工程好处**：从 4 个模型减少到 2 个（Rafailov et al., 2023），训练成本大幅降低。

### GRPO（Group Relative Policy Optimization）

2024 年 DeepSeek 提出的方案（Shao et al., 2024），进一步简化——去掉价值模型（critic），用同一批生成的多个回答的相对质量做优化。

**工程好处**：显存需求进一步降低，更适合大规模分布式训练。

---

## 三、推理时计算扩展（Test-time Compute Scaling）

这是 2024-2026 年最重要的 AI 突破之一。

**传统方式**：模型一次推理就给出答案。
**推理时扩展**：模型"多花时间思考"，在给出最终答案之前生成大量中间推理步骤。

OpenAI o1（2024.09）首次展示了这个能力的威力：在数学和编程问题上的准确率大幅提升，但回答时间从几秒增加到几十秒。
DeepSeek-R1（2025.01）开源复现了这个能力（Guo et al., 2025）。
OpenAI o3（2026.04）更进一步，通过多次采样+验证器筛选来提升准确率。

**关键工程概念**：
- **Best-of-N**：模型生成 N 个答案，选最好的那个（最简单但最贵的方式）
- **PRM（Process Reward Model）**：不只给最终答案打分，还给每一步推理过程打分
- **MCTS（Monte Carlo Tree Search）**：像下棋 AI 一样，探索多条推理路径

---

## 四、Post-training 的核心工程挑战

为什么 post-training 比预训练更复杂？

**预训练**：数据一次性准备好 → 模型训练 → 出结果。流程是线性的。

**Post-training（尤其是 RL）**：需要在训练中穿插推理步骤：
```
训练循环：
  1. 当前模型生成一批回答（推理阶段，像在跑 inference）
  2. 奖励模型/规则给这些回答打分
  3. 根据分数更新模型参数（训练阶段）
  4. 回到步骤 1——但模型已经变了，需要重新生成回答
```

步骤 1 是在训练流程里跑推理——这意味着你要同时部署推理基础设施（vLLM 等）和训练基础设施（DeepSpeed 等），两者之间要高效通信。这是 post-training 工程实现中最复杂的问题。

---

## 五、主流训练框架

| 框架 | 开发商 | 定位 | 特点 |
|------|--------|------|------|
| **DeepSpeed-Chat** | 微软 | 最早 RLHF 框架 | 2023 年发布，功能全面但已进入维护模式 |
| **TRL** | Hugging Face | 最流行 | 生态集成最好（Hugging Face 全家桶），适合中小规模 |
| **NeMo-Aligner** | NVIDIA | 企业级 | GPU 优化最好，但已归档 |
| **OpenRLHF** | 开源社区 | 算法支持最全 | 支持 RLHF/DPO/GRPO 多种算法 |
| **VeRL** | 火山引擎/字节 | 大规模训练 | GPT-5/R1 等训练的底层框架 |
| **LLaMA Factory** | 开源社区 | 微调+对齐 | 最受欢迎（71k stars），低门槛 |

---

## 六、一个简单直觉

```
预训练 = 让模型上学（学知识、学语言）
Post-training = 让模型参加特训班（学会考试技巧、学会礼貌）

RLHF = 特训班有老师打分
  复杂：需要 4 个老师（模型）同时在场

DPO = 特训班看优秀作业自己学
  简单：只看别人的好回答就够了

GRPO = 特训班同学互评
  更简单：不看老师，看同学里谁答得好

推理时扩展 = 考试时多打草稿再交卷
  o1/R1 = 打草稿（chain of thought）
  o3 = 打 10 份草稿选最好的（best-of-N +验证）
```

Post-training 的工程核心就是在"怎么让特训班跑得更快更省显存"这件事上做文章。

---

## 参考来源

- **Training language models to follow instructions with human feedback (InstructGPT)** (Ouyang et al., 2022) — OpenAI 首次提出完整的 RLHF 三步骤流程：偏好标注→奖励模型→PPO 优化，是对齐训练的基础 — [arXiv:2203.02155](https://arxiv.org/abs/2203.02155)
- **Proximal Policy Optimization Algorithms** (Schulman et al., 2017) — 提出 PPO 算法，通过"小步更新"策略实现稳定高效的强化学习训练 — [arXiv:1707.06347](https://arxiv.org/abs/1707.06347)
- **Direct Preference Optimization** (Rafailov et al., 2023) — 跳过奖励模型的新范式，将 RLHF 从 4 模型简化为 2 模型，大幅降低工程复杂度 — [arXiv:2305.18290](https://arxiv.org/abs/2305.18290)
- **DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open-Source LLMs** (Shao et al., 2024) — DeepSeek 在此工作中首次提出 GRPO 算法，去掉价值模型进一步降低显存需求 — [arXiv:2402.03300](https://arxiv.org/abs/2402.03300)
- **DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning** (Guo et al., 2025) — 开源复现 o1 式推理能力，验证了 GRPO 在大规模推理训练中的有效性 — [arXiv:2501.12948](https://arxiv.org/abs/2501.12948)
