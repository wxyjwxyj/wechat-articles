from publishers.html_preview import render_bundle_html


def test_render_bundle_html_shows_intro_topics_and_items():
    bundle = {
        "bundle_date": "2026-04-03",
        "title": "今日 AI 资讯速览｜2026-04-03",
        "intro": "今天共整理 2 篇内容。",
        "topics": [{"name": "AI", "count": 2}],
        "sources": {
            "量子位": [
                {
                    "title": "Claude Code",
                    "summary": "摘要",
                    "published_at": "2026-04-03T09:30:05",
                    "url": "https://a",
                }
            ]
        },
    }

    html = render_bundle_html(bundle)

    assert "今日 AI 资讯速览｜2026-04-03" in html
    assert "今天共整理 2 篇内容。" in html
    assert "AI (2)" in html
    assert "Claude Code" in html
