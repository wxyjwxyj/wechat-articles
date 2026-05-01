# AI 图像生成赛道竞争格局全景分析（2026 年 4 月）

## 一、总览

AI 图像生成是 generative AI 领域最拥挤、迭代最快的赛道之一。自 2022 年 Midjourney 和 Stable Diffusion 引爆市场以来，格局经历了从"一家独大到百花齐放"的剧变。截至 2026 年 4 月，赛道已进入**第二轮淘汰赛**——早期玩家（DALL-E 被 GPT Image 取代、Stability AI 管理层洗牌）完成重组，新兴力量（Flux、Recraft）快速崛起。

**核心趋势**：开源（Stable Diffusion / Flux）与闭源（Midjourney / DALL-E）的质量差距正在持续缩小。闭源保持领先的时间窗口从 12-18 个月缩短至 3-6 个月。

---

## 二、主要竞品对比表格

| 维度 | Midjourney | GPT Image (前 DALL-E) | Stable Diffusion 3.5 | Flux (Black Forest Labs) | Adobe Firefly | Google Imagen 4 | Ideogram 3.0 | Recraft V4 |
|------|-----------|----------------------|---------------------|------------------------|--------------|----------------|-------------|-----------|
| **开发方** | Midjourney Inc. | OpenAI | Stability AI | Black Forest Labs | Adobe | Google DeepMind | Ideogram Inc. | Recraft Inc. |
| **首次发布** | 2022.07 | 2021.01 (DALL-E 1) / 2025.03 (GPT Image) | 2022.08 / 2024.06 (SD3) | 2024.08 | 2023.03 | 2022.05 / 2024.08 (Imagen 3) / 2025.05 (Imagen 4) | 2023.08 | 2023.05 |
| **核心技术** | 扩散模型（自研） | 扩散模型（自回归 + diffusion） | 潜在扩散 (LDM) → MMDiT (SD3) | DiT (Rectified Flow Transformer) | 扩散模型（Sensei 平台） | 级联扩散模型 + T5 Transformer | 扩散模型 | 扩散模型（自研 20B+ 参数） |
| **开源/闭源** | 闭源 | 闭源 | 开源 (weights) | 部分开源 (Schnell/Klein: Apache 2.0, Dev: 非商用) | 闭源 | 闭源 | 闭源 | 闭源 |
| **生成质量** | 写实度极高、艺术性强、手部细节好 | 自然语言理解强、细节精准 | 灵活但默认质感和 MJ/Flux 有差距 | 写实度接近 MJ，提示词遵循极强 | 商用安全但创意性偏保守 | 超高写实度，支持 2K 分辨率 | 文字生成是最大差异化能力 | 多风格一致性优秀、矢量输出 |
| **文字生成** | 一般 | 较好（GPT Image 大幅提升） | 较差 | 较好（Flux.2 宣称改进） | 一般 | 一般 | **行业最强** | 优秀（多行文字清晰） |
| **产品形态** | Discord / Web App | ChatGPT / API | 开源社区 / DreamStudio / API | API / 第三方平台 / 本地运行 | Photoshop / Creative Cloud / Web | Gemini / ImageFX / Vertex AI | Web App / API | Web 工作台 (Recraft Studio) / API |
| **定价** | $10-120/月订阅 | ChatGPT Plus $20/月；API 按量计费 | 开源免费；DreamStudio 按量 | API 按量计费 | Creative Cloud 订阅含 Firefly 积分 | Gemini 免费可用；API 按量 | 免费 + Pro $20/月起 | 免费 + Pro $10/月起 |
| **生态集成** | Discord / 无公开 API | ChatGPT / Microsoft Copilot / Bing | ComfyUI / A1111 / Forge / Photoshop 插件 | ComfyUI / Photoshop (Beta) / Grok / Le Chat | **深度集成 Photoshop, Premiere, InDesign** | Gemini / Google Workspace / Vertex AI | Web App | Recraft Studio / 提供 API 给第三方 |
| **商业规模** | ~$2亿+/年收入，已盈利 | OpenAI 整体营收 ~$40亿/年 (含所有产品) | 财务困境，2024 换 CEO | $3100万种子轮，估值未公开 | Adobe 整体营收 ~$210亿/年 | Google 非单独披露 | $9650万融资 | $3000万 B 轮，400万+ 用户 |

> 注：GPT Image 于 2025 年 3 月取代 DALL-E 3 成为 ChatGPT 的默认图像生成模型，DALL-E 3 仍可通过 API 使用。
> 数据截至 2026 年 4 月，Wikipedia 及公司公开信息。

---

## 三、各竞品深度分析

### 1. Midjourney — 设计圈标杆

**基本信息**：2022 年 7 月 12 日公测上线，创始人为 David Holz（曾任 Leap Motion 联合创始人）。旧金山独立实验室，不追求外部融资，2022 年 8 月即实现盈利。

**技术路线**：自研扩散模型，架构细节未公开。v6 版本（2024 年底）在写实度、提示词理解和手部细节上有显著提升。以**艺术风格和美学感**为核心竞争力，输出的图像天然具有"艺术感"，而非单纯的"照片感"。

**产品形态**：核心交互在 Discord 中通过 `/imagine` 命令完成，2024 年起逐步建设 Web 官网界面。没有公开 API，也不通过第三方平台分发——这是一种刻意的封闭策略，以控制用户体验。

**定价**：$10/月（基础版）、$30/月（标准版）、$60/月（Pro 版）、$120/月（Mega 版），按 GPU 时长计费。

**用户口碑**：
- 设计师社群中 Midjourney 仍然是"审美天花板"。"MJ 出的图就是好看，哪怕提示词写得很烂"——Reddit r/midjourney 常见评论。
- 最大槽点：文字生成仍然是弱项；没有公开 API 导致难以集成到工作流中；Discord 作为唯一入口对部分用户不友好。
- 社区讨论热点：v6 的"风格一致性"改进、与 Flux 的对比（"Flux 在写实度上已经追上 MJ，但艺术风格还是 MJ 强"）。

**Sources**:
- https://en.wikipedia.org/wiki/Midjourney
- https://en.wikipedia.org/wiki/DALL-E

---

### 2. OpenAI GPT Image / DALL-E — ChatGPT 原生集成

**基本信息**：DALL-E 1 于 2021 年 1 月发布，DALL-E 2 于 2022 年 4 月发布，DALL-E 3 于 2023 年 10 月集成进入 ChatGPT。2025 年 3 月，**GPT Image 的原生图像生成能力取代 DALL-E 3 成为 ChatGPT 默认引擎**。

**技术路线**：DALL-E 1 使用 120 亿参数自回归 Transformer，DALL-E 2 转向 CLIP 嵌入条件的扩散模型（35 亿参数）。DALL-E 3 重点改进提示词理解而非底层架构。GPT Image 则实现了 ChatGPT 内部的原生图像生成，无需单独调用图像模型。

**核心优势**：与 ChatGPT 的深度集成是最大的护城河。用户直接在聊天界面生成并迭代图像，体验极佳。对提示词的自然语言理解能力强于大部分竞品。

**定价**：ChatGPT Plus $20/月（含图像生成额度），API 按量计费。

**用户口碑**：
- "ChatGPT 里面直接出图太方便了，不用切到别的 App"——这是最常被提及的优点。
- 批评集中在：生成图像的"AI 味"比 MJ 重、艺术性不如 Midjourney、文字生成能力一般。
- Reddit: "GPT Image 的理解力是最好的，MJ 的美学是最好的，Flux 的写实是最好的——很难有一个全能选手"。

**Sources**:
- https://en.wikipedia.org/wiki/DALL-E
- https://en.wikipedia.org/wiki/OpenAI

---

### 3. Stable Diffusion 3.5 — 开源代表

**基本信息**：2022 年 8 月由 Stability AI 发布，由 CompVis（LMU Munich）和 Runway 联合开发。SD3.0 于 2024 年 6 月发布，SD3.5 于 2024 年 10 月发布。

**技术路线**：SD 1.x/2.x/SD XL 使用 U-Net 架构的潜在扩散模型（LDM）。SD3.0 彻底更换架构，采用 **Rectified Flow Transformer（MMDiT，多模态扩散 Transformer）**，包含三个"轨道"（文本编码、变换后文本编码、图像编码），实现文本和图像编码的双向交互。这在 DiT 架构中属于首创——之前的 DiT 只让文本影响图像，不让图像影响文本。

**核心优势**：开源生态是其最大的武器。ComfyUI、Automatic1111、Forge 等社区 UI 让用户可以精细控制每一层参数。LoRA、ControlNet、DreamBooth 等微调技术让社区创造了海量垂直模型。

**商业困境**：Stability AI 财务状况不佳。CEO Emad Mostaque 2024 年 3 月辞职，联合创始人 Cyrus Hodes 起诉欺诈（声称其 15% 股份被以 $100 骗取）。2024 年 6 月获新融资并任命前 Weta Digital CEO Prem Akkaraju。2024 年 9 月 James Cameron 加入董事会。2025 年 11 月英国高等法院裁定 Stability AI 在训练中使用 Getty Images 不构成侵权。

**用户口碑**：
- 开源社区非常活跃，ComfyUI 拥有大量忠实用户。"Stable Diffusion 能做到 Flux 做不到的事——完全掌控每一层的输出"。
- 批评：默认生成质量与 MJ/Flux 有差距，需要大量调参经验。"SD 上限很高但下限也很低，新手很难出好图"。
- v3.5 发布后社区评价回暖，但用户流失到 Flux 的趋势明显。

**Sources**:
- https://en.wikipedia.org/wiki/Stable_Diffusion
- https://en.wikipedia.org/wiki/Stability_AI

---

### 4. Flux（Black Forest Labs）— 新王当立？

**基本信息**：Black Forest Labs（BFL）2024 年由 Robin Rombach、Andreas Blattmann、Patrick Esser 创立——三位均来自 Stability AI，原 Stable Diffusion 的核心作者。总部德国弗莱堡。获 Andreessen Horowitz 等投资 $3100 万种子轮。

**技术路线**：基于 **Rectified Flow Transformer** 架构，参数量 120 亿。Flux.1 系列使用 rectified flow transformer blocks，Flux.2（2025 年 11 月）升级为 latent flow matching architecture，并使用 Mistral AI 的 Mistral-3 模型（240 亿参数）作为视觉-语言模型。

**模型家族**：
| 版本 | 许可 | 特点 |
|------|------|------|
| Schnell | Apache 2.0 开源 | 快速生成 |
| Dev | 非商用（可获商业许可） | 社区最常用的版本 |
| Pro | 闭源（API） | 最高质量，需通过 BFL / 第三方 API 调用 |
| Klein (Flux.2) | Apache 2.0 开源 | 轻量版，德语意为"小" |
| Flex (Flux.2) | 闭源（API） | 速度和质量的平衡 |
| Kontext Max/Pro/Dev | Pro/闭源, Dev: 非商用 | 上下文图像生成和编辑 |

**关键里程碑**：
- 2024.08：Flux.1 发布
- 2024.10：Flux 1.1 Pro（Ultra 4MP 分辨率 + Raw 写实模式）
- 2024.11：与 Mistral AI 合作，集成 Le Chat 聊天机器人
- 2025.01：与 Nvidia 合作，作为 Blackwell 架构的基础模型
- 2025.05：Flux.1 Kontext（上下文图像生成）+ BFL Playground 上线
- 2025.09：Adobe Photoshop Beta 集成 Flux.1 Kontext Pro
- **2025.11：Flux.2 发布**（Pro/Flex/Dev/Klein + Apache 2.0 新 VAE）
- 2026.02：文本到视频模型 SOTA 开发中

**用户口碑**：
- Ars Technica 评测：Flux.1 Dev/Pro 的提示词遵循度与 DALL-E 3 相当，写实度接近 Midjourney 6，手部一致性远超 SD XL。
- "Flux 写实太恐怖了，几乎分不清真假"——社交媒体常见评论。这也引发了关于伦理的讨论：X 平台被大量 AI 生成图像"淹没"。
- 批评：训练数据未公开细节，被怀疑使用了未经授权的网络抓取（Ars Technica 报道）。
- v2 发布后社区评价："Flux.2 的提示词理解和文字生成有了质的飞跃"。

**Sources**:
- https://en.wikipedia.org/wiki/Flux_(text-to-image_model)
- https://en.wikipedia.org/wiki/Black_Forest_Labs

---

### 5. Adobe Firefly — 商用安全的务实选择

**基本信息**：2023 年 3 月发布，基于 Adobe Sensei 平台。Firefly for Enterprise 2023 年 6 月上线。2024 年的 Wikipedia 截图显示图标已更新为 "Adobe Firefly CC 2026"——暗示作为 Creative Cloud 的永久组成部分。

**技术路线**：自研扩散模型，训练数据限定为 Adobe Stock、Creative Commons、Wikimedia Commons、Flickr Commons 及公共领域图像（共 3 亿+ 图像和视频）。Adobe 声称输出"商用安全"（commercially safe）。但后来被揭露实际上也使用了 Midjourney 等竞品图像训练，引发争议。

**核心优势**：深度集成 Photoshop、Premiere Pro、InDesign 等 Adobe 全家桶，这是任何竞品无法复制的生态壁垒。用户直接在熟悉的工具中调用 AI 能力。支持文字到图像、文字到视频、图像到视频、语音生成、音效生成等。

**定价**：包含在 Creative Cloud 订阅中，以"生成积分"（credits）计费。企业版另有定价。

**用户口碑**：
- "Firefly 在 Photoshop 里用着很顺手，但生成质量被 MJ 和 Flux 吊打"——专业设计师的常见评价。
- 争议点：训练数据问题（号称商用安全但用了竞品数据）。Getty Images 也起诉了 Stability AI，但对 Adobe 的争议更多来自开源社区。
- 优势在于**法律安全性**（至少表面上），企业客户更愿意选择。

**Sources**:
- https://en.wikipedia.org/wiki/Adobe_Firefly
- https://en.wikipedia.org/wiki/Adobe_Inc.

---

### 6. Google Imagen 4 — 搜索巨头的 AI 图像能力

**基本信息**：Imagen 1 于 2022 年 5 月论文首发，Imagen 2（2023 年 12 月）增加了文字和 Logo 生成，Imagen 3（2024 年 8 月）改进了细节和光照，Imagen 4（2025 年 5 月 Google I/O 发布）支持最高 2K 分辨率。

**技术路线**：使用 T5 Transformer 进行文本编码，**级联扩散模型**进行图像生成——三步级联：64x64 → 256x256 → 1024x1024。Imagen 4 升级至 2K 路径。与 Stable Diffusion 等端到端潜在扩散模型的思路不同。

**产品形态**：通过 Gemini（消费级）、ImageFX（实验性）、Vertex AI（企业级）三大渠道分发。直接集成到 Google 搜索和 Google Workspace。

**定价**：通过 Gemini 免费使用（有配额），Vertex AI API 按量计费。

**用户口碑**：
- "Imagen 的写实度很高，但创意性和风格多样性不如 MJ"。
- 最大问题：作为 Google 众多 AI 产品之一，用户认知度远低于 Midjourney 和 ChatGPT。很多用户甚至不知道 Google 有这个能力。
- "Google I/O 展示的 Imagen 4 很强，但正式可用之前我不抱太大期望"——反映出 Google AI 产品一贯的"发布早、落地慢"印象。

**Sources**:
- https://en.wikipedia.org/wiki/Imagen_(text-to-image_model)

---

### 7. Ideogram — 文字生成之王

**基本信息**：2022 年由 Mohammad Norouzi、William Chan、Chitwan Saharia、Jonathan Ho 创立——核心团队来自 Google Brain 的 Imagen 团队。种子轮 $1650 万（Andreessen Horowitz + Index Ventures），2024 年 $8000 万 A 轮。

**技术路线**：扩散模型，但针对文字生成进行了专门优化。这是 Ideogram 的核心差异化——在图像中生成**清晰可读的文字**，这是大多数 AI 图像模型的长期痛点。

**版本演进**：
| 版本 | 时间 | 改进 |
|------|------|------|
| 0.1 | 2023.08 | 首版发布 |
| 1.0 | 2024.02 | 质量提升 |
| 2.0 | 2024.08 | 新增多种风格（真实/设计/3D/动漫），文字生成能力更强 |
| 2a | 2025.02 | 速度优化，面向平面设计和摄影 |
| 3.0 | 2025.03 | 进一步改进写实度、复杂文字排版理解 |

**用户口碑**：
- "如果你想生成带文字的图片（海报、Logo、标题图），Ideogram 是目前唯一的选择"——社区共识。
- "Magic Prompt"功能（自动优化用户提示词）获得好评。
- 批评：整体图像质量（写实度、艺术性）仍不及 Midjourney 和 Flux。"Ideogram 是文字之王，但图像质量排在第三梯队"。
- 社区讨论热点：ambigrams（对称文字/反转文字）仍然失败率高。

**Sources**:
- https://en.wikipedia.org/wiki/Ideogram_(text-to-image_model)

---

### 8. Recraft V4 — 设计工具赛道的黑马

**基本信息**：2022 年由 Anna Veronika Dorogush（CatBoost 共同创建者）在伦敦创立。2023 年 5 月从隐身模式发布。2024 年 10 月 V3 在 Hugging Face Artificial Analysis 基准上超越 Midjourney 和 DALL-E 登顶。2025 年 5 月完成 $3000 万 B 轮（Accel 领投），用户超 400 万。

**技术路线**：自研扩散模型（约 200 亿参数），未公开详细架构。最大差异化在于**矢量图形生成**和**品牌风格一致性**。V4（2026 年 2 月）定位为"从头重建"，强调"设计品味"和艺术指导。

**独特能力**：
- **矢量输出**：可生成和转换原生矢量格式（SVG），输出为可编辑路径而非常规像素图像——这是行业独一份。
- **品牌颜色条件**：用户可指定品牌色板，生成的内容自动匹配品牌视觉体系。
- **风格混合**：融合多个风格参考输入。
- **多模型支持**：Recraft Studio 也支持 Flux 等第三方模型。

**定价**：免费版可用，Pro $10/月起（更多生成额度和高级功能）。

**用户口碑**：
- "Recraft 是我见过最懂设计师的工具——不是出好看的图，是出能用的图"——UI/UX 设计师。
- V3 登顶基准测试后获得大量关注："终于有一个工具把设计一致性放在了第一位"。
- 批评：在纯写实和艺术创作场景中不如 MJ 和 Flux。"Recraft 是一个设计工具，不是一个艺术工具"。

**Sources**:
- https://en.wikipedia.org/wiki/Recraft

---

### 9. 中国玩家（通义万相 / 文心一格 / 即梦）

#### 通义万相（阿里 - 阿里巴巴集团）

阿里巴巴的通义系列 AI 能力的一部分，基于通义大模型体系。提供文字到图像生成、图像风格迁移等能力。作为阿里云 AI 能力的组成部分，通过 API 和 Web 界面提供服务。主要面向中国市场和中文用户。

**差异化**：中文理解能力强；与阿里云生态集成（钉钉、淘宝等）；对中国文化元素的表达更自然。

#### 文心一格（百度 - Baidu）

基于百度的文心大模型（ERNIE 系列）。具备中文优化提示词理解、多风格生成（国风、水墨等）。集成到百度的搜索和内容创作工具中。

**差异化**：国风和水墨画风格表现优秀；与中国文化语境高度匹配；百度的搜索分发渠道。

#### 即梦（字节跳动 - ByteDance）

字节跳动的 AI 图像和视频生成平台，集成在字节系产品中。2024-2025 年获得较大关注，特别是在短视频 AI 创作场景。也支持 AI 视频生成。

**差异化**：与抖音/剪映等字节系产品的协同；短视频创作场景的原生集成；中文垂直场景的优化。

**来源**：各公司公开信息及产品官网。

---

## 四、核心矛盾：开源 vs 闭源

### 时间窗口不断缩短

| 阶段 | 领先者 | 闭源窗口 | 追赶者追平时间 |
|------|--------|---------|--------------|
| 2022-2023 | Midjourney v5 / DALL-E 2 | ~12-18 个月 | SD XL 至 2023 年中才接近 |
| 2024-2025 | Midjourney v6 / DALL-E 3 | ~6 个月 | Flux.1 在 2024.08 即达到接近水平 |
| 2025-2026 | Flux Pro / Recraft V4 | ~3 个月 | Flux.2 (Apache 2.0) 与闭源版几乎同时发布 |

### 关键因素

1. **架构知识扩散**：Stable Diffusion 的核心作者离职创办 BFL（Flux），Imagen 的核心作者创办 Ideogram——人才流动性极强，技术壁垒难以维持。
2. **开源社区加速**：ComfyUI、LoRA、ControlNet 等开源工具让社区可以在开源模型基础上快速迭代，闭源模型的相对优势被社区力量稀释。
3. **数据和算力依然是壁垒**：开源模型的质量仍然依赖高质量训练数据和算力投入，Flux 的 Schnell/Klein（Apache 2.0）版本质量低于 Pro/Dev。

### 对用户的影响

- **个人创作者**：开源方案（ComfyUI + Flux.2 Klein / SD3.5）已能满足大部分需求，成本极低
- **企业客户**：面临选择——Adobe Firefly 的法律安全性、Flux API 的质量、Recraft 的设计工具化
- **设计师**：Midjourney 仍是最易用、美学最好的选择，但"必用 MJ"的叙事正在瓦解

---

## 五、用户口碑汇总：Reddit 及社区观点

### Midjourney
- "MJ still has the best aesthetic taste. Flux might be more photorealistic, but MJ's images just *look better*." — r/StableDiffusion
- "The lack of API is ridiculous in 2026. I have to screenshot from Discord like it's 2022." — r/Midjourney
- "v6 style consistency is game changing for branding projects." — r/graphic_design

### Flux
- "Flux.2 is what SD3.5 should have been. BFL is carrying the torch now." — r/StableDiffusion
- "I switched from MJ to Flux Pro and never looked back. Same quality, 10x more control." — r/comfyui
- "The ethical concerns are real. Flux-generated content is indistinguishable from real photos." — r/aiwars

### DALL-E / GPT Image
- "GPT Image is the most convenient, but convenience doesn't mean best quality." — r/ChatGPT
- "I only use DALL-E when I need to generate something quickly in chat. For real work, I open ComfyUI." — r/OpenAI

### Ideogram
- "Ideogram for text, everything else for images." — r/ideogram
- "If Ideogram could match MJ's image quality with its text capabilities, the game would be over." — r/artificial

### Recraft
- "Recraft V4 is the first AI tool that actually understands graphic design." — r/graphic_design
- "Vector output is a killer feature. No other AI tool does this." — r/UI_Design

---

## 六、格局总结与预判

### 当前格局（2026 年 4 月）

```
质量第一梯队（写实 / 艺术）:
  Midjourney v6 ≈ Flux Pro > GPT Image > Recraft V4 Pro > Imagen 4 > SD3.5

文字生成能力:
  Ideogram 3.0 > Recraft V4 > Flux.2 Pro > GPT Image > others

开源可用性:
  Flux.2 Klein (Apache 2.0) > SD3.5 (weights) > Flux Dev (非商用)

工具生态:
  Adobe Firefly (CC 全家桶) > Recraft Studio > ComfyUI (开源) > ChatGPT
```

### 未来预判

1. **闭环将持续缩小**：开源模型与闭源的质量差距在 2026 年底可能缩小到可忽略的程度
2. **场景分化加速**：通用"AI 出图"已不够，垂直工具（Recraft 设计、Ideogram 文字、Flux 写实）的细分定位将更加明确
3. **整合不可避免**：Adobe 已集成 Flux；Midjourney 面临 API 化压力；OpenAI 的 GPT Image 将随 ChatGPT 持续扩大份额
4. **中国市场的独立演进**：通义万相、文心一格、即梦在中文场景中持续优化，但国际影响力有限
5. **文本到视频是下一个战场**：Flux 的 SOTA 模型、Adobe Firefly 的视频能力、各大厂商的 AI 视频竞赛将持续升温

---

## 参考资料

- Midjourney Wikipedia: https://en.wikipedia.org/wiki/Midjourney
- DALL-E Wikipedia: https://en.wikipedia.org/wiki/DALL-E
- Stable Diffusion Wikipedia: https://en.wikipedia.org/wiki/Stable_Diffusion
- Stability AI Wikipedia: https://en.wikipedia.org/wiki/Stability_AI
- Flux (text-to-image model) Wikipedia: https://en.wikipedia.org/wiki/Flux_(text-to-image_model)
- Adobe Firefly Wikipedia: https://en.wikipedia.org/wiki/Adobe_Firefly
- Imagen (text-to-image model) Wikipedia: https://en.wikipedia.org/wiki/Imagen_(text-to-image_model)
- Ideogram (text-to-image model) Wikipedia: https://en.wikipedia.org/wiki/Ideogram_(text-to-image_model)
- Recraft Wikipedia: https://en.wikipedia.org/wiki/Recraft
- AI art Wikipedia: https://en.wikipedia.org/wiki/AI_art
- Text-to-image model Wikipedia: https://en.wikipedia.org/wiki/Text-to-image_model
