# Post-training / RL 训练基础设施横向竞争图谱（2026 年 4 月）

> 对齐方法（RLHF/DPO/GRPO/Reinforce）的工程实现对比与分析
>
> 调研日期：2026-04-30

---

## 一、总览：训练框架全景对比

### 1.1 框架一览表

| 框架 | 开发方 | GitHub Stars | 创建时间 | 核心定位 | 当前状态 |
|------|--------|-------------|---------|---------|---------|
| DeepSpeed | Microsoft | ~42k | 2020 | 分布式训练+推理优化库 | 活跃，DeepSpeed-Chat 子模块 |
| TRL | HuggingFace | 18.2k | 2020-03 | RLHF 后训练库 | 活跃，v1.3（2026-04） |
| NeMo-Aligner | NVIDIA | 853 | 2023-09 | 企业级对齐训练 | **已归档（Public archive）** |
| OpenRLHF | 开源社区 | 9.4k | 2023-07 | 高性能 Agentic RL 框架 | 活跃，v0.10（2026-04） |
| VeRL | 字节跳动 | ~21k | 2024 | 灵活高效的 RL 后训练 | 活跃，GTC26 展示 |
| LLaMA Factory | 开源社区 | ~71k | 2023 | 统一高效微调框架 | 活跃，支持 100+ 模型 |

### 1.2 框架详情分析

---

#### DeepSpeed-Chat（微软）

**GitHub**: https://github.com/microsoft/DeepSpeed  
**论文**: https://arxiv.org/abs/2308.01320  
**许可证**: Apache-2.0

DeepSpeed-Chat 是业界最早的 RLHF 分布式训练框架，由微软 DeepSpeed 团队在 2023 年 4 月推出。它基于 InstructGPT 的三阶段流水线：SFT → Reward Model Fine-tuning → RLHF (PPO)，实现了端到端的 RLHF 训练。

**核心创新**：DeepSpeed Hybrid Engine（DeepSpeed-HE）统一了训练和推理引擎。在 RLHF 的 PPO 阶段，模型需要交替进行 rollout generation（推理）和 policy update（训练），DeepSpeed-HE 能从 ZeRO-Inference 和 ZeRO-Training 之间无缝切换，同时利用 Tensor Parallelism 和 transformer kernel 优化推理性能。

**训练成本数据**（来自官方 benchmark）：

| GPU 配置 | OPT-6.7B | OPT-13B | OPT-30B | OPT-66B | OPT-175B |
|---------|----------|---------|---------|---------|---------|
| 8x A100-40GB | 5.7h | 10.8h | 1.85天 | N/A | N/A |
| 8x A100-80GB | 4.1h ($132) | 9h ($290) | 18h ($580) | 2.1天 ($1620) | N/A |
| 64x A100-80GB | N/A | 1.25h ($320) | 4h ($1024) | 7.5h ($1920) | 20h ($5120) |

以上为 Step 3（RLHF）的训练时间，基于 135M tokens（67.5M query + 67.5M generated），global batch size 0.5M tokens。

**核心局限**：
- 仅支持 PPO 算法，不支持 DPO/GRPO 等新方法
- 代码与 DeepSpeed 核心库深度耦合，API 较为底层
- 自 2024 年起社区活跃度下降，新功能迭代慢于 OpenRLHF 和 TRL
- 对 VLM 多模态 RL 支持不足

**适用场景**：已有 DeepSpeed 基础设施的团队、需要进行大规模 PPO 训练的实验室。

---

#### TRL（HuggingFace）

**GitHub**: https://github.com/huggingface/trl  
**文档**: https://huggingface.co/docs/trl/index  
**最新版本**: v1.3（2026-04-26）

TRL（Transformer Reinforcement Learning）是当前最流行的 RLHF 训练库，深度集成 HuggingFace 生态系统（Transformers、PEFT、Datasets、Accelerate）。2025 年发布的 TRL v1 是重大里程碑，标志其从"RLHF 工具"进化为"全面后训练框架"。

**支持的训练方法**：
- `SFTTrainer` — 监督微调
- `GRPOTrainer` — Group Relative Policy Optimization
- `DPOTrainer` — Direct Preference Optimization
- `RewardTrainer` — 奖励模型训练
- `PPOTrainer` — 传统 PPO（即将被 GRPO 替代趋势）
- 其他：KTO、CPO 等

**关键特性**：
- **vLLM/SGLang 集成**：支持在 rollout generation 阶段使用 vLLM 加速推理
- **AsyncGRPO**：异步 GRPO 训练，在 GSM8K 上有验证的超参数配置（2026-04 更新）
- **多模态支持**：通过 HuggingFace Transformers 支持视觉语言模型
- **DeepSpeed + Accelerate**：底层可使用 DeepSpeed ZeRO 阶段 2/3
- **社区生态**：550 open issues、130 open PRs、2700+ forks
- **活跃度**：2752 commits，最近提交在 2026-04-30

**局限**：
- 对大规模分布式的支持不如 OpenRLHF/VeRL（主要依赖 HuggingFace Accelerate）
- GRPOTrainer 较新（2025 下半年引入），生产验证不如 PPO 充分
- 单框架的 rollout generation 性能不如 vLLM 原生方案

**适用场景**：中小规模团队、快速原型验证、与 HuggingFace 生态紧密配合的项目。

---

#### NeMo-Aligner（NVIDIA）— ⚠️ 已归档

**GitHub**: https://github.com/NVIDIA/NeMo-Aligner  
**状态**: **Public Archive（公共归档）**

NeMo-Aligner 是 NVIDIA 基于 NeMo 框架构建的企业级对齐训练工具包。它利用 Megatron-LM 实现大规模分布式训练，支持数百到数千 GPU 的扩展。

**曾支持的功能**：
- RLHF（PPO）— 基于 NeMo 的分布式训练后端
- DPO — 直接偏好优化
- SteerLM — NVIDIA 提出的可控制模型行为的方法
- SFT — 监督微调

**归档原因分析**：
NeMo-Aligner 在 2025-2026 年间被归档，推测原因：① NVIDIA 的资源转向了更新的项目（如 NeMo 2.0 或其它内部工具）；② 开源社区在 RLHF 框架上的竞争加剧，NeMo-Aligner 的 853 stars 难以与 TRL/OpenRLHF 竞争；③ NVIDIA 可能将对齐能力集成到 NeMo 核心框架中而非独立维护。

**对生态的影响**：
- 已部署 NeMo-Aligner 的团队需要迁移方案
- 社区不再有新功能贡献和 bug 修复
- 建议新项目使用 TRL 或 OpenRLHF 替代

---

#### OpenRLHF（开源社区）

**GitHub**: https://github.com/OpenRLHF/OpenRLHF  
**文档**: https://openrlhf.readthedocs.io/  
**最新**: v0.10（2026-04）

OpenRLHF 是目前发展最快、架构设计最现代的 RLHF 框架之一。它自称"首个结合 Ray + vLLM 分布式架构的高性能开源 RLHF 框架"，采用统一的基于 Agent 的设计范式。

**支持的算法**：
- PPO（经典近端策略优化）
- REINFORCE++（带 baseline 的策略梯度改进版）
- GRPO（Group Relative Policy Optimization）
- RLOO（Reinforce Leave-One-Out）
- DAPO（Dynamic Advantage Policy Optimization）

**关键里程碑**（2026 年）：
- **VLM RLHF 支持**：训练 Qwen3.5 等视觉语言模型，端到端图像输入训练
- **Multi-Turn VLM RL**：多步交互，prompt 和环境反馈中均包含图像
- **ProRL V2**：NVIDIA 使用 REINFORCE++ 训练 1.5B reasoning 模型
- **ScaleRL**（arxiv: 2510.13786）：验证 REINFORCE++ 在大规模训练场景的有效性

**架构优势**：
1. **Ray 分布式调度**：天然支持多节点扩展，Actor/Reference/Critic/Reward 模型可分布在 Ray actor 上
2. **vLLM 集成**：rollout generation 使用 vLLM 的 continuous batching
3. **Hybrid Engine**（类似 DeepSpeed-HE）：在训练和推理间自动切换
4. **Agent-based 设计**：统一 agent 执行流水线，支持单轮和多轮交互
5. **LoRA 支持**：参数高效微调

**适用场景**：需要大规模分布式 RL 训练、希望使用最新算法（REINFORCE++/GRPO）、需要多模态 RL 支持、对生产级稳定性和性能有要求的团队。

---

#### VeRL（字节跳动/火山引擎）

**GitHub**: https://github.com/volcengine/verl  
**文档**: https://verl.readthedocs.io/  
**Stars**: ~21k（增长最快的 RL 训练框架之一）

VeRL（Volcano Engine Reinforcement Learning for LLMs）的正式名称为 **HybridFlow**，是字节跳动开源的高性能 RL 后训练框架。2429 次提交、21k stars 表明其社区活跃度极高。

**核心架构**：
- **训练后端**：FSDP、FSDP2、Megatron-LM 三种选择
- **Rollout 生成**：vLLM（>= 0.8.2）、SGLang、HF Transformers
- **独特的 HybridFlow 设计**：将 RL 训练流程拆分为可组合的算子

**关键特性**：
- **灵活的后端切换**：FSDP 适合中小规模快速实验，Megatron-LM 适合超大模型训练
- **vLLM >=0.8.2 支持**：避免 0.7.x 的 OOM bug
- **DeepSeek 671B 优化**：Megatron 后端适配 DeepSeek 级别的大模型（issue #1033）
- **LoRA + Router Replay**：在 PyTorch Conference Europe 2026 展示
- **GTC26 亮相**：NVIDIA 官方会议两个 session 介绍
- **生产级就绪**：火山引擎内部大规模验证

**技术亮点**：
- 与 vLLM 和 SGLang 的集成度业界最高
- 训练/推理引擎解耦，可独立升级
- 完善的性能调优指南（perf tuning guide）

**适用场景**：需要处理超大模型（如 671B DeepSeek）、需要高度可定制的 RL 训练流程、在字节/火山生态中的团队、追求最新技术（SGLang 等）的团队。

---

#### LLaMA Factory（开源社区）

**GitHub**: https://github.com/hiyouga/LLaMA-Factory  
**Stars**: ~71k（所有框架中最高）  
**论文**: ACL 2024

LLaMA Factory 是最受欢迎的 LLM 微调框架，虽有 71k stars 但需注意：**它的核心定位是微调（fine-tuning），而非纯 RL 框架**。它是"微调框架附带了 RL 能力"。

**支持的训练方法**：
- Pre-training（预训练）
- Supervised Fine-Tuning（监督微调）
- **PPO**（基于奖励模型的强化学习）
- **DPO**（直接偏好优化）
- **KTO**（无配对数据的偏好优化）
- **ORPO**（无参考模型的偏好优化）
- Reward Modeling（奖励模型训练）

**核心优势**：
- **LoRA/QLoRA 生态最完善**：支持 2/3/4/5/6/8-bit QLoRA（AQLM/AWQ/GPTQ/HQQ 等）
- **100+ 模型支持**：LLaMA、Qwen3、DeepSeek、Gemma、Phi、GLM 等
- **先进优化器**：GaLore、BAdam、APOLLO、Adam-mini、Muon
- **实用技巧集成**：FlashAttention-2、Unsloth、Liger Kernel、RoPE scaling
- **零代码 CLI + Web UI**：降低使用门槛
- **EasyR1 子项目**：高效的 GRPO 训练（2025-02 发布）

**RL 能力局限**：
- RL 训练是"附加功能"而非核心优化目标
- 不支持大规模分布式 RL 训练（主要在单机/少量 GPU 上运行）
- 不支持 GRPO（需要通过 EasyR1 子项目，非 LLaMA Factory 直接提供）
- rollout generation 性能不如专用 RL 框架
- 主要面向"用 LoRA 微调做对齐"的场景

**适用场景**：个人开发者和小团队快速微调与对齐、需要 LoRA/QLoRA 参数高效微调、非 RL 研究导向的日常微调任务。

---

## 二、算法方法对比

### 2.1 核心算法全景

| 算法 | 奖励模型 | Critic 网络 | 在线 Rollout | 训练稳定 | 内存占用 | 工程复杂度 | 代表框架 |
|------|---------|------------|------------|---------|---------|-----------|---------|
| **PPO (RLHF)** | 需要 | 需要 | 需要 | 中等 | 极高（4模型） | 高 | 所有框架 |
| **DPO** | 不需要 | 不需要 | 不需要 | 高 | 低（2模型） | 低 | TRL, LLaMA Factory |
| **GRPO** | 需要 | 不需要 | 需要 | 高 | 中等（3模型） | 中等 | OpenRLHF, TRL, VeRL |
| **REINFORCE++** | 需要 | 不需要 | 需要 | 中高 | 中等 | 中低 | OpenRLHF |
| **RLOO** | 需要 | 不需要 | 需要 | 中高 | 中等 | 中低 | OpenRLHF |
| **KTO** | 不需要 | 不需要 | 不需要 | 高 | 低 | 低 | TRL, LLaMA Factory |

### 2.2 算法深度分析

#### PPO（RLHF 经典方案）

**论文**: Schulman et al., "Proximal Policy Optimization Algorithms", 2017  
**在 RLHF 中的实现**: InstructGPT (Ouyang et al., 2022)

PPO 是 RLHF 领域最先被大规模验证的算法。该方案需要同时维护 4 个模型：
1. **Actor**（策略模型）：要训练的目标模型
2. **Reference**（参考模型）：冻结的 Actor 副本，用于 KL 散度约束
3. **Reward Model**（奖励模型）：训练得到，对回复打分
4. **Critic**（价值模型）：估计状态价值，降低策略梯度方差

**工程挑战**：
- **显存爆炸**：4 个模型同时加载，70B 模型需要 ~560GB+ 显存（FP16）
- **训练不稳定**：reward hacking、reward 分布漂移、KL 散度崩溃
- **同步复杂性**：trainer 和 rollout 之间需要高效通信
- **混合精度困境**：推理（rollout generation）需要 FP16，训练可能 BF16

**调优经验**（来自各大框架的实践）：
- KL penalty 系数通常在 0.01-0.05
- PPO clip epsilon 0.2
- GAE lambda 0.95
- 学习率 Actor 1e-6 ~ 5e-6，Critic 1e-5 ~ 5e-5
- mini-batch size 通常为 4-8

**现状**: PPO 仍是最受信任的对齐方法，但 GRPO 和 REINFORCE++ 正在快速替代它。

---

#### DPO 及其变体

**论文**: Rafailov et al., "Direct Preference Optimization", NeurIPS 2023  
**变体**: KTO (2024), ORPO (2024), SimPO (2024), IPO (2023)

DPO 的核心洞察是：不需要显式的奖励模型，偏好概率可以写成策略比率的函数。DPO 训练只需两个模型（Actor + Reference），大幅降低显存需求和工程复杂度。

**DPO vs PPO 计算成本（以 7B 模型为例）**：

| 指标 | PPO | DPO | 节省 |
|------|-----|-----|------|
| 模型数量 | 4 | 2 | 50% |
| 单步显存（A100-80GB） | ~240GB | ~120GB | 50% |
| 训练时间（同等数据量） | ~3x | 1x | 67% |
| 实现代码行数 | ~1500+ | ~300+ | 80% |
| 超参数数量 | ~10+ | ~5 | 50% |

**局限性**：
- **静态数据**：DPO 不生成新 trajectory，完全依赖固定偏好数据集
- **分布外泛化**：当 Actor 分布偏离偏好数据分布时，DPO 效果下降明显
- **迭代 DPO**（Iterative DPO / Online DPO）：部分方案引入了在线采样，但增加了复杂度

**各变体对比**：

| 变体 | 差异点 | 优势 | 局限 |
|------|-------|------|------|
| DPO | 基础版本 | 简单有效 | 需要配对偏好数据 |
| KTO | 不需要配对数据 | 只需"好/坏"标签 | 收敛较慢 |
| ORPO | 在 SFT 阶段直接优化偏好 | 一步到位，无需 RM | 偏好数据依赖强 |
| SimPO | 用参考回复长度做正则 | 无需 Reference 模型 | 超参数敏感 |
| IPO | 使用 Identity Preference Optimization | 理论更优美 | 实践中不如 DPO 稳定 |

---

#### GRPO（DeepSeek 方案）

**论文**: DeepSeek, "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning", 2025  
**首次大规模应用**: DeepSeek-R1（2025-01）

GRPO（Group Relative Policy Optimization）由 DeepSeek 提出，核心创新是**放弃 Critic 网络**，用**组内评分**替代价值函数。

**工作原理**：
1. 为每个 prompt 生成 G 个回复（一个 group）
2. 用 Reward Model 对 G 个回复打分
3. 计算 group 内的 mean 和 std 作为 baseline
4. 用 group-normalized advantage 更新策略

**优势**：
- **去掉 Critic 网络**：从 4 模型降为 3 模型（Actor + Reference + Reward），降低 25% 显存
- **天然适配推理任务**：在数学、代码等可自动验证的任务上表现出色
- **避免价值函数偏差**：group baseline 比 learned value function 更稳定

**工程实现注意**：
- G（group size）是关键超参数，通常 8-64，越大 baseline 越准确但计算量线性增长
- Reward model 需要高效部署，因每个 step 要打分 G 次
- DeepSeek-R1 使用 rule-based reward（格式奖励 + 答案正确性）
- TRL 的 AsyncGRPO 支持异步 rollout generation

**GRPO vs PPO 训练成本（70B 模型，128 GPUs）**：

| 指标 | PPO | GRPO |
|------|-----|------|
| 模型数 | 4 | 3 |
| 训练总显存 | ~2.1TB | ~1.6TB |
| 吞吐量 | 基准 | ~1.3x |
| 收敛步数 | 基准 | ~0.8x |

---

#### REINFORCE++ / RLOO

REINFORCE++ 是 OpenRLHF 提出的 REINFORCE 算法改进版本。RLOO（Reinforce Leave-One-Out）是更具体的实现。

**核心思路**：回到最原始的 REINFORCE 算法，但加入现代改进：
- 多个样本的 leave-one-out baseline
- Advantage normalization
- KL 散度约束（与 Reference 模型）
- Token-level 或 sequence-level 奖励

**优势**：
- 工程实现最简（OpenRLHF 中约 200 行核心代码）
- 不依赖 Critic 网络（同 GRPO）
- 支持任意自定义 reward function
- 被 ProRL V2 和 ScaleRL 验证在大规模训练中的有效性

**局限**：
- 样本效率低于 PPO（需要更多 rollout）
- 对 reward model 质量敏感
- leave-one-out baseline 在 group 较小时噪声大

---

### 2.3 Online vs Offline 对比

| 维度 | Online（在线） | Offline（离线） |
|------|---------------|----------------|
| 代表算法 | PPO, GRPO, REINFORCE++ | DPO, KTO, ORPO |
| 数据来源 | 训练中实时生成 rollout | 固定偏好数据集 |
| 分布匹配 | 好（策略在数据上分布匹配） | 差（策略漂移后与数据不匹配） |
| 计算成本 | 高（每次迭代都要推理） | 低（只需一次数据准备） |
| 收敛质量 | 通常更高 | 依赖数据质量 |
| 工程复杂度 | 高 | 低 |

**混合方案**：一些研究尝试混合两者的优势，如 Iterative DPO（online-like DPO），但尚未成为主流。

---

## 三、推理时计算扩展（Test-Time Compute Scaling）

### 3.1 代表性工作对比

| 方法 | 组织 | 发布时间 | 核心机制 | 开源 | 训练方法 |
|------|------|---------|---------|------|---------|
| **o1** | OpenAI | 2024-09 | Chain-of-Thought 推理时扩展 | 否 | PPO + 过程奖励 |
| **R1** | DeepSeek | 2025-01 | GRPO + 推理时搜索 | 是 | GRPO |
| **o3** | OpenAI | 2026-04 | Beam Search + PRM 验证 | 否 | 大规模 PRM 训练 |

### 3.2 详细分析

#### OpenAI o1（2024-09）

o1 是首个将"推理时计算扩展"商业化的模型。核心思想：在推理阶段让模型先生成思考链（chain-of-thought），再输出最终答案。

**训练方法**：
- 使用强化学习训练模型生成 CoT
- 过程奖励模型（Process Reward Model, PRM）对每一步推理打分
- 通过 RL 优化推理路径的质量

**技术特点**：
- 推理时间可调（从快速到深度思考）
- 使用特殊的 token 格式标记思考过程
- 推理链路可以很长（数千 tokens）
- 在数学、代码、科学推理上显著优于 GPT-4

---

#### DeepSeek-R1（2025-01）

DeepSeek-R1 是开源领域最具影响力的推理模型。它的关键贡献是证明了：**仅通过强化学习（GRPO），不需要人类标注推理过程，LLM 就能自己学会长链推理**。

**训练流程**（根据公开论文）：
1. **Cold-start SFT**：用少量高质量推理数据进行监督微调
2. **Reasoning-oriented RL**：使用 GRPO + rule-based reward（格式奖励 + 答案正确性）
3. **Rejection Sampling**：对 checkpoint 采样并筛选高质量推理路径
4. **SFT + RL**：用筛选数据再做一次 SFT 和 RL

**工程实现要点**：
- GRPO 的 group size G=64
- rule-based reward 替代 learned RM（减少 reward hacking）
- 训练中动态调整 KL 散度系数
- 支持推理时的 self-consistency decoding

**开源影响**：
- R1 开源了模型权重和部分训练技术
- 引发了"开源推理模型"竞赛（QwQ、Skywork-o1 等）
- 推动了 GRPO 在各框架中的快速实现（TRL v1、OpenRLHF 0.8+）

---

#### OpenAI o3（2026-04）

o3 是 OpenAI 最新一代推理模型（2026 年 4 月发布），代表了推理时计算扩展的最新水平。

**核心技术**：
- **Multiple Beam Search**：同时维护多个推理路径进行束搜索
- **PRM 验证**：过程奖励模型对每一步推理进行验证和剪枝
- **自适应计算**：根据问题难度动态分配推理时间
- **>10x 推理计算扩展**：相比 o1 大幅增加了推理时的计算预算

**o1 vs o3 推理计算对比**：

| 指标 | o1 | o3 |
|------|-----|-----|
| 推理 token 上限 | ~32k | ~100k+ |
| 搜索策略 | 单路径 CoT | 多路径 Beam Search |
| PRM 粒度 | 段级别 | 步级别 |
| 推理时间调整 | 快速/长链 | 连续可调 |
| 高计算模式下的性能增益 | ~2x | ~5-10x |

**工程挑战**：
- PRM 的部署开销：每步验证都需要一次 PRM 推理调用
- 推理延迟：长 CoT + 多路径搜索导致延迟大幅增加
- 推理成本：高计算模式下成本是标准的 5-50 倍

#### MCTS + PRM 的工程实现

Monte Carlo Tree Search（MCTS）结合 Process Reward Model（PRM）是实现推理时扩展的核心技术路径。

**MCTS 在 LLM 推理中的工作流程**：
1. **Selection**：根据 UCT（Upper Confidence Tree）选择当前最有希望的推理路径
2. **Expansion**：在选中的节点扩展新的推理步骤
3. **Simulation**：从新节点开始模拟到结束
4. **Backpropagation**：用 PRM 的分数更新路径上所有节点的价值
5. **Best path**：选择评分最高的完整推理路径

**PRM 训练方法**：
- **Math-Shepherd**（2024）：自动生成过程监督数据
- **AlphaMath**（2024）：基于 MCTS 的数学推理探索
- **PRM800K**（OpenAI）：人工标注的 800K 过程奖励数据

**工程实现对比**：

| 任务 | 方法 | 硬件需求 | 推理延迟增加 | 质量提升 |
|------|------|---------|------------|---------|
| Best-of-N | N 次采样 + RM 重排序 | 低 | N 倍 | 中等 |
| Beam Search MCTS | 多路径搜索 + PRM | 中 | 5-10 倍 | 高 |
| o3-style | 大规模 Beam Search + 自适应 PRM | 高 | 10-100 倍 | 最高 |

---

## 四、框架综合对比

### 4.1 多维度评估矩阵

| 评估维度 | DeepSpeed-Chat | TRL | NeMo-Aligner | OpenRLHF | VeRL | LLaMA Factory |
|---------|---------------|-----|-------------|---------|------|--------------|
| **算法支持** | PPO | PPO/DPO/GRPO/KTO | PPO/DPO | PPO/GRPO/RLOO/REINFORCE++ | PPO/GRPO | PPO/DPO/KTO/ORPO |
| **多模态支持** | 无 | 基础（HF Transformers） | 无 | VLM 原生支持 | 有限 | 广泛（100+模型） |
| **分布式扩展** | 高达 175B | 基础（Accelerate） | 高达 1T+ | 高达数百节点（Ray） | 高达千节点（Megatron） | 有限（单机多卡） |
| **Rollout 引擎** | 内置 DeepSpeed | vLLM（可选） | 内置 | vLLM | vLLM/SGLang | vLLM/SGLang |
| **显存效率** | ZeRO 优化 | 中等 | Megatron 优化 | Ray + vLLM 混合 | FSDP/Megatron | LoRA/QLoRA 最高效 |
| **LoRA 支持** | 基础 | 完善（PEFT） | 基础 | 支持 | Megatron LoRA | 最强（6+量化方法） |
| **文档质量** | 中等 | 优秀 | 中等 | 良好 | 优秀 | 优秀 |
| **学习曲线** | 陡峭 | 平缓 | 陡峭 | 中等 | 中等 | 最平缓 |
| **社区活跃** | 低（维护模式） | 极高 | 已归档 | 高 | 极高 | 极高 |
| **生产验证** | Microsoft 内部 | HuggingFace 生态 | NVIDIA 内部 | 多家企业 | 火山引擎 | Amazon/NVIDIA |

### 4.2 算力成本参考

**基于 2026 年 GPU 市场价格估算**：

| 训练任务 | 推荐框架 | GPU 需求 | 训练时间 | 估算成本（按需） |
|---------|---------|---------|---------|----------------|
| 7B 模型 PPO | TRL/OpenRLHF | 4-8x A100-80GB | 6-12h | ~$200-500 |
| 7B 模型 DPO | TRL/LLaMA Factory | 1-2x A100-80GB | 2-4h | ~$30-100 |
| 13B 模型 GRPO | OpenRLHF/TRL | 8x A100-80GB | 8-16h | ~$500-1000 |
| 70B 模型 PPO | OpenRLHF/VeRL | 32-64x A100-80GB | 2-5天 | ~$5k-15k |
| 70B 模型 GRPO | OpenRLHF/VeRL | 24-48x A100-80GB | 1.5-4天 | ~$4k-12k |
| DeepSeek 671B | VeRL | 64-256x H100 | 周级 | ~$50k-200k |

> **注意**：以上为粗略估算，实际成本受 batch size、sequence length、rollout count、GPU 类型、云厂商折扣等因素影响。

---

## 五、总结与趋势判断

### 5.1 框架定位总结

```
                生产级大规模分布式
                       │
                  VeRL ─┼── OpenRLHF
                       │
          NeMo-Aligner │(已归档)
                       │
    模型微调为主 ──────┼────── 全面后训练
                       │
              LLaMA Factory
                       │
                   TRL │
                       │
                个人/小团队实验
```

### 5.2 关键趋势

1. **GRPO 和 REINFORCE++ 正在替代 PPO**：去掉 Critic 网络是明确趋势，减少显存的同时保持质量。DeepSeek-R1 的成功验证了这一方向。

2. **RL 训练框架从"训练库"进化为"训练+推理混合引擎"**：纯训练库（如最早的 DeepSpeed-Chat）已被"训练+推理混合"方案（OpenRLHF 的 Ray+vLLM、VeRL 的 FSDP+SGLang）取代。

3. **多模态 RL 成为新战场**：2026 年 Q1-Q2，OpenRLHF 和 TRL 都已支持 VLM RL 训练，视觉信息作为 RL 的一环。

4. **推理时计算扩展从研究走向工程**：o3/MCTS/PRM 的技术栈正在成为 RL 训练框架的第二增长曲线。

5. **LLaMA Factory 的单极分化**：71k stars 使其在微调场景中占据绝对优势，但在纯 RL 和大规模分布式方面不是竞争对手。

6. **NeMo-Aligner 归档标志一个时代的结束**：NVIDIA 不再在 RLHF 框架层面与社区直接竞争。

### 5.3 选择建议

| 你的需求 | 推荐框架 | 理由 |
|---------|---------|------|
| 快速原型验证 | TRL | 文档最好、生态最完善、学习曲线平缓 |
| 小团队微调+对齐 | LLaMA Factory | 零代码、LoRA 最强、模型支持最广 |
| 大规模 RL 训练（100+ GPU） | OpenRLHF | Ray 分布式、算法支持最全 |
| 超大模型（100B+） | VeRL | Megatron 后端、已验证 DeepSeek 671B |
| 多模态 RL | OpenRLHF | VLM 原生支持（2026-04 发布） |
| 已有 HuggingFace 生态 | TRL | 无缝集成 Transformers/Datasets/PEFT |
| 字节跳动/火山引擎生态 | VeRL | 原生适配、火山支持 |

---

## 六、信息来源

### GitHub 仓库
- DeepSpeed: https://github.com/microsoft/DeepSpeed
- TRL: https://github.com/huggingface/trl
- NeMo-Aligner: https://github.com/NVIDIA/NeMo-Aligner
- OpenRLHF: https://github.com/OpenRLHF/OpenRLHF
- VeRL: https://github.com/volcengine/verl
- LLaMA Factory: https://github.com/hiyouga/LLaMA-Factory

### 关键论文
- DeepSpeed-Chat: https://arxiv.org/abs/2308.01320
- DPO: https://arxiv.org/abs/2305.18290 (NeurIPS 2023)
- GRPO/R1: https://arxiv.org/abs/2501.12948 (DeepSeek-R1)
- PPO: https://arxiv.org/abs/1707.06347 (Schulman et al., 2017)
- InstructGPT: https://arxiv.org/abs/2203.02155 (Ouyang et al., 2022)
- KTO: https://arxiv.org/abs/2402.01306
- ORPO: https://arxiv.org/abs/2403.07691
- Math-Shepherd (PRM): https://arxiv.org/abs/2312.08935
- LLaMA Factory: https://arxiv.org/abs/2412.15124 (ACL 2024)

### 文档与参考
- TRL 文档: https://huggingface.co/docs/trl/index
- OpenRLHF 文档: https://openrlhf.readthedocs.io/
- VeRL 文档: https://verl.readthedocs.io/
- LLaMA Factory 文档: https://llamafactory.readthedocs.io/
- TRL v1 博客: https://huggingface.co/blog/trl-v1
- OpenRLHF 技术报告: https://www.researchgate.net/publication/393414548
- ScaleRL: https://arxiv.org/abs/2510.13786
- ProRL V2 (NVIDIA): https://developer.nvidia.com/blog/scaling-llm-reinforcement-learning-with-prolonged-training-using-prorl-v2/
- GTC26 VeRL Session: https://www.nvidia.com/en-us/on-demand/session/gtc26-S81829/

---

*本报告基于 2026 年 4 月 30 日的公开信息编制，GitHub stars 数据通过 shields.io 徽章和 GitHub API 获取，内容分析基于各框架的 README、论文和官方文档。*
