# pipeline/bundles.py

from pipeline.tagging import build_topics


def build_daily_bundle(bundle_date: str, items: list[dict]) -> dict:
    """
    根据当日 item 列表生成 bundle 数据结构。
    items 必须包含 source_name、tags 字段。
    """
    topics = build_topics(items)
    highlights = [
        {
            "title": item["title"],
            "summary": item.get("summary", ""),
            "source_name": item["source_name"],
            "url": item["url"],
        }
        for item in items[:5]
    ]
    top_topic_names = ", ".join(topic["name"] for topic in topics[:3]) or "AI"
    intro = f"今天共整理 {len(items)} 篇内容，重点关注 {top_topic_names}。"
    return {
        "bundle_date": bundle_date,
        "title": f"今日 AI 资讯速览｜{bundle_date}",
        "intro": intro,
        "highlights": highlights,
        "topics": topics,
        "items": items,
        "status": "draft",
    }
