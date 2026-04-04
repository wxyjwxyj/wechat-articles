from publishers.mp_article import build_mp_article_payload


def test_build_mp_article_payload_contains_sections():
    bundle = {
        "bundle_date": "2026-04-03",
        "title": "今日 AI 资讯速览｜2026-04-03",
        "intro": "今天重点关注 Claude Code 与 Agent。",
        "topics": [{"name": "Claude Code", "count": 2}, {"name": "Agent", "count": 1}],
        "sources": {
            "量子位": [
                {
                    "title": "Claude Code 爆改",
                    "summary": "摘要",
                    "published_at": "2026-04-03T09:30:05",
                    "url": "https://a",
                }
            ]
        },
    }

    payload = build_mp_article_payload(bundle)

    assert payload["title"] == "今日 AI 资讯速览｜2026-04-03"
    assert "今天重点关注 Claude Code 与 Agent。" in payload["body_html"]
    assert "热门主题" in payload["body_html"]
    assert "量子位" in payload["body_html"]
    assert payload["status"] == "draft"
