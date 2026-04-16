from pathlib import Path
from unittest.mock import patch, MagicMock

from storage.db import init_db
from storage.repository import ItemRepository, SourceRepository
from pipeline.dedupe import dedupe_items, _keyword_dedupe, _merge_group


def test_dedupe_items_keeps_only_unique_urls(tmp_path: Path):
    items = [
        {"url": "https://a", "title": "A", "content_hash": "1"},
        {"url": "https://a", "title": "A", "content_hash": "1"},
        {"url": "https://b", "title": "B", "content_hash": "2"},
    ]

    result = dedupe_items(items)

    assert [item["url"] for item in result] == ["https://a", "https://b"]


def test_item_repository_inserts_only_once_for_same_url(tmp_path: Path):
    db_path = tmp_path / "content.db"
    init_db(db_path)
    SourceRepository(db_path).upsert_source(
        {
            "type": "wechat",
            "name": "量子位",
            "external_id": "fakeid",
            "status": "active",
            "config": {},
        }
    )

    repo = ItemRepository(db_path)
    item = {
        "source_id": 1,
        "source_type": "wechat",
        "title": "A",
        "url": "https://a",
        "author": "量子位",
        "published_at": "2026-04-03T09:30:05",
        "raw_content": "{}",
        "summary": "摘要",
        "cover": "",
        "tags": [],
        "language": "zh",
        "content_hash": "hash-1",
        "status": "raw",
    }

    repo.upsert_item(item)
    repo.upsert_item(item)

    rows = repo.list_items_by_date("2026-04-03")
    assert len(rows) == 1


def test_keyword_dedupe_does_not_merge_different_events_sharing_keyword():
    """仅共享关键词（如 Mythos）但报道不同事件的文章不应被合并。"""
    items = [
        {
            "url": "https://wechat/a",
            "title": "史上最有故事感的技术报告——Claude最强模型Mythos 7个极其精彩的细节",
            "summary": "介绍 Anthropic Mythos 模型的技术细节",
            "source_name": "硅星人Pro",
            "source_type": "wechat",
        },
        {
            "url": "https://techcrunch/b",
            "title": "Trump officials may be encouraging banks to test Anthropic's Mythos model",
            "summary": "Trump officials encouraging banks to test Mythos",
            "source_name": "TechCrunch AI",
            "source_type": "rss",
        },
    ]
    result = _keyword_dedupe(items)
    assert len(result) == 2, "不同事件不应被合并，即使共享 Mythos 关键词"


def test_keyword_dedupe_does_not_merge_claude_related_but_distinct():
    """同一话题（Claude实名认证）但角度不同的文章不应被合并。回归测试：阈值0.4时误合并。"""
    items = [
        {
            "url": "https://wechat/a",
            "title": "Claude实名认证引众怒！要求真人手持证件自拍",
            "summary": "强制验证是为了更精准封号，Opus自己都看不下去",
            "source_name": "新智元",
            "source_type": "wechat",
        },
        {
            "url": "https://wechat/b",
            "title": "Claude半个月连崩7次！全球宕机3小时，强制实名精准封号",
            "summary": "服务稳定性问题与实名认证封号争议",
            "source_name": "量子位",
            "source_type": "wechat",
        },
    ]
    result = _keyword_dedupe(items)
    assert len(result) == 2, "主题相关但角度不同的文章不应被合并"


def test_dedupe_falls_back_to_keyword_when_claude_returns_none():
    """Claude 去重返回 None 时应降级到关键词方案，不丢失文章。"""
    items = [
        {"url": "https://a", "title": "OpenAI releases GPT-5", "summary": "GPT-5 released", "source_name": "A", "source_type": "rss"},
        {"url": "https://b", "title": "OpenAI 发布 GPT-5", "summary": "GPT-5 发布", "source_name": "B", "source_type": "wechat"},
        {"url": "https://c", "title": "GitHub Trending today", "summary": "trending repos", "source_name": "C", "source_type": "rss"},
    ]
    with patch("pipeline.dedupe._claude_dedupe", return_value=None) as mock_claude:
        result = dedupe_items(items, api_key="fake-key")
    mock_claude.assert_called_once()
    # GPT-5 两篇标题相似应被合并为 1 条，GitHub Trending 独立 1 条
    assert len(result) == 2


def test_claude_dedupe_uses_last_json_when_model_self_corrects():
    """Claude 先输出错误 JSON 再自我纠正时，应取最后一个 JSON 对象。"""
    from pipeline.dedupe import _claude_dedupe

    # 模拟 Claude 先输出合并分组，再自我纠正为分开
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''```json\n{"groups": [[1, 2]]}\n```\n\nLet me correct that:\n\n```json\n{"groups": [[1], [2]]}\n```''')]

    items = [
        {"url": "https://a", "title": "Mythos technical details", "source_name": "A"},
        {"url": "https://b", "title": "Trump officials test Mythos", "source_name": "B"},
    ]

    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = mock_response
        result = _claude_dedupe(items, api_key="fake-key")

    assert result is not None
    assert len(result) == 2, "应取最后一个 JSON（分开），而不是第一个（合并）"
