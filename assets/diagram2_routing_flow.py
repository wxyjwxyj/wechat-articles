"""图2：MoE 路由流程 — 宏观视图 vs 微观视图（v4 自上而下+美化）"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'Songti SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))
for ax in (ax1, ax2):
    ax.set_xlim(0, 460)
    ax.set_ylim(0, 660)
    ax.axis('off')
fig.patch.set_facecolor('white')

def box(ax, x, y, w, h, fc, ec, lw=2, alpha=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=4",
                 facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha))

def txt(ax, x, y, s, size=14, color='#1e1e1e', bold=False):
    ax.text(x, y, s, fontsize=size, color=color, ha='center', va='center',
            fontweight='bold' if bold else 'normal')

def arr(ax, x, y1, y2, color='#868e96', lw=2):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))

# ══════════════════════════════════════════════════════════════════
# 左侧：宏观视图 — 层堆叠（自上而下）
# ══════════════════════════════════════════════════════════════════
txt(ax1, 230, 10, '宏观视图：层堆叠', size=18, color='#1971c2', bold=True)

layers = [
    (40,  '#ffc9c9', '#e03131', 'Attention'),
    (110, '#a5d8ff', '#1971c2', 'MoE FFN'),
    (180, '#ffc9c9', '#e03131', 'Attention'),
    (250, '#a5d8ff', '#1971c2', 'MoE FFN'),
    (320, '#ffc9c9', '#e03131', 'Attention'),
    (390, '#a5d8ff', '#1971c2', 'MoE FFN'),
    (460, '#ffc9c9', '#e03131', 'Attention'),
]

for y, fc, ec, label in layers:
    box(ax1, 80, y, 300, 50, fc, ec, lw=2)
    txt(ax1, 230, y+25, label, size=15, color=ec, bold=True)

for i in range(6):
    arr(ax1, 230, layers[i][0]+50, layers[i+1][0])

# ══════════════════════════════════════════════════════════════════
# 右侧：微观视图 — 单个 MoE 层（自上而下）
# ══════════════════════════════════════════════════════════════════
txt(ax2, 230, 10, '微观视图：单个 MoE 层', size=18, color='#e67700', bold=True)

# Input
box(ax2, 100, 40, 260, 40, '#e9ecef', '#495057')
txt(ax2, 230, 60, 'Input', size=15)

arr(ax2, 230, 80, 105)

# Gating Network
box(ax2, 110, 105, 240, 45, '#d8f5a2', '#5c940d', lw=2)
txt(ax2, 230, 120, 'Gating Network', size=14, color='#5c940d', bold=True)
txt(ax2, 230, 138, '(Router)', size=10, color='#5c940d')

# 5 个 Expert（横排）
expert_data = [
    (20,  180, False, 'Expert 1'),
    (110, 180, True,  'Expert 2'),
    (200, 180, False, 'Expert 3'),
    (290, 180, True,  'Expert N-1'),
    (380, 180, False, 'Expert N'),
]

for x, y, sel, label in expert_data:
    fc = '#a5d8ff' if sel else '#f8f9fa'
    ec = '#1971c2' if sel else '#ced4da'
    lw = 2 if sel else 1
    alpha = 1.0 if sel else 0.3
    box(ax2, x, y, 70, 50, fc, ec, lw=lw, alpha=alpha)
    txt(ax2, x+35, y+25, label, size=10,
        color=ec if sel else '#adb5bd', bold=sel)

# Router → Expert
for x, y, sel, _ in expert_data:
    color = '#1971c2' if sel else '#ced4da'
    lw = 2 if sel else 1
    ax2.annotate('', xy=(x+35, y), xytext=(230, 150),
                 arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                 linestyle='' if sel else '--'))

txt(ax2, 145, 168, 'G(x)2', size=10, color='#1971c2', bold=True)
txt(ax2, 325, 168, 'G(x)N-1', size=10, color='#1971c2', bold=True)

arr(ax2, 230, 230, 270)

# 加权求和
box(ax2, 110, 270, 240, 40, '#fff3bf', '#e67700', lw=2)
txt(ax2, 230, 290, '加权求和', size=15, color='#e67700', bold=True)

arr(ax2, 230, 310, 340)

# Output
box(ax2, 100, 340, 260, 40, '#e9ecef', '#495057')
txt(ax2, 230, 360, 'Output', size=15)

# 图例
box(ax2, 30, 410, 400, 45, '#ffffff', '#dee2e6', lw=1)
box(ax2, 45, 422, 16, 12, '#a5d8ff', '#1971c2', lw=2)
txt(ax2, 100, 428, '被选中的 Expert', size=10, color='#1971c2')
box(ax2, 185, 422, 16, 12, '#f8f9fa', '#ced4da', lw=1, alpha=0.3)
txt(ax2, 240, 428, '未被选中（计算为零）', size=10, color='#868e96')
box(ax2, 345, 422, 16, 12, '#d8f5a2', '#5c940d', lw=2)
txt(ax2, 395, 428, 'Router', size=10, color='#5c940d')

plt.tight_layout()
out = '/Users/zouapeng/Downloads/03_文档资料/news1/assets/diagram2_routing_flow.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print('saved:', out)
