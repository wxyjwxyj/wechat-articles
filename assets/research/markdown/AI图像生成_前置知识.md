# AI 图像生成 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉 AI 图像生成的基本概念，可以直接翻阅主报告。

> 🎯 **读完这篇你能**：解释扩散模型的"加噪 → 去噪"核心原理，区分 U-Net 和 DiT 两种扩散架构路线，并能说出 Stable Diffusion 的 VAE 潜在空间压缩为什么是关键工程突破。

---

## 一、AI 图像生成是做什么的？

AI 图像生成就是用 AI 模型"凭空"画出图片——你输入一段文字（"一只戴礼帽的柴犬，油画风格"），AI 输出一张图片。

2022 年是 AI 图像生成进入大众视野的元年（社区估算）：DALL-E 2 和 Midjourney 让"文字变图片"从一个研究实验变成了人人可用的产品。到 2026 年，AI 生成图片已经无处不在——从社交媒体头像到电商产品图到电影概念设计。

---

## 二、关键概念

### 扩散模型（Diffusion Model）

2022 年至今，扩散模型是 AI 图像生成的核心技术。原理简单说：

1. **训练**：给大量图片逐步"加噪"（加随机噪点直到完全变雪花），然后让模型学会"去噪"（从雪花还原回图片）
2. **生成**：从纯噪点出发，模型一步步去噪，最终生成一张清晰图片

**DDPM（Denoising Diffusion Probabilistic Models）** 是 2020 年 Ho 等人发表的论文（Ho et al., 2020），重新引起了学界对扩散模型的兴趣。它是第一个在图像生成上系统超越 GAN 的扩散模型——训练稳定、生成质量高。这个工作奠定了后续所有扩散模型（DALL-E 2、Stable Diffusion、Midjourney）的技术基础。

扩散模型之所以取代了 GAN，是因为训练更稳定、多样性更好。GAN 需要同时训练"生成器"和"判别器"两个网络对抗博弈（Goodfellow et al., 2014），极易失败。扩散模型只需要训练一个去噪网络。

### 潜在扩散（Latent Diffusion）—— Stable Diffusion 的核心

直接在像素空间做扩散太慢（一张 1024×1024 的图就是 300 万像素）。Stable Diffusion 的聪明之处（Rombach et al., 2022）：先用一个 VAE（Variational Autoencoder，变分自编码器）把图片压缩到小巧的"潜在空间"（latent space），在压缩后的空间里做扩散，最后再把结果解压回高清图。

这就像：写一部长篇小说的提纲（潜在空间），而不是写完整本书再修改。

### DiT（Diffusion Transformer）

2024 年开始普及的新架构。之前扩散模型的核心网络是 U-Net（一种编码-解码结构）。DiT 用 Transformer 替代 U-Net（Peebles & Xie, 2023），效果更好、扩展性更强。Flux（Black Forest Labs, 2024 年 8 月）是第一个大获成功的 DiT 图像生成模型。

**类比**：U-Net 像一个专门为某种游戏（固定分辨率、固定尺寸）设计的手柄，打那一个游戏很顺手，换一个游戏就不行了。DiT 像一个通用手柄——什么游戏都能接，分辨率、时长、宽高比都能适应，因为 Transformer 天生处理的是"patch"（小块）而不是固定形状的像素网格。

### 文本编码器（Text Encoder）

AI 图像生成需要"理解用户输入的文字"，然后生成匹配的图片。这个"理解"靠的是文本编码器——把用户输入的文字转化成模型能理解的向量表示。

**类比**：文本编码器就像中英翻译——你告诉 AI "画一只戴礼帽的柴犬"，编码器先把这个中文指令"翻译"成 AI 能理解的"数字语言"（向量），然后生成模块才能根据这个向量画出对应的图。翻译质量直接影响画出来的东西——如果编码器"误译了"礼帽，AI 可能画出一只戴普通帽子的狗。

不同的模型用不同的文本编码器，直接影响生成效果：CLIP（OpenAI）最常用，T5（Google）更长文本理解更强。

### ControlNet（控制网络） / LoRA（Low-Rank Adaptation，低秩适配）

ControlNet 和 LoRA 是 Stable Diffusion 生态的两个核心技术，让开源社区能做很多闭源产品做不了的事：

- **ControlNet**（Zhang & Agrawala, 2023）：给生成过程加额外的控制条件——比如提供一张"人物姿势骨架"图，让生成的图片完全按照这个姿势来
  **类比**：就像给画家一个模特摆好姿势照着画（ControlNet），而不是只靠口头描述"这个人站着，左手叉腰"——模型有了"参考图"，精确度大幅提升。

- **LoRA**（Hu et al., 2021）：用少量图片微调模型，让模型学会生成特定风格或特定人物
  **类比**：就像给一个通用画师看几张宫崎骏的画，他就能学会那种风格。LoRA 不需要重新训练整个模型，只调整极小一部分参数（通常小于 0.1%），就能让模型掌握新的画风。

这些技术让 Stable Diffusion 的开源生态比任何闭源产品都丰富。

---

## 三、主流产品速览

| 产品 | 开发商 | 一句话 | 开/闭源 |
|------|--------|--------|:-------:|
| **Midjourney** | 独立实验室 | 设计圈标杆，画质最好，审美最强 | ❌ |
| **DALL-E / GPT Image** | OpenAI | 集成 ChatGPT，文字理解力强 | ❌ |
| **Stable Diffusion 3.5** | Stability AI | 开源代表，生态最丰富 | ✅ |
| **Flux** | Black Forest Labs | SD 原班人马，DiT 架构，写实度高 | ✅（部分）|
| **Adobe Firefly** | Adobe | 商用安全，集成 Photoshop | ❌ |
| **Imagen 3/4** | Google | 2K 分辨率，通过 Gemini 分发 | ❌ |
| **Ideogram** | Ideogram | 文字生成最强（图片里的文字可读） | ❌ |
| **Recraft** | Recraft | 设计工具，矢量图输出 | ❌ |

---

## 四、一个简单直觉

```
AI 图像生成的进化史 = 从"这什么东西"到"这是 AI 画的？"到"这居然是人画的？"

2014-2021（GAN 时代）：能生成"像图片"的东西但经常翻车
2022（扩散革命）：DALL-E 2 / Midjourney / SD 让"文生图"成为现实
2023-2024（质量飞跃）：Midjourney V6 摄影级，SD 生态遍地开花
2024-2026（DiT 时代）：Flux 写实度接近 Midjourney，开源追赶闭源

2026 年的状态：
- 静态图生成 → 已经极其成熟
- 文字生成 → 大部分时候对但偶尔翻车（Ideogram 最强）
- 一致性 → 多张图保持同一角色还不行
- 商业可用的合规训练 → Adobe 在这块赢麻了
```

AI 图像生成在 2026 年是所有 AI 赛道中"最成熟"的——生成质量已经够好、成本足够低、工具链足够完善。它不再是"能不能做"的问题，而是"怎么做得更好、更可控、更商用"的问题。

---

## 参考来源

- **Generative Adversarial Nets** (Goodfellow et al., 2014) — GAN 的开山之作，生成器与判别器对抗训练，深度学习图像生成的起点 — https://arxiv.org/abs/1406.2661
- **Denoising Diffusion Probabilistic Models** (Ho et al., 2020) — DDPM，重新引发扩散模型研究热潮，系统超越 GAN 的图像生成质量 — https://arxiv.org/abs/2006.11239
- **High-Resolution Image Synthesis with Latent Diffusion Models** (Rombach et al., 2022) — Stable Diffusion 的核心，在 VAE 压缩的潜在空间中做扩散，大幅降低计算量 — https://arxiv.org/abs/2112.10752
- **Scalable Diffusion Models with Transformers** (Peebles & Xie, 2023) — DiT 架构，用 Transformer 替代 U-Net 做扩散，2024 年后图像/视频生成的主流骨架 — https://arxiv.org/abs/2212.09748
- **Adding Conditional Control to Text-to-Image Diffusion Models** (Zhang & Agrawala, 2023) — ControlNet，为扩散模型添加空间条件控制（骨架、边缘、深度图）— https://arxiv.org/abs/2302.05543
- **LoRA: Low-Rank Adaptation of Large Language Models** (Hu et al., 2021) — 低秩适配微调，AI 图像生成中训练特定风格/角色的核心技术 — https://arxiv.org/abs/2106.09685
