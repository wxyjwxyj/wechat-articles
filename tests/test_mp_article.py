from publishers.mp_article import build_mp_article_payload


def test_build_mp_article_payload_contains_sections():
    bundle = {
        "bundle_date": "2026-04-03",
        "title": "今日 AI 资讯速览｜2026-04-03",
        "intro": "测试",
        "topics": [{"name": "Claude Code", "count": 2}, {"name": "Agent", "count": 1}],
        "items_flat": [
            {
                "title": "Claude Code 爆改",
                "summary": "摘要",
                "sources_list": [{"source_name": "量子位", "url": "https://a"}],
                "score": 8,
            }
        ],
    }

    payload = build_mp_article_payload(bundle)

    assert payload["title"] == "今日 AI 资讯速览｜2026-04-03"
    assert "DAILY AI BRIEFING" in payload["body_html"]
    assert "量子位" in payload["body_html"]
    assert payload["status"] == "draft"
    assert payload["bundle_date"] == "2026-04-03"
