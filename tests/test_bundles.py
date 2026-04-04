from publishers.html_preview import render_bundle_html


def test_render_bundle_html_shows_intro_topics_and_items():
    bundle = {
        "bundle_date": "2026-04-03",
        "title": "今日 AI 资讯速览｜2026-04-03",
        "intro": "今天共整理 2 篇内容。",
        "topics": [{"name": "AI", "count": 2, "category": "AI技术"}],
        "items_flat": [
            {
                "title": "Claude Code",
                "summary": "摘要",
                "published_at": "2026-04-03T09:30:05",
                "sources_list": [{"source_name": "量子位", "url": "https://a"}],
                "score": 8,
            }
        ],
    }

    html = render_bundle_html(bundle)

    # 验证关键内容在 HTML 中
    assert "2026-04-03" in html
    assert "Claude Code" in html
    assert "量子位" in html
