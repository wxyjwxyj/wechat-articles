"""normalize_rss_item 单元测试。"""
from pipeline.normalize import normalize_rss_item


def test_normalize_rss_item_maps_fields():
    source = {"id": 10, "name": "TechCrunch AI", "type": "rss"}
    raw_item = {
        "title": "OpenAI releases GPT-5",
        "url": "https://techcrunch.com/2026/04/05/gpt5",
        "summary": "OpenAI officially launches GPT-5 with multimodal reasoning.",
        "published": "2026-04-05T09:00:00+00:00",
        "source_name": "TechCrunch AI",
    }

    item = normalize_rss_item(source, raw_item)

    assert item["source_id"] == 10
    assert item["source_type"] == "rss"
    assert item["title"] == "OpenAI releases GPT-5"
    assert item["url"] == "https://techcrunch.com/2026/04/05/gpt5"
    assert "OpenAI" in item["summary"]
    assert item["language"] == "en"
    assert item["status"] == "raw"
    assert item["content_hash"]  # 非空


def test_normalize_rss_item_content_hash_stable():
    """相同 source_name+title+url 生成相同 hash（幂等性）。"""
    source = {"id": 10, "name": "TechCrunch AI", "type": "rss"}
    raw_item = {
        "title": "AI news",
        "url": "https://example.com/ai",
        "summary": "Some AI news",
        "published": "2026-04-05T09:00:00+00:00",
        "source_name": "TechCrunch AI",
    }

    item1 = normalize_rss_item(source, raw_item)
    item2 = normalize_rss_item(source, raw_item)
    assert item1["content_hash"] == item2["content_hash"]
