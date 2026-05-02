# 学习率 Warmup 与衰减 前置知识

> 这份文档面向对深度学习训练有好奇但没有技术背景的读者。

> 🎯 **读完这篇你能**：理解为什么训大模型要先"慢慢热车"（warmup）再"慢慢刹车"（decay），能说出不同衰减策略的形状和适用场景，能解释为什么 warmup 没有提出者却无处不在。

---

## 一、Warmup 是什么？一句话

**训练刚开始时，学习率不要拉满——先用几百到几千步从 0 慢慢增长到最大值。**

就像冬天开车先热车。刚启动时润滑油还没铺开，踩满油门容易拉缸。神经网络刚初始化时参数是随机的，优化器的一阶/二阶矩估计还是空的——直接上大学习率，梯度容易爆炸。

---

## 二、为什么需要它？

三个层面的原因（后来才被论文解释清楚，实践中大家发现对就先用了）：

**1. Adam 优化器的"冷启动"问题**：Adam 需要积累一定步数的梯度统计才能做出合理的自适应学习率。前几百步的二阶矩估计方差极大，自适应 lr 剧烈波动。Warmup 就是在等它稳定。

**2. Transformer 的梯度不平衡**：原始 Transformer（Post-LN）中，前几层收到的梯度可能是后几层的几十倍。Warmup 通过小 lr 防止这种不平衡在早期引爆。

**3. 参数初始化的随机性**：刚随机初始化的参数没有任何"方向感"，需要少量步数的小 lr 探索，找到大致方向后再加速。

---

## 三、Warmup 的历史：两条独立的"发明"

2017 年 6 月，两篇论文几乎同时描述了 warmup——但都不是它"正式提出"的地方：

- **Goyal et al.（Facebook）**：用 8K batch size 训练 ImageNet，发现直接放大 lr 会爆炸。解决方法：前 5 个 epoch 线性 warmup。
- **Vaswani et al.（Google）**：Transformer 论文的 Noam Scheduler，前 4000 步 lr 从 0 线性增长。

两篇论文的动机不同——一个是"batch size 太大"，一个是"这模型训起来不稳定"。但结论一样：开始用小 lr。

此后没人能说清"谁发明的"——因为它本质上是个实践共识，两个团队几乎同时踩了同一个坑。

---

## 四、衰减策略：训练后期的"刹车"

Warmup 是热车，衰减是快到终点的刹车。不同衰减策略的区别在于刹车方式：

| 策略 | 形状 | 一句话 |
|------|------|------|
| **Step Decay** | 阶梯式 | 每 N 步除以 10，AlexNet 时代的做法 |
| **Cosine Decay** | 余弦曲线 | 平滑退火，GPT-3 起成为 LLM 标准 |
| **Linear Decay** | 直线 | BERT 用的，2025 年发现可能比余弦更好 |
| **WSD** | 三段式 | Warmup→Stable→Decay，DeepSeek 新范式 |
| **Constant+Cooldown** | 平稳+急刹 | 全程恒定，最后猛降 |

---

## 五、为什么 Cosine Decay 曾经是"标配"？为什么现在在变？

Cosine decay 从 GPT-3 (2020) 开始成为 LLM 训练标配——它在 ImageNet 时代就被验证优于 step decay，平滑曲线利于精细收敛。

但问题是：**余弦衰减把"训多久"锁死了。** 总步数 T 一开始就得定好——中途想加训，衰减已经到底，lr 太小没法学新东西。DeepSeek 2024 年提出 WSD（Warmup-Stable-Decay）：中间一大段恒定 lr，最后才衰减。这样随时可以续训。

2025 年 ICLR 一篇论文更激进——**线性衰减到零比余弦衰减更好。** 不仅简单，而且验证 loss 系统性地更低。

---

## 六、一张图理解

```
  lr
  ^
  |     ___
  |    /   \___
  |   /         \___
  |  /               \________
  | /                         \
  +--------------------------------> steps
  warmup  stable       decay

WSD 三阶段：慢慢加速 → 全速巡航 → 慢慢减速到站
```

---

## 参考来源

- Goyal et al. "Accurate, Large Minibatch SGD" (2017) — https://arxiv.org/abs/1706.02677
- Vaswani et al. "Attention Is All You Need" (2017) — https://arxiv.org/abs/1706.03762
- RAdam (Liu et al. 2019) — warmup 的首个理论解释 — https://arxiv.org/abs/1908.03265
- Xiong et al. "On Layer Normalization in the Transformer Architecture" (2020) — https://arxiv.org/abs/2002.04745
- GPT-3 (Brown et al. 2020) — Warmup + Cosine Decay 大模型标配化 — https://arxiv.org/abs/2005.14165
- DeepSeek-V3 — WSD 调度大规模验证 — https://arxiv.org/abs/2412.19437
- "Straight to Zero" (Bergsma et al. 2025) — 线性衰减优于余弦 — https://arxiv.org/abs/2502.15938
