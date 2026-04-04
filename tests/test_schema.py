from pathlib import Path

from storage.db import init_db, get_connection
from storage.repository import SourceRepository, ItemRepository, BundleRepository


def test_init_db_creates_core_tables(tmp_path: Path):
    db_path = tmp_path / "content.db"

    init_db(db_path)
    conn = get_connection(db_path)
    names = {
        row[0]
        for row in conn.execute(
            "select name from sqlite_master where type='table'"
        ).fetchall()
    }

    assert {"sources", "items", "topics", "bundles", "bundle_items", "bundle_topics", "publish_tasks"}.issubset(names)


def test_source_repository_can_insert_and_list_sources(tmp_path: Path):
    db_path = tmp_path / "content.db"
    init_db(db_path)

    repo = SourceRepository(db_path)
    repo.upsert_source(
        {
            "type": "wechat",
            "name": "量子位",
            "external_id": "MzIzNjc1NzUzMw==",
            "status": "active",
            "config": {"fakeid": "MzIzNjc1NzUzMw=="},
        }
    )

    rows = repo.list_sources()

    assert len(rows) == 1
    assert rows[0]["name"] == "量子位"
    assert rows[0]["type"] == "wechat"


def test_bundle_repository_upsert_and_replace(tmp_path: Path):
    db_path = tmp_path / "content.db"
    init_db(db_path)

    # 先创建 source 和 item
    SourceRepository(db_path).upsert_source(
        {"type": "wechat", "name": "量子位", "external_id": "fakeid", "status": "active", "config": {}}
    )
    item_repo = ItemRepository(db_path)
    item_repo.upsert_item(
        {
            "source_id": 1,
            "source_type": "wechat",
            "title": "Test",
            "url": "https://test",
            "author": "量子位",
            "published_at": "2026-04-03T09:00:00",
            "raw_content": "{}",
            "summary": "摘要",
            "cover": "",
            "tags": [],
            "language": "zh",
            "content_hash": "hash-1",
            "status": "raw",
        }
    )

    bundle_repo = BundleRepository(db_path)
    bundle_id = bundle_repo.upsert_bundle(
        {
            "bundle_date": "2026-04-03",
            "title": "今日 AI 资讯速览｜2026-04-03",
            "intro": "测试导语",
            "highlights": [],
            "status": "draft",
        }
    )

    assert isinstance(bundle_id, int)
    assert bundle_id > 0

    bundle_repo.replace_bundle_items(bundle_id, [1])
    bundle_repo.replace_bundle_topics(bundle_id, [])

    # 幂等：再次 upsert 应返回同一 id
    same_id = bundle_repo.upsert_bundle(
        {
            "bundle_date": "2026-04-03",
            "title": "今日 AI 资讯速览｜2026-04-03（更新）",
            "intro": "更新导语",
            "highlights": [],
            "status": "draft",
        }
    )
    assert same_id == bundle_id
