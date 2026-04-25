"""RSS Collector 单元测试（使用 mock，不发真实 HTTP 请求）。"""
from unittest.mock import patch, MagicMock
import feedparser
import pytest

# 模拟一个 feedparser entry 对象
def _make_entry(title, url, summary, published=None):
    from datetime import datetime, timezone
    if published is None:
        published = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    entry = MagicMock()
    entry.title = title
    entry.link = url
    entry.summary = summary
    entry.get.side_effect = lambda k, d="": {"published": published}.get(k, d)
    # feedparser 把时间解析为 struct_time
    import time
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    entry.published_parsed = time.strptime(now_str, "%Y-%m-%d %H:%M:%S")
    entry.tags = []
    return entry

def _make_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = False
    return feed


def test_fetch_filters_by_ai_keywords():
    """只返回标题/摘要包含 AI 关键词的条目。"""
    from collectors.rss import RssCollector

    entries = [
        _make_entry("GPT-5 released by OpenAI", "https://example.com/1", "OpenAI launches GPT-5"),
        _make_entry("Apple shares hit record high", "https://example.com/2", "Stock market news"),
    ]

    with patch("collectors.rss.feedparser.parse", return_value=_make_feed(entries)):
        collector = RssCollector(feed_url="https://fake.feed/rss", max_items=10, days_back=3)
        results = collector.fetch_recent_items()

    assert len(results) == 1
    assert results[0]["title"] == "GPT-5 released by OpenAI"


def test_fetch_returns_required_fields():
    """每条返回结果包含必要字段。"""
    from collectors.rss import RssCollector

    entries = [
        _make_entry("AI agent benchmark 2026", "https://example.com/ai", "New AI benchmarks released"),
    ]

    with patch("collectors.rss.feedparser.parse", return_value=_make_feed(entries)):
        collector = RssCollector(feed_url="https://fake.feed/rss", max_items=10, days_back=3)
        results = collector.fetch_recent_items()

    assert len(results) == 1
    item = results[0]
    for field in ("title", "url", "summary", "published", "source_name"):
        assert field in item, f"缺少字段: {field}"


def test_fetch_respects_max_items():
    """最多返回 max_items 条。"""
    from collectors.rss import RssCollector

    entries = [
        _make_entry(f"AI news {i}", f"https://example.com/{i}", "artificial intelligence update")
        for i in range(10)
    ]

    with patch("collectors.rss.feedparser.parse", return_value=_make_feed(entries)):
        collector = RssCollector(feed_url="https://fake.feed/rss", max_items=3, days_back=3)
        results = collector.fetch_recent_items()

    assert len(results) <= 3
