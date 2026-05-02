---
name: research-report-queue
description: 待写的横纵分析报告选题（无正式论文、工程驱动、社区先行）
type: project
---

4 个选题，都是"工程跑在论文前面"的类型：

1. **llama.cpp / GGUF 生态** — 一个人（Georgi Gerganov）用 C++ 反编译了整个推理生态。GGML→GGUF→k-quant→Ollama→LM Studio。2023.03 至今。核心叙事：从一台 MacBook 跑 LLaMA 开始，长成本地推理的事实标准。

2. **Warmup + 学习率衰减** — 没有提出论文，却是所有大模型训练的标配。2016-2018 年间靠无数次"模型又不收敛了"的试错摸出来。核心叙事：训练经验怎么从社区共识变成基础设施。

3. **模型合并（Model Merging）** — 2023 年底社区先用 MergeKit 大规模合并分发 LoRA 权重，论文（TIES-Merging、DARE）晚了半年才来解释"为什么不应该能工作但确实能"。核心叙事：先有实践后有理论。

4. **RoPE（旋转位置编码）** — 苏剑林 2021 独立研究者发论文，中文社区先火，被 Meta LLaMA 采用后全球跟进。有论文但普及靠的是工程选择。核心叙事：一个人一篇论文穿透全行业。

**Why**: AI 基础设施工艺史系列。KV Cache 是第一篇，这四个是后续。
