"""ItemRepository 核心逻辑测试：content_hash 冲突更新、翻译回写、日期过滤。"""
from datetime import date
from pathlib import Path

import pytest

from storage.db import init_db
from storage.repository import ItemRepository, SourceRepository

TODAY = date.today().isoformat()
YESTERDAY = "2000-01-01"  # 固定的过去日期，不会与 created_at 冲突


def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "content.db"
    init_db(db_path)
    SourceRepository(db_path).upsert_source(
        {"type": "wechat", "name": "量子位", "external_id": "fakeid", "status": "active", "config": {}}
    )
    return db_path


def _item(title="标题", url="https://example.com", content_hash="hash-1", published_at=None):
    return {
        "source_id": 1,
        "source_type": "wechat",
        "title": title,
        "url": url,
        "author": None,
        "published_at": published_at or f"{TODAY}T10:00:00",
        "raw_content": "{}",
        "summary": "摘要",
        "cover": "",
        "tags": [],
        "language": "zh",
        "content_hash": content_hash,
        "status": "raw",
    }


def test_upsert_item_conflict_updates_url(tmp_path):
    db = _make_db(tmp_path)
    repo = ItemRepository(db)

    repo.upsert_item(_item(url="https://old.com", content_hash="hash-1"))
    repo.upsert_item(_item(url="https://new.com", content_hash="hash-1"))

    rows = repo.list_items_by_date(TODAY)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://new.com"


def test_upsert_item_different_hash_inserts_new(tmp_path):
    db = _make_db(tmp_path)
    repo = ItemRepository(db)

    repo.upsert_item(_item(title="A", content_hash="hash-1"))
    repo.upsert_item(_item(title="B", content_hash="hash-2"))

    rows = repo.list_items_by_date(TODAY)
    assert len(rows) == 2


def test_update_item_translations(tmp_path):
    db = _make_db(tmp_path)
    repo = ItemRepository(db)
    repo.upsert_item(_item())

    rows = repo.list_items_by_date(TODAY)
    item_id = rows[0]["id"]

    repo.update_item_translations(item_id, "中文标题", "中文摘要")

    rows = repo.list_items_by_date(TODAY)
    assert rows[0]["title_zh"] == "中文标题"
    assert rows[0]["summary_zh"] == "中文摘要"


def test_list_items_by_date_filters_correctly(tmp_path):
    db = _make_db(tmp_path)
    repo = ItemRepository(db)

    # 今天的记录（published_at = today）
    repo.upsert_item(_item(content_hash="h1"))
    # 过去的记录（published_at = YESTERDAY，created_at 也是今天，但 published_at 不匹配今天）
    repo.upsert_item(_item(content_hash="h2", published_at=f"{YESTERDAY}T10:00:00"))

    today_rows = repo.list_items_by_date(TODAY)
    # h1 的 published_at 和 created_at 都是今天，h2 的 published_at 是 YESTERDAY
    # 但 h2 的 created_at 也是今天，所以 OR 条件下 h2 也会被今天的查询匹配
    # 这是预期行为：created_at OR published_at 任一匹配即返回
    assert any(r["content_hash"] == "h1" for r in today_rows)

    # 查一个完全不存在的日期（既不是 created_at 也不是 published_at）
    empty = repo.list_items_by_date("1999-01-01")
    assert len(empty) == 0
