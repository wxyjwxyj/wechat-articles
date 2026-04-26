"""publishers/html_preview.py 测试：HTML 生成逻辑。"""
from publishers.html_preview import render_bundle_html, _source_color, _source_color_cache


def _make_bundle(items=None, topics=None, date="2026-04-26"):
    """构造测试用 bundle 数据。"""
    return {
        "bundle_date": date,
        "items_flat": items or [],
        "topics": topics or [],
    }


def _make_item(title="测试标题", summary="测试摘要", score=8, tags=None, sources=None):
    """构造测试用条目。"""
    return {
        "title": title,
        "title_zh": None,
        "summary": summary,
        "summary_zh": None,
        "score": score,
        "tags": tags or ["AI公司"],
        "source_name": "量子位",
        "source_type": "wechat",
        "published_at": "2026-04-26 10:00:00",
        "sources_list": sources or [{"source_name": "量子位", "url": "https://example.com"}],
    }


def test_render_returns_html_string():
    """返回值是包含 DOCTYPE 的 HTML 字符串。"""
    html = render_bundle_html(_make_bundle())
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_render_includes_date():
    """HTML 中包含 bundle 日期。"""
    html = render_bundle_html(_make_bundle(date="2026-04-26"))
    assert "2026-04-26" in html


def test_render_includes_item_title():
    """条目标题被渲染到 HTML 中。"""
    item = _make_item(title="OpenAI 发布 GPT-5")
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "OpenAI 发布 GPT-5" in html


def test_render_escapes_html_in_title():
    """标题中的 HTML 特殊字符被转义。"""
    item = _make_item(title='<script>alert("xss")</script>')
    html = render_bundle_html(_make_bundle(items=[item]))
    # 标题被转义后显示为 &lt;script&gt;，而不是原始的 <script>
    assert "&lt;script&gt;" in html


def test_render_uses_title_zh_when_present():
    """有 title_zh 时优先使用中文标题。"""
    item = _make_item(title="GPT-5 Release")
    item["title_zh"] = "GPT-5 发布"
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "GPT-5 发布" in html
    # 原始英文标题不在标题列中（可能在 data 属性里）


def test_render_summary_truncation():
    """超过 120 字的摘要被截断。"""
    long_summary = "A" * 200
    item = _make_item(summary=long_summary)
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "A" * 120 in html
    assert "…" in html


def test_render_no_digest():
    """空摘要显示"暂无摘要"。"""
    item = _make_item(summary="")
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "暂无摘要" in html


def test_render_score_badge():
    """有分数时显示分数徽章。"""
    item = _make_item(score=9)
    html = render_bundle_html(_make_bundle(items=[item]))
    assert ">9<" in html


def test_render_merged_badge():
    """多来源时显示"多家"徽章。"""
    sources = [
        {"source_name": "量子位", "url": "https://a.com"},
        {"source_name": "机器之心", "url": "https://b.com"},
    ]
    item = _make_item(sources=sources)
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "多家" in html


def test_render_topics_by_category():
    """话题按分类分组显示。"""
    topics = [
        {"name": "GPT-5", "category": "AI公司", "count": 5},
        {"name": "Transformer", "category": "AI技术", "count": 3},
    ]
    html = render_bundle_html(_make_bundle(topics=topics))
    assert "AI公司" in html
    assert "AI技术" in html
    assert "GPT-5" in html


def test_render_merges_academic_to_other():
    """学术分类被归入"其他"。"""
    topics = [{"name": "论文", "category": "学术", "count": 2}]
    html = render_bundle_html(_make_bundle(topics=topics))
    assert "其他" in html


def test_render_source_filter_chips():
    """来源被渲染为筛选 chip。"""
    item = _make_item()
    html = render_bundle_html(_make_bundle(items=[item]))
    assert "量子位" in html
    assert "source-filter" in html


def test_render_wechat_order():
    """公众号按固定顺序排列。"""
    sources = [
        {"source_name": "硅星人Pro", "url": "https://a.com"},
        {"source_name": "量子位", "url": "https://b.com"},
    ]
    item = _make_item(sources=sources)
    html = render_bundle_html(_make_bundle(items=[item]))
    # 量子位应该在硅星人Pro 前面
    assert html.index("量子位") < html.index("硅星人Pro")


def test_source_color_cache_cleared_per_render():
    """每次渲染前清空颜色缓存。"""
    _source_color_cache.clear()
    _source_color("OldSource")
    assert "OldSource" in _source_color_cache
    # 渲染会清空缓存并重新填充，旧的缓存条目不会保留
    render_bundle_html(_make_bundle())
    assert "OldSource" not in _source_color_cache


def test_render_empty_bundle():
    """空 bundle 不报错。"""
    html = render_bundle_html(_make_bundle())
    assert "共采集 0 篇" in html


def test_render_mobile_responsive():
    """包含手机适配的 media query。"""
    html = render_bundle_html(_make_bundle())
    assert "@media (max-width: 768px)" in html
