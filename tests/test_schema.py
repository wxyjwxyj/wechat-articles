from pathlib import Path

from storage.db import init_db, get_connection
from storage.repository import SourceRepository


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
