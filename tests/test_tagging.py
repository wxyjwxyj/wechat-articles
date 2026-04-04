from pipeline.tagging import extract_tags, build_topics
from pipeline.bundles import build_daily_bundle


def test_extract_tags_matches_known_keywords():
    item = {"title": "Claude Code 与 AI Agent 最新进展", "summary": "智能体工作流"}

    tags = extract_tags(item)

    # 验证关键标签存在（不严格要求顺序和完整列表，因为标签词表可能扩展）
    assert "Claude Code" in tags
    assert "Agent" in tags
    assert "AI" in tags


def test_build_daily_bundle_groups_items_by_source_and_topics():
    items = [
        {"id": 1, "title": "Claude Code", "summary": "摘要", "source_name": "量子位", "tags": ["Claude Code", "AI"], "published_at": "2026-04-03T09:30:05", "url": "https://a"},
        {"id": 2, "title": "多 Agent", "summary": "摘要", "source_name": "机器之心", "tags": ["Agent", "AI"], "published_at": "2026-04-03T10:00:00", "url": "https://b"},
    ]

    bundle = build_daily_bundle("2026-04-03", items)

    assert bundle["bundle_date"] == "2026-04-03"
    assert bundle["title"] == "今日 AI 资讯速览｜2026-04-03"
    assert len(bundle["highlights"]) == 2
    # 验证 topics 包含 AI（不要求排序位置）
    topic_names = [t["name"] for t in bundle["topics"]]
    assert "AI" in topic_names
