"""图1：Transformer 层结构 — Dense FFN vs MoE FFN（v6 美化）"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'Songti SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))
for ax in (ax1, ax2):
    ax.set_xlim(0, 460)
    ax.set_ylim(0, 640)
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
# 左侧：Dense Transformer
# ══════════════════════════════════════════════════════════════════
txt(ax1, 230, 10, 'Dense Transformer', size=18, color='#1971c2', bold=True)

# 层定义：(y, h, fc, ec, label)
LH = 45  # 标准层高
dense = [
    (40,  LH, '#e9ecef', '#495057', 'Input Tokens'),
    (105, 55, '#d0ebff', '#1971c2', 'Multi-Head Attention'),
    (180, LH, '#f1f3f5', '#868e96', 'Add & Norm'),
    (245, 55, '#e2e8f0', '#495057', 'FFN（一个大网络）'),
    (320, LH, '#f1f3f5', '#868e96', 'Add & Norm'),
    (385, LH, '#e9ecef', '#495057', 'Output'),
]

for y, h, fc, ec, label in dense:
    box(ax1, 60, y, 340, h, fc, ec)
    txt(ax1, 230, y + h/2, label, size=15, color=ec)

for i in range(5):
    arr(ax1, 230, dense[i][0] + dense[i][1], dense[i+1][0])

# ══════════════════════════════════════════════════════════════════
# 右侧：MoE Transformer
# ══════════════════════════════════════════════════════════════════
txt(ax2, 230, 10, 'MoE Transformer', size=18, color='#e67700', bold=True)

# Input → Attention → Add&Norm → MoE FFN → Add&Norm → Output
box(ax2, 60, 40, 340, LH, '#e9ecef', '#495057')
txt(ax2, 230, 40 + LH/2, 'Input Tokens', size=15)

box(ax2, 60, 105, 340, 55, '#d0ebff', '#1971c2')
txt(ax2, 230, 132, 'Multi-Head Attention', size=15, color='#1971c2')

box(ax2, 60, 180, 340, LH, '#f1f3f5', '#868e96')
txt(ax2, 230, 180 + LH/2, 'Add & Norm', size=15, color='#868e96')

# MoE FFN 大框（紧凑）
moe_y = 245
moe_h = 195
box(ax2, 60, moe_y, 340, moe_h, '#fff3bf', '#e67700', lw=2)
txt(ax2, 230, moe_y + 15, 'MoE FFN', size=13, color='#e67700', bold=True)

# Router 菱形
rx, ry = 230, 280
diamond = plt.Polygon([[rx, ry-18], [rx+30, ry], [rx, ry+18], [rx-30, ry]],
                       facecolor='#d8f5a2', edgecolor='#5c940d', lw=2)
ax2.add_patch(diamond)
txt(ax2, rx, ry, 'Router', size=12, color='#5c940d', bold=True)

# 4 个 Expert（2x2 紧凑网格）
experts = [
    (95,  310, True),  (255, 310, False),
    (95,  370, False), (255, 370, True),
]
for i, (x, y, sel) in enumerate(experts):
    fc = '#fff3bf' if sel else '#f8f9fa'
    ec = '#e67700' if sel else '#ced4da'
    lw = 2 if sel else 1
    alpha = 1.0 if sel else 0.35
    box(ax2, x, y, 120, 40, fc, ec, lw=lw, alpha=alpha)
    txt(ax2, x+60, y+20, f'Expert {i+1}', size=12,
        color=ec if sel else '#adb5bd', bold=sel)

# Router → Expert
for x, y, sel in experts:
    color = '#e67700' if sel else '#ced4da'
    lw = 2 if sel else 1
    ax2.annotate('', xy=(x+60, y), xytext=(rx, ry+18),
                 arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                 linestyle='' if sel else '--'))

txt(ax2, 80, 330, '0.65', size=11, color='#e67700', bold=True)
txt(ax2, 395, 390, '0.80', size=11, color='#e67700', bold=True)

# MoE FFN 以下
box(ax2, 60, 460, 340, LH, '#f1f3f5', '#868e96')
txt(ax2, 230, 460 + LH/2, 'Add & Norm', size=15, color='#868e96')

box(ax2, 60, 525, 340, LH, '#e9ecef', '#495057')
txt(ax2, 230, 525 + LH/2, 'Output', size=15)

# 箭头
arr(ax2, 230, 40+LH, 105)          # Input → Attention
arr(ax2, 230, 160, 180)             # Attention → Add&Norm
arr(ax2, 230, 225, moe_y)           # Add&Norm → MoE
arr(ax2, 230, moe_y+moe_h, 460)     # MoE → Add&Norm
arr(ax2, 230, 505, 525)             # Add&Norm → Output

# 图例（紧凑）
box(ax2, 320, 305, 125, 80, '#ffffff', '#dee2e6', lw=1)
box(ax2, 328, 315, 16, 12, '#fff3bf', '#e67700', lw=2)
txt(ax2, 385, 321, '被选中', size=10, color='#e67700')
box(ax2, 328, 337, 16, 12, '#f8f9fa', '#ced4da', lw=1, alpha=0.35)
txt(ax2, 385, 343, '未选中', size=10, color='#868e96')
box(ax2, 328, 359, 16, 12, '#d8f5a2', '#5c940d', lw=2)
txt(ax2, 385, 365, 'Router', size=10, color='#5c940d')

plt.tight_layout()
out = '/Users/zouapeng/Downloads/03_文档资料/news1/assets/diagram1_moe_layer.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print('saved:', out)
