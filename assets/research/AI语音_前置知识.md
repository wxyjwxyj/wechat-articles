# AI 语音 前置知识

> 这份文档为零基础读者准备。如果你已经熟悉 AI 语音的基本概念，可以直接翻阅主报告。

> 🎯 **读完这篇你能**：梳理 AI 语音技术栈（TTS / ASR / 实时对话）及语音合成四代演进路线，解释端到端语音模型为什么比传统三段式方案延迟更低、体验更自然。

---

## 一、AI 语音包括什么？

AI 语音技术栈分成三大块：

- **TTS（Text-to-Speech，语音合成）**：把文字变成声音——你输入"你好世界"，AI 用人类的声音读出来
- **ASR（Automatic Speech Recognition，语音识别）**：把声音变成文字——你说话，AI 转成文字
- **实时语音对话**：ASR → 理解 → TTS 整个链条在几百毫秒内完成，实现"跟 AI 打电话"的体验

2026 年的趋势是这三块的边界在模糊——GPT-4o voice 把 ASR、理解、TTS 全整合到一个端到端模型里，不再分成三个独立的步骤。

---

## 二、关键概念

### 语音合成（TTS）的几代技术

**第一代：拼接合成**。录一个真人读几小时语音，然后像拼积木一样拼出句子。效果：机械感强，不自然。

**第二代：参数合成 + 神经网络（Tacotron、WaveNet）**。2016 年 DeepMind 的 WaveNet 是关键突破（van den Oord et al., 2016）——用神经网络直接生成原始音频波形。效果：自然度大幅提升，但计算量大、速度慢。

**第三代：神经编解码（2023-2024）**。把语音压缩成离散的"token"（类似于把文字变成 token），像语言模型一样生成语音 token，再解码成音频。Meta 的 EnCodec、微软的 VALL-E 是代表（Wang et al., 2023）。特点：速度快、能保留语音特征（语气、情感）、支持零样本克隆。

**第四代：端到端语音模型（2024-2025）**。GPT-4o voice 为代表的——不再分 ASR→理解→TTS 三步，一个模型同时处理语音输入和输出。特点：延迟极低、能理解语气和情感、支持实时打断。

### 零样本语音克隆

只用几秒（3-30 秒）的参考音频就能克隆一个人的声音（Wang et al., 2023）。ElevenLabs 在 2023 年把这项技术带火（ElevenLabs）。核心原理：神经编解码把语音分解成内容 token 和说话人 token，克隆时提取说话人 token 但换成新的内容。

### 语音 Token / 编解码器

语音不能直接输入大模型——需要先转换成离散的 token。编解码器（Encoder-Decoder）做这件事：
- **编码**：把语音波形压缩成 token 序列
- **解码**：把 token 序列还原成语音波形

Meta 的 EnCodec（Défossez et al., 2022）、Google 的 SoundStream、微软的 AudioDec 是关键方案。

### 情感语音 / 语气控制

好的语音合成不只是"读出文字"，而是理解语境后选择说话的语气——高兴时声音轻快、严肃时语气低沉。ElevenLabs 的语音模型能理解文本的情感并自动匹配语气。GPT-4o voice 更进一步，能根据对话上下文实时调整情感表达。

---

## 三、语音合成 vs 语音识别的市场

两者商业价值不同：

| | TTS（合成） | ASR（识别） |
|---|---|---|
| 价格参考 | ~$0.015-0.30/千字符（社区估算） | ~$0.01-0.10/分钟（社区估算） |
| 主要客户 | 有声书、配音、虚拟主播 | 会议转录、客服分析 |
| 技术壁垒 | 自然度、情感表达 | 准确率、多语言适应性 |
| 开源情况 | CosyVoice、ChatTTS、GPT-SoVITS | Whisper |

ASR 市场更成熟（准确率已经超过人类水平）（Radford et al., 2022），TTS 市场差异化空间更大（情感、克隆、多语言质量参差不齐）。

---

## 四、核心矛盾：自然度 vs 延迟

这是 AI 语音行业最根本的取舍：

- **最自然的语音**：用大模型（如 GPT-4o）做端到端生成，但需要 300-1000ms 的延迟
- **最快的语音**：用轻量模型（如 CosyVoice 的 bi-streaming），延迟能做到 150ms，但自然度不如大模型

**TTFB（Time To First Byte，首包时间）** 是衡量语音延迟的核心指标——从用户说完话到 AI 开始回话的第一个音频字节传回来的时间。延迟超过 500ms 用户就会觉得"不自然"。2026 年的延迟竞赛数据：ElevenLabs Flash 75ms TTFB（目前最快）（ElevenLabs），Deepgram Aura-2 90ms（Deepgram），CosyVoice 3 bi-streaming ~150ms（FunAudioLLM / Alibaba, 2024），GPT-4o voice ~320ms（社区估算）。行业正在全面压向 100ms 以下。

---

## 五、主流产品速览

| 产品 | 类型 | 一句话 |
|------|------|--------|
| **ElevenLabs** | TTS | 语音克隆领导者，2023 爆红，2025 估值 $3B+（ElevenLabs） |
| **OpenAI TTS / Whisper** | TTS+ASR | 2023 TTS API，2022 Whisper 开源 |
| **GPT-4o voice** | 实时对话 | 目前最自然的 AI 语音对话体验 |
| **CosyVoice 3** | TTS（开源） | 阿里开源，0.5B 参数（FunAudioLLM / Alibaba, 2024），指标逼近商业产品 |
| **Fish Speech** | TTS（开源） | 开源语音合成，活跃社区 |
| **Deepgram** | ASR | 企业级语音识别，NVIDIA 投资 |
| **Azure Speech** | TTS+ASR | 微软企业级服务 |
| **豆包语音** | 全部 | 字节跳动，全栈语音能力 |
| **科大讯飞** | 全部 | 中国语音老牌龙头 |

---

## 六、一个简单直觉

```
语音 AI 的进化史 = 从"机器人读课文"到"AI 像真人一样说话"

第一代：Tacotron + WaveNet → 像 Siri，一听就是 AI
第二代：ElevenLabs → 像真人读稿子，但缺情感
第三代：GPT-4o voice → 像真人聊天，有语气有情感有停顿

2026 年的状态：
- 读文字 → 已经完美（CosyVoice、ElevenLabs）
- 聊大天 → 接近完美（GPT-4o voice）
- 有情感地对话 → 还需要进步
- 多语言混合 / 方言 → 很多产品做不到
```

---

## 参考来源

- **WaveNet: A Generative Model for Raw Audio** (van den Oord et al., 2016) — 用神经网络直接生成原始音频波形，语音合成自然度的里程碑 — https://arxiv.org/abs/1609.03499
- **Tacotron: Towards End-to-End Speech Synthesis** (Wang et al., 2017) — 端到端 TTS 的开创性工作，从字符序列直接生成梅尔频谱 — https://arxiv.org/abs/1703.10135
- **Whisper: Robust Speech Recognition via Large-Scale Weak Supervision** (Radford et al., 2022) — 68 万小时多语言弱监督数据训练的通用的 ASR 模型 — https://arxiv.org/abs/2212.04356
- **Neural Codec Language Models are Zero-Shot Text to Speech Synthesizers (VALL-E)** (Wang et al., 2023) — 神经编解码语言模型实现 3 秒音频零样本语音克隆 — https://arxiv.org/abs/2301.02111
- **ElevenLabs** — 语音克隆与合成的商业标杆，2025 年估值 $3B+，Flash 模型 TTFB 75ms — https://elevenlabs.io/
- **High Fidelity Neural Audio Compression** (Défossez et al., Meta, 2022) — EnCodec 神经音频编解码器，将音频压缩为离散 token，为 VALL-E 等语音合成模型提供基础 — https://arxiv.org/abs/2210.13438
- **Deepgram** — Aura-2 模型 TTFB 90ms，企业级实时语音识别与合成 API — https://deepgram.com/
- **CosyVoice** (FunAudioLLM / Alibaba, 2024) — SOTA 开源语音合成，0.5B 参数，支持流式合成与零样本克隆 — https://github.com/FunAudioLLM/CosyVoice
