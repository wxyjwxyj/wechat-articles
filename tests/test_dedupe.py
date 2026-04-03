from pathlib import Path

from storage.db import init_db
from storage.repository import ItemRepository, SourceRepository
from pipeline.dedupe import dedupe_items


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
