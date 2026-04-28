"""生成《读懂 MoE 之前，你需要知道的事》PDF"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── 注册中文字体 ──────────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
pdfmetrics.registerFont(TTFont('PingFangB', '/System/Library/Fonts/PingFang.ttc'))

W, H = A4
OUT = '/Users/zouapeng/Downloads/03_文档资料/news1/assets/MoE前置知识入门.pdf'

# ── 颜色 ──────────────────────────────────────────────────────────────────────
C_BLUE      = colors.HexColor('#1971c2')
C_BLUE_LIGHT= colors.HexColor('#d0ebff')
C_ORANGE    = colors.HexColor('#e67700')
C_ORANGE_LT = colors.HexColor('#fff3bf')
C_GREEN     = colors.HexColor('#2f9e44')
C_GREEN_LT  = colors.HexColor('#d3f9d8')
C_GRAY      = colors.HexColor('#868e96')
C_GRAY_LT   = colors.HexColor('#f1f3f5')
C_DARK      = colors.HexColor('#212529')
C_PURPLE    = colors.HexColor('#7048e8')
C_PURPLE_LT = colors.HexColor('#e5dbff')

# ── 样式 ──────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}
    base = dict(fontName='PingFang', leading=20)

    s['cover_title'] = ParagraphStyle('cover_title',
        fontName='PingFang', fontSize=32, leading=44,
        textColor=C_DARK, alignment=TA_CENTER, spaceAfter=8)

    s['cover_sub'] = ParagraphStyle('cover_sub',
        fontName='PingFang', fontSize=16, leading=26,
        textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=4)

    s['ch_title'] = ParagraphStyle('ch_title',
        fontName='PingFang', fontSize=20, leading=30,
        textColor=C_BLUE, spaceBefore=18, spaceAfter=8,
        borderPad=4)

    s['sec_title'] = ParagraphStyle('sec_title',
        fontName='PingFang', fontSize=14, leading=22,
        textColor=C_DARK, spaceBefore=12, spaceAfter=4,
        leftIndent=0)

    s['body'] = ParagraphStyle('body',
        fontName='PingFang', fontSize=11, leading=20,
        textColor=C_DARK, alignment=TA_JUSTIFY,
        spaceBefore=4, spaceAfter=4)

    s['analogy'] = ParagraphStyle('analogy',
        fontName='PingFang', fontSize=11, leading=20,
        textColor=colors.HexColor('#495057'),
        leftIndent=12, rightIndent=12,
        spaceBefore=6, spaceAfter=6)

    s['highlight'] = ParagraphStyle('highlight',
        fontName='PingFang', fontSize=11, leading=20,
        textColor=C_DARK,
        leftIndent=12, rightIndent=12,
        spaceBefore=6, spaceAfter=6)

    s['code'] = ParagraphStyle('code',
        fontName='PingFang', fontSize=10, leading=18,
        textColor=colors.HexColor('#2b2d42'),
        leftIndent=12, spaceBefore=4, spaceAfter=4)

    s['caption'] = ParagraphStyle('caption',
        fontName='PingFang', fontSize=9, leading=14,
        textColor=C_GRAY, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=8)

    return s

S = make_styles()

# ── 辅助函数 ──────────────────────────────────────────────────────────────────
def sp(n=6):
    return Spacer(1, n)

def hr(color=C_GRAY_LT, thickness=1):
    return HRFlowable(width='100%', thickness=thickness, color=color, spaceAfter=4, spaceBefore=4)

def body(text):
    return Paragraph(text, S['body'])

def sec(text):
    return Paragraph(text, S['sec_title'])

def analogy_box(text):
    """灰色引用框：类比"""
    inner = Paragraph('💡 ' + text, S['analogy'])
    t = Table([[inner]], colWidths=[W - 60*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_GRAY_LT),
        ('ROUNDEDCORNERS', [6]),
        ('BOX', (0,0), (-1,-1), 0.5, C_GRAY),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return t

def highlight_box(text, bg=C_BLUE_LIGHT, border=C_BLUE):
    """彩色高亮框：核心概念"""
    inner = Paragraph(text, S['highlight'])
    t = Table([[inner]], colWidths=[W - 60*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('BOX', (0,0), (-1,-1), 1.5, border),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return t

def chapter(num, title, color=C_BLUE):
    text = f'<font color="#{hex(color.red)[2:].zfill(2)}{hex(color.green)[2:].zfill(2)}{hex(color.blue)[2:].zfill(2)}"><b>第 {num} 章　{title}</b></font>'
    return Paragraph(text, S['ch_title'])

# ── 页眉页脚 ──────────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('PingFang', 9)
    canvas.setFillColor(C_GRAY)
    if doc.page > 1:
        canvas.drawCentredString(W/2, 18*mm, f'读懂 MoE 之前，你需要知道的事　·　第 {doc.page} 页')
        canvas.setStrokeColor(C_GRAY_LT)
        canvas.setLineWidth(0.5)
        canvas.line(20*mm, 22*mm, W-20*mm, 22*mm)
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════════════
# 内容构建
# ══════════════════════════════════════════════════════════════════════════════
story = []

# ── 封面 ──────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 60*mm))
story.append(Paragraph('读懂 MoE 之前', S['cover_title']))
story.append(Paragraph('你需要知道的事', S['cover_title']))
story.append(sp(12))
story.append(Paragraph('零基础入门指南', S['cover_sub']))
story.append(sp(8))
story.append(Paragraph('从神经网络到混合专家模型，一步一步讲清楚', S['cover_sub']))
story.append(Spacer(1, 40*mm))
story.append(hr(C_BLUE, 2))
story.append(sp(6))

toc_data = [
    ['章节', '主题'],
    ['第 1 章', '神经网络是什么'],
    ['第 2 章', '权重（Weight）是什么'],
    ['第 3 章', '训练是怎么回事'],
    ['第 4 章', 'Token 是什么'],
    ['第 5 章', '向量（Vector）是什么'],
    ['第 6 章', '矩阵乘法是什么'],
    ['第 7 章', 'Transformer 是什么'],
    ['第 8 章', 'Attention 是什么'],
    ['第 9 章', 'FFN（全连接网络）是什么'],
    ['第 10 章', '参数量是什么'],
    ['第 11 章', '稠密模型 vs 稀疏模型'],
    ['第 12 章', 'MoE 是什么'],
    ['第 13 章', '训练 vs 推理'],
]
toc_style = TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'PingFang'),
    ('FONTSIZE', (0,0), (-1,-1), 11),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('BACKGROUND', (0,0), (-1,0), C_BLUE),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_GRAY_LT]),
    ('GRID', (0,0), (-1,-1), 0.3, C_GRAY),
    ('LEFTPADDING', (0,0), (-1,-1), 10),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('TEXTCOLOR', (0,1), (0,-1), C_BLUE),
])
toc = Table(toc_data, colWidths=[50*mm, 100*mm])
toc.setStyle(toc_style)
story.append(toc)
story.append(PageBreak())
