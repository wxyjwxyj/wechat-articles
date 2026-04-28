"""图3：DeepSeekMoE 架构对比 — 三列演进（v4 自上而下+美化）"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'Songti SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 3, figsize=(20, 9))
for ax in axes:
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 600)
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
# (a) 传统 Top-2 路由
# ══════════════════════════════════════════════════════════════════
ax = axes[0]
txt(ax, 180, 10, '(a) 传统 Top-2 路由', size=16, color='#495057', bold=True)

box(ax, 100, 40, 160, 35, '#e9ecef', '#495057')
txt(ax, 180, 57, 'Token', size=14)

arr(ax, 180, 75, 95)

box(ax, 110, 95, 140, 35, '#d8f5a2', '#5c940d', lw=2)
txt(ax, 180, 112, 'Router', size=13, color='#5c940d', bold=True)

# 4 个大专家
for i, y in enumerate([160, 225, 290, 355]):
    sel = i in [0, 1]
    fc = '#a5d8ff' if sel else '#f8f9fa'
    ec = '#1971c2' if sel else '#ced4da'
    lw = 2 if sel else 1
    alpha = 1.0 if sel else 0.3
    box(ax, 80, y, 200, 45, fc, ec, lw=lw, alpha=alpha)
    txt(ax, 180, y+22, f'Expert {i+1}', size=14,
        color=ec if sel else '#adb5bd', bold=sel)
    # Router → Expert
    color = '#1971c2' if sel else '#ced4da'
    lw_a = 2 if sel else 1
    arr(ax, 180, 130, y, color=color, lw=lw_a)

txt(ax, 180, 430, 'K = 2', size=15, color='#1971c2', bold=True)
txt(ax, 180, 455, '4 个大专家', size=12, color='#868e96')

# ══════════════════════════════════════════════════════════════════
# (b) 细粒度专家分割
# ══════════════════════════════════════════════════════════════════
ax = axes[1]
txt(ax, 180, 10, '(b) 细粒度专家分割', size=16, color='#1971c2', bold=True)

box(ax, 100, 40, 160, 35, '#e9ecef', '#495057')
txt(ax, 180, 57, 'Token', size=14)

arr(ax, 180, 75, 95)

box(ax, 110, 95, 140, 35, '#d8f5a2', '#5c940d', lw=2)
txt(ax, 180, 112, 'Router', size=13, color='#5c940d', bold=True)

# 8 个小专家（2列4行）
positions = []
for row in range(4):
    for col in range(2):
        positions.append((50 + col*130, 155 + row*70))

for i, (x, y) in enumerate(positions):
    sel = i in [0, 5]
    fc = '#a5d8ff' if sel else '#f8f9fa'
    ec = '#1971c2' if sel else '#ced4da'
    lw = 2 if sel else 1
    alpha = 1.0 if sel else 0.3
    box(ax, x, y, 100, 42, fc, ec, lw=lw, alpha=alpha)
    txt(ax, x+50, y+21, f'E{i+1}', size=12,
        color=ec if sel else '#adb5bd', bold=sel)

# Router → 选中的
ax.annotate('', xy=(50+50, 155), xytext=(180, 130),
            arrowprops=dict(arrowstyle='->', color='#1971c2', lw=2))
ax.annotate('', xy=(50+130+50, 155+2*70), xytext=(180, 130),
            arrowprops=dict(arrowstyle='->', color='#1971c2', lw=2))
# Router → 未选中（虚线）
for i, (x, y) in enumerate(positions):
    if i not in [0, 5]:
        ax.annotate('', xy=(x+50, y), xytext=(180, 130),
                    arrowprops=dict(arrowstyle='->', color='#ced4da', lw=1, linestyle='--'))

txt(ax, 180, 450, 'K = 2', size=15, color='#1971c2', bold=True)
txt(ax, 180, 475, '8 个小专家，路由更灵活', size=12, color='#868e96')

# ══════════════════════════════════════════════════════════════════
# (c) DeepSeekMoE
# ══════════════════════════════════════════════════════════════════
ax = axes[2]
txt(ax, 180, 10, '(c) DeepSeekMoE', size=16, color='#e67700', bold=True)

box(ax, 100, 40, 160, 35, '#e9ecef', '#495057')
txt(ax, 180, 57, 'Token', size=14)

arr(ax, 180, 75, 95)

box(ax, 110, 95, 140, 35, '#d8f5a2', '#5c940d', lw=2)
txt(ax, 180, 112, 'Router', size=13, color='#5c940d', bold=True)

# 2 个共享专家（深红色）
for i, y in enumerate([155, 225]):
    box(ax, 50, y, 180, 50, '#ffc9c9', '#e03131', lw=2)
    txt(ax, 140, y+18, f'共享专家 {i+1}', size=13, color='#e03131', bold=True)
    txt(ax, 140, y+38, '（始终激活）', size=9, color='#e03131')
    # Token → 共享专家
    ax.annotate('', xy=(140, y), xytext=(180, 75),
                arrowprops=dict(arrowstyle='->', color='#e03131', lw=2))

# 路由专家（蓝色）
routed = [(260, 160), (260, 220), (260, 280), (260, 340)]
for i, (x, y) in enumerate(routed):
    sel = i in [0, 2]
    fc = '#a5d8ff' if sel else '#f8f9fa'
    ec = '#1971c2' if sel else '#ced4da'
    lw = 2 if sel else 1
    alpha = 1.0 if sel else 0.3
    box(ax, x, y, 70, 40, fc, ec, lw=lw, alpha=alpha)
    txt(ax, x+35, y+20, f'R{i+1}', size=12,
        color=ec if sel else '#adb5bd', bold=sel)
    # Router → 路由专家
    color = '#1971c2' if sel else '#ced4da'
    lw_a = 2 if sel else 1
    ax.annotate('', xy=(x, y+20), xytext=(245, 112),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw_a,
                                linestyle='' if sel else '--'))

txt(ax, 180, 420, '共享专家：始终激活', size=12, color='#e03131', bold=True)
txt(ax, 180, 445, '路由专家：K = 2', size=12, color='#1971c2', bold=True)
txt(ax, 180, 470, '通用知识 + 专业化知识', size=11, color='#868e96')

# 底部标注
fig.text(0.33, 0.04, '拆分', fontsize=15, color='#5c940d', fontweight='bold', ha='center')
fig.text(0.62, 0.04, '+共享专家', fontsize=15, color='#5c940d', fontweight='bold', ha='center')

plt.tight_layout(rect=[0, 0.08, 1, 1])
out = '/Users/zouapeng/Downloads/03_文档资料/news1/assets/diagram3_deepseek_moe.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print('saved:', out)
