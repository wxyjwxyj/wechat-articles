"""把 fig1_moe_ffn_layer.excalidraw 渲染成 PNG"""
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import matplotlib.patheffects as pe
import numpy as np

fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 820)
ax.set_ylim(-30, 510)
ax.invert_yaxis()
ax.axis('off')
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

def rect(ax, x, y, w, h, fc, ec, lw=1.5, alpha=1.0, radius=4):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=2",
                         facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha)
    ax.add_patch(box)

def text(ax, x, y, s, size=12, color='#1e1e1e', ha='center', va='center', bold=False):
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight=weight, fontfamily='sans-serif')

def arrow_up(ax, x, y1, y2, color='#1e1e1e', lw=1.5):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))

def arrow_diag(ax, x1, y1, x2, y2, color='#1e1e1e', lw=1.5, dashed=False):
    ls = '--' if dashed else '-'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, linestyle=ls))

# ── 标题 ──────────────────────────────────────────────────────────────────────
text(ax, 410, -15, '图1：MoE 改造的是 FFN 子层', size=16, bold=True)

# ── 左侧：单层 Transformer 结构 ───────────────────────────────────────────────
text(ax, 150, 18, '单层 Transformer 结构', size=11, color='#555555')

layers = [
    (440, '#e9ecef', '#555555', 1.5, 'Output'),
    (370, '#f1f3f5', '#868e96', 1.5, 'Add & Norm'),
    (290, '#fff3bf', '#e67700', 3.0, 'Switching FFN Layer (MoE)'),
    (220, '#f1f3f5', '#868e96', 1.5, 'Add & Norm'),
    (150, '#d0ebff', '#1971c2', 1.5, 'Self-Attention'),
    (80,  '#e9ecef', '#555555', 1.5, 'Input Token'),
]

for (y, fc, ec, lw, label) in layers:
    rect(ax, 40, y, 200, 40, fc, ec, lw=lw)
    color = ec if ec != '#555555' else '#1e1e1e'
    text(ax, 140, y + 20, label, size=12, color=color)

# 层间箭头
for y_from, y_to in [(120, 155), (190, 225), (330, 365), (405, 440)]:
    arrow_up(ax, 140, y_from, y_to)
# MoE 层特殊箭头（橙色）
arrow_up(ax, 140, 265, 295, color='#e67700', lw=2)

# ── 放大箭头 ──────────────────────────────────────────────────────────────────
ax.annotate('', xy=(390, 310), xytext=(245, 310),
            arrowprops=dict(arrowstyle='->', color='#e67700', lw=2,
                            linestyle='dashed'))
text(ax, 318, 295, '放大', size=11, color='#e67700')

# ── 右侧：MoE FFN 内部路由 ────────────────────────────────────────────────────
text(ax, 600, 18, 'MoE FFN 内部：路由过程', size=11, color='#555555')

# x1, x2 圆形
for (cx, cy, label) in [(420, 200, 'x₁'), (420, 340, 'x₂')]:
    circle = plt.Circle((cx, cy), 22, facecolor='#d0ebff', edgecolor='#1971c2', lw=2)
    ax.add_patch(circle)
    text(ax, cx, cy, label, size=14, color='#1e1e1e')

# Router 菱形
router_x, router_y = 535, 270
diamond = plt.Polygon(
    [[router_x, router_y - 45], [router_x + 45, router_y],
     [router_x, router_y + 45], [router_x - 45, router_y]],
    facecolor='#d8f5a2', edgecolor='#5c940d', lw=2)
ax.add_patch(diamond)
text(ax, router_x, router_y, 'Router', size=12, color='#5c940d', bold=True)

# x1 → Router, x2 → Router
arrow_diag(ax, 442, 200, 490, 250, color='#1e1e1e', lw=1.5)
arrow_diag(ax, 442, 340, 490, 290, color='#1e1e1e', lw=1.5)

# 4 个 Expert
experts = [
    (650, 130, '#fff3bf', '#e67700', 2.5, 'Expert 1  ✓', '#e67700'),
    (650, 210, '#f1f3f5', '#adb5bd', 1.5, 'Expert 2',    '#868e96'),
    (650, 290, '#f1f3f5', '#adb5bd', 1.5, 'Expert 3',    '#868e96'),
    (650, 370, '#fff3bf', '#e67700', 2.5, 'Expert 4  ✓', '#e67700'),
]
for (x, y, fc, ec, lw, label, tc) in experts:
    rect(ax, x, y, 140, 40, fc, ec, lw=lw)
    text(ax, x + 70, y + 20, label, size=12, color=tc)

# Router → Expert 箭头
# 实线（激活）
arrow_diag(ax, 580, 255, 650, 150, color='#e67700', lw=2.5)
arrow_diag(ax, 580, 285, 650, 390, color='#e67700', lw=2.5)
# 虚线（未激活）
arrow_diag(ax, 580, 262, 650, 230, color='#adb5bd', lw=1.5, dashed=True)
arrow_diag(ax, 580, 278, 650, 310, color='#adb5bd', lw=1.5, dashed=True)

# 概率标注
text(ax, 618, 192, '0.65', size=11, color='#e67700')
text(ax, 618, 348, '0.80', size=11, color='#e67700')

# ── 图例 ──────────────────────────────────────────────────────────────────────
legend_x, legend_y = 650, 440
rect(ax, legend_x, legend_y, 140, 50, '#ffffff', '#adb5bd', lw=1)
ax.plot([legend_x+10, legend_x+40], [legend_y+15, legend_y+15], '-', color='#e67700', lw=2.5)
text(ax, legend_x+95, legend_y+15, '激活路由', size=10, color='#e67700', ha='center')
ax.plot([legend_x+10, legend_x+40], [legend_y+35, legend_y+35], '--', color='#adb5bd', lw=1.5)
text(ax, legend_x+95, legend_y+35, '未激活', size=10, color='#868e96', ha='center')

plt.tight_layout()
out = '/Users/zouapeng/Downloads/03_文档资料/news1/assets/fig1_preview.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print('saved:', out)
