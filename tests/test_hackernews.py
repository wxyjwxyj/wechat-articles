from unittest.mock import patch, MagicMock

from collectors.hackernews import HackerNewsCollector, _is_ai_related
from pipeline.normalize import normalize_hackernews_story


# ── _is_ai_related 筛选逻辑 ──


def test_is_ai_related_matches_keywords():
    assert _is_ai_related("OpenAI releases GPT-5 with reasoning")
    assert _is_ai_related("New LLM benchmark shows Claude leading")
    assert _is_ai_related("NVIDIA announces new GPU for AI training")


def test_is_ai_related_rejects_non_ai():
    assert not _is_ai_related("Show HN: A new todo app in Rust")
    assert not _is_ai_related("PostgreSQL 17 released")
    assert not _is_ai_related("Ask HN: Best books on management?")


def test_is_ai_related_excludes_hiring():
    assert not _is_ai_related("Ask HN: Who is hiring? (April 2026)")


# ── normalize_hackernews_story ──


def test_normalize_hackernews_story_maps_fields():
    source = {"id": 99, "type": "hackernews", "name": "Hacker News"}
    raw_story = {
        "id": 12345,
        "title": "Claude 4 achieves SOTA on coding benchmarks",
        "url": "https://example.com/claude4",
        "score": 350,
        "comments": 120,
        "time": "2026-04-05T08:30:00+00:00",
        "hn_url": "https://news.ycombinator.com/item?id=12345",
        "by": "testuser",
    }

    item = normalize_hackernews_story(source, raw_story)

    assert item["source_id"] == 99
    assert item["source_type"] == "hackernews"
    assert item["title"] == "Claude 4 achieves SOTA on coding benchmarks"
    assert item["url"] == "https://news.ycombinator.com/item?id=12345"
    assert "https://example.com/claude4" in item["summary"]
    assert item["author"] == "testuser"
    assert item["language"] == "en"
    assert item["status"] == "raw"
    assert "350 points" in item["summary"]
    assert "120 comments" in item["summary"]
    assert item["content_hash"]  # 非空


def test_normalize_hackernews_story_handles_no_url():
    """HN self-post 没有外链时，url 应为 HN 讨论页。"""
    source = {"id": 99, "type": "hackernews"}
    raw_story = {
        "id": 99999,
        "title": "Ask HN: Best AI tools for 2026?",
        "url": "https://news.ycombinator.com/item?id=99999",
        "score": 50,
        "comments": 30,
        "time": "2026-04-05T10:00:00+00:00",
        "hn_url": "https://news.ycombinator.com/item?id=99999",
        "by": "someone",
    }

    item = normalize_hackernews_story(source, raw_story)
    assert "news.ycombinator.com" in item["url"]


# ── HackerNewsCollector（mock API） ──


def test_collector_filters_and_sorts():
    """测试 collector 正确筛选 AI 文章并按 score 排序。"""
    mock_stories = [
        {"id": 1, "type": "story", "title": "PostgreSQL 17 Released", "score": 500, "url": "https://pg.com", "time": 1712345678, "descendants": 200, "by": "a"},
        {"id": 2, "type": "story", "title": "OpenAI launches GPT-5", "score": 300, "url": "https://openai.com", "time": 1712345679, "descendants": 150, "by": "b"},
        {"id": 3, "type": "story", "title": "New LLM training method", "score": 100, "url": "https://arxiv.org", "time": 1712345680, "descendants": 50, "by": "c"},
        {"id": 4, "type": "story", "title": "Claude Code enterprise launch", "score": 200, "url": "https://anthropic.com", "time": 1712345681, "descendants": 80, "by": "d"},
    ]

    def mock_get(url, timeout=10):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "topstories" in url:
            resp.json.return_value = [1, 2, 3, 4]
        else:
            # 从 URL 提取 story ID
            story_id = int(url.split("/")[-1].replace(".json", ""))
            story = next(s for s in mock_stories if s["id"] == story_id)
            resp.json.return_value = story
        return resp

    collector = HackerNewsCollector(min_score=20, max_stories=10, scan_limit=10)
    collector._session = MagicMock()
    collector._session.get.side_effect = mock_get
    results = collector.fetch_top_ai_stories()

    # 应只返回 AI 相关文章（排除 PostgreSQL）
    titles = [r["title"] for r in results]
    assert "PostgreSQL 17 Released" not in titles
    assert "OpenAI launches GPT-5" in titles
    assert "New LLM training method" in titles
    assert "Claude Code enterprise launch" in titles

    # 应按 score 降序
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
