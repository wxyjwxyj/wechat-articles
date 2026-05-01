# AI 芯片格局：大模型算力的"军火商"之战

> **副标题：从 CUDA 到万卡集群，谁在决定 AI 的算力天花板？**

---

## 一、一句话定义

AI 芯片是专门为深度学习训练和推理设计的加速器——GPU、TPU、NPU 的总称。2026 年，全球 AI 芯片市场规模突破 1500 亿美元，NVIDIA 以约 80% 的份额统治这个赛道，但 AMD、Google TPU、华为昇腾正在从不同方向发起挑战。

> 🎯 **读完这篇你能**：理解算力、内存带宽、互联带宽三个核心指标如何构成 AI 芯片的不可能三角，能分析 NVIDIA 的护城河到底在哪里以及谁能真正挑战它。

---

## 二、技术背景

AI 芯片和普通 CPU 的区别用一句话就能说清：**CPU 是"通才"——什么都能做，但一次只能做几件事；AI 芯片是"专才"——只会做矩阵乘法，但一次能做几万件事。**

深度学习的核心计算是矩阵乘法（更具体地说，是 General Matrix Multiply, GEMM）。一个 7B 参数的模型，每一次前向传播需要执行数十亿次矩阵乘法。如果让 CPU 来做，速度会慢 100-1000 倍。

### 三个决定芯片性能的核心指标

1. **算力（Compute）**：单位时间内能执行多少次计算，以 TFLOPS（万亿次浮点运算/秒）衡量。注意精度不同数值天差地别——FP32 和 FP4 的峰值算力可以差 4-8 倍。
2. **内存带宽（Memory Bandwidth）**：芯片读/写内存的速度，以 GB/s 衡量。大模型推理时，瓶颈往往不是算力，而是"把参数从内存搬到计算单元"的速度。
3. **互联（Interconnect）**：多卡集群时芯片之间的通信速度，以 GB/s 衡量。万卡集群的扩展效率，90% 取决于互联技术。

这三个指标构成了 AI 芯片的"不可能三角"——追求任意一个指标都会牺牲另一个。NVIDIA 的厉害之处在于，它在三个指标上都做到了行业领先。

### Tensor Core 是什么？

2017 年 Volta 架构引入的专门硬件单元，一次可以执行 4x4 矩阵乘法——相比普通 CUDA Core 的单个乘加操作，效率提升 8-16 倍。到 2026 年的 Blackwell，Tensor Core 已进化到第 5 代，支持 FP4/FP6/FP8/BF16 多种精度。

### 为什么精度越来越低？

FP32（32 位浮点）→ FP16（16 位）→ FP8（8 位）→ FP4（4 位）。规律很明显：**精度越低，计算越快，显存占用越少。** 关键是训练和推理算法的进步让低精度计算也能保持足够准确度。NVFP4 的 4-bit 训练可以匹配 16-bit 训练的准确度——这在 2022 年还是不可能的事。

> **📚 关联报告**
> - [Transformer](./Transformer_横纵分析报告.md) — 理解芯片为什么专注矩阵乘法：Attention 和 FFN 的计算本质
> - [大模型训练框架与基础设施](./大模型训练框架与基础设施_横纵分析报告.md) — 万卡集群如何把芯片的算力"组装"起来
> - [模型压缩](./模型压缩_横纵分析报告.md) — 量化/蒸馏如何降低对高端芯片的依赖
> - [Transformer 推理部署](./Transformer_推理部署_横纵分析报告.md) — 推理芯片需求与训练截然不同

---

## 三、纵向分析：十八年，从图形渲染到 AI 引擎

### 3.1 史前时期（2006-2011）：CUDA 的诞生

2006 年的 GPU 还只干一件事：给显示器渲染画面。NVIDIA 那年的 GeForce 8800 GTX（代号 G80）发布时，谁也没想到它会在十年后成为 AI 革命的引擎。

**关键人物：Ian Buck。** 这位斯坦福博士生在 2004 年之前做了 Brook 项目——一种让 GPU 做通用计算的编程语言。NVIDIA 创始人黄仁勋看到了这个项目的潜力，把 Ian Buck 招入公司。他和 John Nickolls 一起，在 G80 硬件上构建了 CUDA（Compute Unified Device Architecture），2007 年 2 月正式发布第一个 SDK。

这个决策在当时极其冒险。CUDA 的开发耗费了 NVIDIA 数亿美元，而最初的几年几乎没有应用场景——开发者习惯了 CPU 编程，GPU 编程的学习曲线陡峭，市场反应冷淡。NVIDIA 内部也有质疑声：为什么要花这么多资源做一个看起来没有市场的东西？

黄仁勋后来的解释很简单：**"我们赌的是计算终将需要并行化。"**

### 3.2 引爆点（2012）：AlexNet 改变一切

2012 年，多伦多大学的 Alex Krizhevsky 用两块 NVIDIA GTX 580（Fermi 架构，512 CUDA 核心）训练了 AlexNet，在 ImageNet 竞赛中将图像识别错误率从 26% 降到 15%，大幅领先第二名。

这个实验结果的意义远超计算机视觉领域——它证明了 GPU 大规模并行计算能力对深度学习的巨大价值。在此之前，AI 研究者主要用 CPU 训练模型，一个模型跑几天是家常便饭。GPU 把这个时间缩短到了几小时。

但 AlexNet 的意义不止于此。它开启了一个正反馈循环：**AI 越热 → GPU 卖得越多 → NVIDIA 收入越高 → 研发投入越大 → GPU 越适合 AI。** 这个循环到今天仍在运转。

### 3.3 生态奠基（2014-2016）：cuDNN + TPU 的出现

2014 年，NVIDIA 发布了 cuDNN——专门为深度学习优化的 GPU 加速库。cuDNN 提供了高度优化的卷积、池化、归一化等操作原语。所有主流深度学习框架（Caffe、TensorFlow、PyTorch）都基于 cuDNN 构建 GPU 加速层。

cuDNN 的战略意义后来才被看清：**它不是让开发者选择 NVIDIA，而是让开发者无法选择别的芯片。** 写了三年的 PyTorch 代码，底层全是 cuDNN 调用——换成 AMD 的 ROCm 就得重新适配，性能还不能保证。

2016 年对 NVIDIA 来说是另一个里程碑：Pascal 架构的 P100 是首个使用 HBM2 内存的数据中心 GPU，NVLink 1.0 提供了 160 GB/s 的 GPU 互联带宽。这两个特性让多卡训练成为可能——HBM 解决了"内存墙"，NVLink 解决了"通信墙"。

同年 5 月，Google 在 I/O 大会上公开了 TPU v1——一个纯推理 ASIC，运行 Google 搜索的 RankBrain、照片分类和 AlphaGo。这个芯片不卖，只在 Google 内部使用，也没有引起 NVIDIA 的警惕。事后看，这是"专用路线 vs 通用路线"的第一次公开对阵。

### 3.4 黄金时代（2017-2020）：Transformer + Tensor Core + Mellanox

2017 年发生了两件改变 AI 芯片格局的事。

**第一件：Google 发表 "Attention Is All You Need"。** Transformer 架构对计算的需求和之前的 CNN/RNN 完全不同——它的自注意力机制需要大量并行矩阵乘法，对算力和内存带宽的需求远高于之前的模型架构。Transformer 的兴起直接拉动了 GPU 需求。

**第二件：NVIDIA 发布 Volta V100，内置 640 个 Tensor Core。** 这是芯片历史上第一次出现专门为 AI 设计的计算单元。Tensor Core 一次执行 4x4 矩阵乘法，效率是普通 CUDA Core 的 8 倍。V100 成为 2017-2020 年训练 AI 模型的标配硬件。

2019 年 3 月，NVIDIA 以 69 亿美元收购 Mellanox——一家以色列网络设备公司。这笔收购当时让很多人看不懂：一个 GPU 公司买网络公司干什么？

后来的故事回答了这个问题。Mellanox 的 InfiniBand 技术成为构建万卡 GPU 集群的网络基石。当 OpenAI 训练 GPT-3 时，10000 块 GPU 之间的通信瓶颈——通过 Mellanox 的 InfiniBand 交换机解决。**今天 NVIDIA 的垄断，不只是 GPU 的垄断，更是"GPU + 网络 + 软件"全栈的垄断。** 而 Mellanox 是这个拼图里缺失的那一块。

2020 年 5 月，Ampere A100 发布。MIG（多实例 GPU）技术让一块 GPU 可以被切分为最多 7 个独立实例，分别服务不同用户。这直接降低了 GPU 云服务的成本——云厂商可以像卖虚拟机一样卖 GPU 切片。

### 3.5 供不应求（2022-2023）：H100 和 ChatGPT 的时代

2022 年 3 月，Hopper H100 发布。Transformer Engine 支持 FP8 精度训练，NVLink 4.0 带宽提升到 900 GB/s，HBM3 内存带宽 3.35 TB/s。H100 是所有指标的"天花板"。

但真正让 H100 封神的是 2022 年 11 月发布的 ChatGPT。ChatGPT 引爆的生成式 AI 浪潮，让 GPU 需求在几个月内暴增。

2023 年的 GPU 市场处于一种前所未有状态：**H100 单价 25,000-30,000 美元，eBay 上炒到 40,000+，仍然一卡难求。** 创业公司买不到 GPU，云厂商要等 6-12 个月的交付期。NVIDIA 的市值从 2023 年初的 3600 亿飙升至 2024 年中的 3.3 万亿美元——超越 Microsoft 和 Apple，成为全球市值最高的公司。

这段时间，AMD 也没闲着。MI300X 在 2023 年 12 月发布，192GB HBM3 显存容量超过了 H100 的 80GB，FP16 算力 1.3 PFLOPS 也超过了 H100 的 990 TFLOPS。但 AMD 的软件生态 ROCm 远不如 CUDA 成熟——开发者可以在 H100 上"开箱即用"，在 MI300X 上却要花几周适配。

### 3.6 地缘政治重塑格局（2022-2026）：出口管制改变了一切

2022 年 10 月，美国商务部工业安全局（BIS）发布了对华 AI 芯片出口管制——禁止向中国出口 A100/H100。这是 AI 芯片格局的第一个"地震"。

NVIDIA 的应对很"灵活"：快速开发了降级版 A800/H800，将互联带宽砍掉一截以符合管制阈值。但 2023 年 10 月，新规进一步收紧，连 A800/H800 也被禁。NVIDIA 再推出 H20——性能大幅降级，互联带宽腰斩。

到 2026 年初，出口管制已进入博弈新阶段：特朗普政府实施了"逐案审查"机制，H200 获得出口许可后被中国海关阻止入境。中国则限制镓/锗出口作为反制。

这场管制的一个关键影响是：**它意外催生了中国国产 AI 芯片的"被迫崛起"。** 华为昇腾 910B 成为替代 A100 的主要选项，2026 年初 DeepSeek 被报转向华为昇腾。中国国产 AI 芯片市场份额预计到 2026 年底达到 50%。

### 3.7 白热化（2024-2026）：Blackwell、Rubin、TPU v8

2024-2026 年是 AI 芯片竞争最激烈的三年。

**NVIDIA Blackwell 到 Rubin 的加速迭代。** 2024 年 3 月发布的 B200 是双 die 封装（2080 亿晶体管），NV-HBI 10 TB/s，FP4 9 PFLOPS，NVLink 5.0 1.8 TB/s。Blackwell 初期遭遇 CoWoS-L 封装缺陷和液冷系统泄漏导致出货推迟，但到 2025 年已全面上量，TrendForce 预计 2026 年 Blackwell 占 NVIDIA 高端 GPU 出货超 71%。Blackwell Ultra 在 GTC 2025 公布，配备 GB300/GB300 NVL72 机架方案。

**Rubin 的节奏比预期快得多。** 2025 年 9 月 NVIDIA 已向客户发送 Rubin VR200 首批样品；CES 2026 黄仁勋正式发布 Vera Rubin——首款 HBM4 GPU（288GB HBM4, 22TB/s 带宽），单芯片 50 PFLOPs AI 算力，搭载 88 核 Vera CPU，宣称相较 Blackwell 有 5 倍性能提升。2026 年下半年全面投产，NVL72 整机柜方案推出。GTC 2026 进一步更新路线图到 2028 年——**Feynman**（HBM5, 首次堆叠逻辑晶圆）和下一代 CPU **Rosa**。NVIDIA 的迭代节奏从"两年一代"变成了"一年一代"。

**2026 年 1 月，NVIDIA 以约 200 亿美元收购 Groq**——这家 LPU 推理芯片初创公司此前被视为 NVIDIA 在推理市场上的最大威胁。收购以"知识产权许可 + 人才"模式完成。Groq 3 LPU 在 GTC 2026 上已集成展示。这被评价为"推理时代的战略布局"。

**GTC 2026 还发布了两个关键战略转向：NVLink Fusion 和 CPO 硅光子。** NVLink Fusion 允许第三方 CPU 和 ASIC 通过 NVLink 协议连接 NVIDIA 硬件——从封闭走向半开放，AWS 已宣布 Trainium 4 将集成 NVLink Fusion。Quantum 3400 CPO 交换机发布，定调"光铜并行"策略（短距铜缆、长距硅光），NVIDIA 投资 Marvell 20 亿美元合作。

**Google TPU v7 Ironwood（2025.04）** 在第 7 代实现了关键突破——每芯片 192GB 内存，Pod 内可达 42.5 Exaflops 算力，专门为推理模型优化，传言订单达 100 万颗。接着的 **TPU v8（2026.04）** 是一个标志性事件——Google 首次将训练和推理拆分为两条产品线：v8t（训练）峰值 12.6 FP4 PFLOPS，9600 芯片超算；v8i（推理）288GB HBM3e。数据震撼：Midjourney 切到 TPU 后推理成本从月 210 万美元降到 70 万美元以下（降 65%），Anthropic 计划到 2027 年扩展到 100 万 TPU。

**AMD MI350X：** 2025 年 6 月 AMD Advancing AI 大会正式发布，3nm 制程（TSMC N3P），推理性能比 MI300X 提升高达 35 倍——这个数字主要是 4-bit 量化推理场景。搭配 Samsung/Micron HBM3E，同期发布 ROCm 7.0（推理性能是 ROCm 6 的 3.8 倍）。MI400（2026 年出货，432GB HBM4），MI450（已获 Anthropic 大单），MI500（2027 年，2nm，CDNA 6）。AMD 还推出了 Helios 机架级别 AI 解决方案，双宽机架对标 NVIDIA NVL72。

### 3.8 阶段总结

AI 芯片发展的十八年可划分为五个阶段：

| 阶段 | 时间 | 核心特征 | 关键事件 |
|------|------|---------|---------|
| **萌芽期** | 2006-2011 | CUDA 从 0 到 1，但场景不明 | CUDA 发布、G80 架构 |
| **引爆期** | 2012-2016 | GPU 被证明适合深度学习 | AlexNet、cuDNN、TPU v1 |
| **黄金期** | 2017-2020 | Transformer + Tensor Core 双击 | V100、A100、Mellanox 收购 |
| **爆发期** | 2022-2023 | ChatGPT 引爆，一卡难求 | H100、市值 3.3T、出口管制 |
| **混战期** | 2024-2026 | NVIDIA 全栈 + 自研 ASIC 围剿 | Blackwell→Rubin、NVIDIA 200亿收 Groq、TPU v7/v8、Maia 200、华为 50%中国份额 |

---

## 四、横向分析：2026 年的竞争图谱

> **场景判断：该领域竞品充分（场景 C）。** 以下按梯队划分展开分析。

### 4.1 第一梯队：NVIDIA

**核心优势：全栈垄断**

NVIDIA 的垄断不是"GPU 硬件"的垄断，而是一个覆盖了硬件、互联、网络、软件的全栈生态系统：

- **硬件**：从 H100（2022）到 B200（2024）到 Rubin（规划中），每年一代的迭代节奏
- **互联**：NVLink 5.0（1.8 TB/s）+ NVSwitch，构建了私有但极其高效的 GPU-to-GPU 通信
- **网络**：Mellanox InfiniBand，万卡集群的基石
- **软件**：CUDA（400 万 + 开发者）、cuDNN、TensorRT、NeMo、Megatron-LM

H100（700W，80GB HBM3，990 TFLOPS FP16）至今仍是部署最广泛的 AI 训练 GPU。B200（1000W，192GB HBM3e，2.25 PFLOPS FP16）2025 年产能已全部售罄。

**致命短板：**

太贵，且供不应求。2025 财年 NVIDIA 数据中心营收 2159 亿美元——一条产品线比 AMD 整个公司还大。但这种"印钞机"式的利润正在激发全行业的反抗：Google、AWS、Microsoft 三家最大的云厂商同时自研芯片，AMD 和 Intel 在加速追赶。

**开发者口碑：**

CUDA 的开发者体验是行业标杆——文档完善、Nsight 调试工具是标杆级产品。社区里有一句经典描述："CUDA is not just a moat, it's an ocean." 但 vendor lock-in 和闭源策略也积累了越来越多的不满。

### 4.2 第二梯队：AMD + Google TPU

#### AMD：追赶者的两难

MI300X（2023）和 MI350X（2025）在硬件规格上已经能跟 NVIDIA 对标——MI350X 的 288GB HBM3e 和 2.39 PFLOPS FP16 甚至在某些指标上超过 B200。ROCm 是全开源的，HIP 兼容层可以让 CUDA 代码在 AMD GPU 上编译运行。

AMD 面临的核心问题是「硬件好但不好用」。ROCm 虽然开源，但对 CUDA 的新特性跟进通常慢 6-12 个月。开发者写一个自定义 kernel，CUDA 生态里有 10 年积累的优化经验和成熟的 debug 工具链，ROCm 上得自己从零摸索。

2024 年 AMD 数据中心 GPU 营收约 50 亿美元——不到 NVIDIA 的 5%。但这个数字在快速增长，TrendForce 预测 2025 年 AMD 市场份额会提升到 10-15%。

#### Google TPU：自研芯片的样板

TPU 是"自研芯片"这条路线最成功的案例。到 2026 年，Google 在训练中使用了约 30% TPU、在推理中使用了约 50% TPU——Google 已经是 NVIDIA 之外最大的 AI 芯片用户。

TPU vs GPU 的核心优势是**能效和成本**：
- TPU 每卡约 300W（GPU 700W+）
- 推理能效比低 60-65%
- 按需价格低至 $1.38/小时，承诺折扣价 $0.39-0.55/小时

数据最能说明问题：Midjourney 切换到 TPU 后成本降了 65%。Anthropic 计划到 2027 年使用 100 万 TPU。

但 TPU 有好几个限制：只能用 GCP 云服务（不卖芯片），深度绑定 JAX 框架（PyTorch 支持不如 CUDA），大规模训练场景下的灵活性不如 GPU。

### 4.3 第三梯队：华为 + 云厂商自研 + 初创公司

#### 华为昇腾：国产替代的绝对主力，三年路线图首次公开

**2025 年 9 月，华为首次在联接大会公布昇腾 AI 芯片的三年路线图**——这在国产芯片领域是前所未有的事：

| 型号 | 时间 | 关键特性 |
|------|------|---------|
| 昇腾 910C | 2025 | 升级版 |
| **昇腾 950PR** | 2026 Q1 | 自研 HBM 内存，单卡算力达 H20 的 2.87 倍，支持 FP4 |
| **昇腾 960** | 2026 H2 | 持续迭代 |
| **昇腾 970** | 2027 | 下一代架构 |

同期推出 CloudMatrix 384 超节点——"全球最强超节点"。华为还首次公布了自研 HBM 内存。瑞穗证券估计 2025 年华为昇腾出货约 70 万颗。

软件生态仍是最大短板（CANN + MindSpore 远不如 CUDA 成熟），SMIC 拿不到 EUV 也限制了制程进步。但在"国产替代"政策驱动下，中国互联网大厂已批量采购，DeepSeek 被报道转向昇腾。

**市场数据更新——中国 AI 芯片格局剧变：**

Bernstein Research 预测 2026 年华为将占中国 AI 芯片市场 **50%** 份额，NVIDIA（受出口管制影响）将降至 **8%**。IDC 2025 年数据显示中国 AI 芯片总出货约 400 万张，NVIDIA 占约 55%，国产厂商合计约 41%。9 家国产 AI 芯片公司出货超万卡。寒武纪思元 590 出货强劲，计划 2026 年产能翻倍至约 5 万张。

这个数据的含义很清楚：**在全球市场 NVIDIA 80% 份额保持稳定的同时，中国市场正在快速独立化——两个生态的分离不是"趋势"而是"已完成的事实"。**

#### 云厂商自研芯片

AWS Trainium 2/3/4、Microsoft Maia 100/200、Meta MTIA、百度的昆仑芯 2、阿里的含光 800——几乎所有大型云厂商都在自研芯片。

**2025-2026 年，云厂商自研芯片从"谈判筹码"变成了"实质威胁"**：

**AWS Trainium：** Trainium 2 已部署至 Project Rainier（约 50 万颗，2025.11 上线用于 Anthropic 训练）。Trainium 3（Trn3 UltraServers, 2025.12）已一般可用。Trainium 4 已公布，将集成 NVIDIA NVLink Fusion。CEO Andy Jassy 称芯片业务独立估值 500 亿美元，考虑对外销售。AWS 暂停 Inferentia 推理芯片，聚焦 Trainium。

**Microsoft Maia 200（2026.01）：** 3nm 工艺，算力超 10 PFLOPS，宣称性能超越 Google TPU v7。但曾因延迟（从 2025 推至 2026）导致第三代推迟至 2028 年后。

**Meta MTIA（2026.03）：** 一次性推出四款芯片（两年四代），RISC-V 核心。3 月先推推理芯片，训练芯片正与台积电测试。2026.04 与 Broadcom 达成数 GW 级定制芯片合作，协议延至 2029 年。

**多家分析机构将 2026 年称为"定制芯片转折点"**（Custom Silicon Inflection Point）。Introl、TrendForce、Wedbush 一致认为：自研 ASIC 是 NVIDIA 面临的最大威胁——不是 AMD，不是 Intel。博通作为 ASIC 设计商被认为是 NVIDIA 最大潜在对手。但现实是：这些芯片仍以内用为主，它们对 NVIDIA 的威胁是"减少需求"而非"抢占份额"。

#### 初创公司

Cerebras（晶圆级芯片，2026.04 再次冲刺 IPO，估值约 20 亿）、Groq（LPU 推理芯片，2026.01 被 NVIDIA 以约 200 亿美元收购）、SambaNova（SN50 RDU 芯片，声称比 B200 更快）、d-Matrix（3D DRAM 突破，推理速度比 HBM4 快 10 倍）、Unconventional AI（Naveen Rao 创立，4.75 亿美元种子轮）。这些初创公司在特定场景有优势，但除 Cerebras 外，大多已被收购或仍处于早期阶段。

### 4.4 关键参数对比

| 芯片 | 发布时间 | 制程 | 算力(FP16) | 内存/带宽 | 互联 | TDP | 软件生态 | 开源 |
|:-----|:-------:|:----:|:--------:|:---------:|:---:|:---:|:-------:|:---:|
| NVIDIA H100 | 2022-03 | 4nm | 990 TFLOPS | 80GB HBM3 / 3.35 TB/s | NVLink 4 900 GB/s | 700W | CUDA | ❌ |
| NVIDIA B200 | 2024-03 | 4NP | 2.25 PFLOPS | 192GB HBM3e / 8 TB/s | NVLink 5 1.8 TB/s | 1000W | CUDA | ❌ |
| **NVIDIA Rubin** | **2026H2** | **3nm** | **~50 PFLOPS(FP4)** | **288GB HBM4 / 22 TB/s** | **NVLink 6** | **—** | CUDA | ❌ |
| AMD MI300X | 2023-12 | 5nm | 1.31 PFLOPS | 192GB HBM3 / 5.3 TB/s | Infinity Fabric | 750W | ROCm | ✅ |
| AMD MI350X | 2025-06 | 3nm | 2.39 PFLOPS | 288GB HBM3e / 8 TB/s | Infinity Fabric | 1000W | ROCm | ✅ |
| Google TPU v7 Ironwood | 2025-04 | — | — | 192GB / — | ICI | — | JAX/XLA | ❌ |
| Google TPU v8t | 2026-04 | — | 12.6 PFLOPS(FP4) | 216GB HBM3e / 6.5 TB/s | Boardfly | — | JAX/XLA | ❌ |
| 华为昇腾 950PR | 2026-Q1 | — | 2.87× H20 | 自研 HBM | HCCS | — | CANN | ❌ |
| **MS Maia 200** | **2026-01** | **3nm** | **>10 PFLOPS** | **—** | **—** | **—** | Azure | ❌ |
| AWS Trainium 3 | 2025-12 | — | — | — | — | — | Neuron | ❌ |
| Intel Gaudi 3 | 2024 | 7nm | — | 128GB HBM2e / 3.7 TB/s | 24x100GbE | 600W | SynapseAI | ❌ |

### 4.5 市场格局

NVIDIA 约 80% 的 AI 加速器市场份额短期内难以撼动。但我看到了三个结构性变化正在发生：

第一，**推理正在取代训练成为主战场。** 2023 年推理占 AI 计算约 33%，2026 年预计将占三分之二。推理场景对延迟和成本更敏感，这给了低成本芯片（TPU、定制 ASIC）机会。Gartner 预测到 2030 年，在 1 万亿参数 LLM 上执行推理的成本将比 2025 年降低 90% 以上——这个降幅的大部分来自芯片创新。

第二，**CUDA 护城河正在变浅，但 NVIDIA 在主动加深。** OpenAI Triton、MLIR、JAX 正在逐步解除开发者对 CUDA 的绑定。NVLink Fusion 则是 NVIDIA 反向操作——允许第三方 CPU/ASIC 接入 NVLink，用"半开放"应对开放生态的挑战。

第三，**中国市场正在成为独立的 AI 芯片生态。** Bernstein 预测 2026 年华为中国 AI 芯片份额达 50%、NVIDIA 降至 8%——这与全球 80% 的 NVIDIA 份额形成极端反差。两个生态的分离不是"趋势"而是"已完成的事实"。

### 4.6 核心趋势

1. **低精度计算成为新战场**：FP4/FP8 训练从实验走向主流。Blackwell 的 NVFP4 可以用 4-bit 精度匹配 16-bit 的训练准确度——由此，未来同样规模的芯片可以跑 4 倍大的模型。
2. **互联技术进入"光铜并行+标准大战"**：NVLink 5.0 1.8 TB/s 和 Google Boardfly 代表"私有高带宽 vs 灵活可编程"两种路线。2025-2026 新增变量——NVLink Fusion（NVIDIA 半开放，第三方 CPU/ASIC 可接入 NVLink）、UALink 联盟（AMD/Intel/Google/Microsoft/Meta 的开放 scale-up 互联标准，对标 NVLink）、Ultra Ethernet 1.0（以太网已正式成为 AI scale-out 网络主流，规模是 InfiniBand 的两倍以上）、CPO 硅光子（NVIDIA Quantum 3400 交换机发布，短距铜缆、长距硅光）。
3. **HBM 是战略瓶颈**：2026 年 HBM 需求同比增长约 70%，SK hynix 和 Micron 的产能已完全预订。AI 数据中心消耗了约 70% 的高端内存生产——制约 AI 芯片出货的不只是芯片本身，更是配套的 HBM 内存。
4. **Chiplet 成为标准设计范式**：Blackwell 的双 die 设计只是开始，Rubin 规划 3+ die，AMD 的 chiplet 架构也在迭代。2026 年将是 chiplet 设计成熟之年。
5. **云厂商自研不可逆**：虽然 NVIDIA 霸权短期内不会动摇，但 Google TPU 的成功案例让所有大厂都看到了自研芯片的价值——就算不是为了替代，也是为了谈判。

---

## 五、横纵交汇洞察

### 5.1 历史的锁扣

**第一条链：CUDA 的"时间差"护城河**

2007 年 CUDA 发布时，没人想到这个投资数亿美元、最初没有市场的项目，会在十几年后成为 NVIDIA 最坚固的壁垒。

回看这段历史，最让我惊叹的不是 NVIDIA 做对了什么，而是**它在一个没有市场的时候就开始布局。** 2012 年 AlexNet 引爆深度学习时，NVIDIA 已经为 GPU 计算积累了 5 年的技术和社区基础。2016 年 cuDNN 让 TensorFlow 和 PyTorch 深度绑定 CUDA 时，开发者都没有意识到这个选择的长期后果——直到想换 AMD 的时候，才发现代码库里全是 cuDNN 调用。

这就是我能看到的最核心的「历史锁扣」：**当 AI 爆发的瞬间到来时，NVIDIA 已经在基础设施层卡好了位置。** 这种做法不是巧合——黄仁勋在多次采访中说过，"我们不是在预测 AI 会来，我们是在建造 AI 需要的基础设施"。

**第二条链：专用与通用的永恒辩论**

AI 芯片的历史，也是一场"专用 vs 通用"的反复拉锯。

Google TPU 是"专用派"的极致——做了个只能跑神经网络推理的 ASIC，面积小、功耗低、效率高。NVIDIA GPU 是"通用派"——什么都能跑（训练、推理、渲染、加速计算），但每个场景都不是最优。

2026 年，我看到了一个有趣的趋同：NVIDIA 的 GPU 越来越"专用"——Tensor Core 是专用矩阵乘法器，Transformer Engine 是专为 Transformer 设计的，NV-HBI 是专用芯片互联。而 Google TPU 越来越"通用"——v8t/v8i 拆分突破了"仅推理"的限制，v8i 甚至加入了更多 SRAM 来支持复杂推理模式。

**这个趋同的背后有一个更深的规律：当市场规模足够大时，专用就会战胜通用。** 未来 AI 芯片的竞争将不再是 GPU vs ASIC，而是"专有全栈"（NVIDIA 模式）vs "开放标准"（AMD + UALink 联盟 + 开放软件生态）。

**第三条链：地缘政治正在制造"两个 AI 世界"**

出口管制对 AI 芯片格局的影响，可能比任何技术突破都要深远。

我看到了一个正在形成的格局：一个"西方生态"（NVIDIA + AMD + Google TPU，CUDA/Triton/ROCm 互通），和一个"中国生态"（华为昇腾 + 寒武纪 + 海光，CANN + 自研框架）。两个生态在底层硬件上完全隔离，但在上层应用层通过 PyTorch 等框架保持一定的兼容性。

长期来看，这会带来一个后果：**中国 AI 芯片在缺少 EUV 光刻机的情况下，被迫在算法优化和系统效率上走一条自己的路。** DeepSeek 用 512 块 H800 训练出 R1 证明了"算法可以部分替代算力"。如果这种趋势持续，中国 AI 可能会走出一条"低算力 + 高算法效率"的发展路径——这跟西方"堆算力"的路线完全不同。

### 5.2 三个剧本

#### 剧本一（最可能）：NVIDIA 继续主导，但份额缓慢下降

未来 2-3 年，NVIDIA 仍将以 60-80% 的市场份额主导 AI 芯片市场。CUDA 生态的惯性太大，AMD 和自研芯片短期内无法撼动。B200/Rubin 迭代保持硬件领先，但推理市场占比提升会稀释 NVIDIA 的统治力（推理场景更多使用低成本芯片）。Google TPU 继续扩大自用比例并向第三方开放，AMD 份额缓慢爬升到 15-20%。国内昇腾在政策驱动下占据中国市场的大头，但全球份额有限。

#### 剧本二（最危险）：AI 芯片供应瓶颈扼制行业发展

HBM 产能瓶颈持续恶化，加上 Blackwell 级别的先进封装产能不足，AI 芯片供应跟不上需求增长。创业公司因为买不到 GPU 而倒闭，中美芯片脱钩导致全球供应链效率下降。AI 行业增速放缓，模型进化速度下降，泡沫破灭。这个剧本的可能性不低——2026 年 HBM 产能已完全预订，台积电 CoWoS 产能也长期紧张。

#### 剧本三（最乐观）：架构突破打破 NVIDIA 垄断

光互联 + Chiplet + 开放软件生态的三重突破，让 AI 芯片成本大幅下降、供应量大幅上升。光子计算从实验室进入商用，一个 1000 美元的 AI 芯片可以达到今天 B200 的水平。推理成本下降 90%+，AI 应用爆发。CUDA 的锁定被 Triton/MLIR 打破，开发者可以自由选择任何芯片。华为通过算法优化在受限硬件上做出竞争力。这个剧本的关键前提是：光互联或类似架构突破从规模上验证——这可能需要 3-5 年。

---

## 六、信息来源

### 核心论文与文章

| 论文/文章 | 来源 | 访问时间 |
|-----------|------|---------|
| Attention Is All You Need | arxiv.org/abs/1706.03762 | 2026-04-30 |
| TPU v1: In-Datacenter Performance Analysis of a Tensor Processing Unit (ISCA 2017) | dl.acm.org/doi/10.1145/3079856.3080246 | 2026-04-30 |
| ImageNet Classification with Deep Convolutional Neural Networks (AlexNet) | 2012 | 2026-04-30 |

### 产品与技术来源

| 来源 | URL | 访问时间 |
|------|-----|---------|
| NVIDIA H100 Whitepaper | https://nvdam.widen.net/content/tdwwiwotwr/original/gtc22-whitepaper-hopper.pdf | 2026-04-30 |
| NVIDIA Blackwell Technical Brief | https://resources.nvidia.com/en-us-blackwell-architecture | 2026-04-30 |
| NVIDIA CUDA Wikipedia | https://en.wikipedia.org/wiki/CUDA | 2026-04-30 |
| NVIDIA Tesla Wikipedia | https://en.wikipedia.org/wiki/Nvidia_Tesla | 2026-04-30 |
| Wikipedia: Hopper Microarchitecture | https://en.wikipedia.org/wiki/Hopper_(microarchitecture) | 2026-04-30 |
| Wikipedia: Blackwell Microarchitecture | https://en.wikipedia.org/wiki/Blackwell_(microarchitecture) | 2026-04-30 |
| Google TPU Wikipedia | https://en.wikipedia.org/wiki/Tensor_Processing_Unit | 2026-04-30 |
| AMD Instinct Wikipedia | https://en.wikipedia.org/wiki/AMD_Instinct | 2026-04-30 |
| AMD ROCm Wikipedia | https://en.wikipedia.org/wiki/ROCm | 2026-04-30 |
| Huawei Wikipedia | https://en.wikipedia.org/wiki/Huawei | 2026-04-30 |
| Gartner AI Inference Market Forecast (March 2026) | Gartner | 2026-04-30 |
| Grand View Research: AI Inference Market 2030 | Grand View Research | 2026-04-30 |
| Jon Peddie Research: GPU Market Q1 2025 | Jon Peddie Research | 2026-04-30 |
| The Guardian: China blocks NVIDIA H200 (2026-01) | https://www.theguardian.com/technology/2026/jan/17/china-blocks-nvidia-h200-ai-chips-that-us-government-cleared-for-export-report | 2026-04-30 |
| SemiAnalysis: China AI Chips | https://www.semianalysis.com/p/nvidias-new-china-ai-chips-circumvent | 2026-04-30 |
| Forbes: AI chip market analysis | Forbes | 2026-04-30 |
| CNBC: Cerebras S-1 filing (2026-04) | CNBC | 2026-04-30 |
| Data Center Dynamics: Blackwell delay analysis | Data Center Dynamics | 2026-04-30 |
| East Asia Forum: US-China chip export controls | East Asia Forum | 2026-04-30 |
| NVIDIA GTC 2026 Keynote | Rubin/Feynman/NVLink Fusion/CPO | 2026-04-30 |
| NVIDIA CES 2026 Keynote | Vera Rubin official launch | 2026-04-30 |
| NVIDIA 收购 Groq | Fortune, Yahoo Finance (2026-01) | 2026-04-30 |
| TrendForce: Blackwell/Rubin出货占比预测 (2026-04) | TrendForce | 2026-04-30 |
| Google TPU v7 Ironwood 发布 | Google Cloud Next (2025-04) | 2026-04-30 |
| AWS Trainium 3 re:Invent 发布 (2025-12) | AWS | 2026-04-30 |
| Microsoft Maia 200 发布 | Microsoft Official Blog (2026-01-26) | 2026-04-30 |
| Meta MTIA 四款芯片 | CNBC, The Register (2026-03) | 2026-04-30 |
| 华为昇腾三年路线图 | 华为全联接大会 (2025-09) | 2026-04-30 |
| Bernstein Research: 中国AI芯片市场份额预测 (2026) | Bernstein Research | 2026-04-30 |
| Ultra Ethernet Consortium Spec 1.0 发布 | Ultra Ethernet Consortium | 2026-04-30 |
| UALink Consortium 成立 | AMD/Intel/Google/Microsoft/Meta | 2026-04-30 |
| Dell'Oro: 以太网 AI scale-out 规模超 InfiniBand 两倍 (2026-01) | Dell'Oro | 2026-04-30 |

---

> **方法论说明**：本报告采用横纵分析法（Horizontal-Vertical Analysis），由数字生命卡兹克提出。纵向部分追溯 AI 芯片从 2006 年 CUDA 到 2026 年 TPU v8 的完整演进史；横向部分对比当前主要 AI 芯片厂商的竞争格局；横纵交汇部分给出综合性判断和未来推演。
>
> 报告生成时间：2026 年 4 月 30 日
