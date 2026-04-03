# storage/repository.py
import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Optional

from storage.db import get_connection


class SourcePayload(TypedDict):
    type: str
    name: str
    external_id: str
    status: Optional[str]
    config: Optional[dict]


class ItemPayload(TypedDict):
    source_id: int
    source_type: str
    title: str
    url: str
    author: Optional[str]
    published_at: str
    raw_content: str
    summary: Optional[str]
    cover: Optional[str]
    tags: list[str]
    language: str
    content_hash: str
    status: str


class SourceRepository:
    """管理数据源（sources）的仓库类。"""

    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def upsert_source(self, payload: SourcePayload) -> dict:
        """
        插入或更新数据源信息。如果名称（name）已存在则更新其他字段。
        返回操作后的 source 字典。
        """
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    insert into sources(type, name, external_id, status, config, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?)
                    on conflict(name) do update set
                      type=excluded.type,
                      external_id=excluded.external_id,
                      status=excluded.status,
                      config=excluded.config,
                      updated_at=excluded.updated_at
                    returning *
                    """,
                    (
                        payload["type"],
                        payload["name"],
                        payload["external_id"],
                        payload.get("status", "active"),
                        json.dumps(payload.get("config", {}), ensure_ascii=False),
                        now,
                        now,
                    ),
                )
                return dict(cursor.fetchone())

    def list_sources(self) -> list[dict]:
        """列表所有数据源。"""
        with closing(get_connection(self.db_path)) as conn:
            rows = [dict(row) for row in conn.execute("select * from sources order by id asc").fetchall()]
        return rows


class ItemRepository:
    """管理内容条目（items）的仓库类。"""

    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def upsert_item(self, payload: ItemPayload) -> None:
        """
        插入或更新条目。如果 url 已存在则更新所有字段。
        """
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute(
                    """
                    insert into items(
                        source_id, source_type, title, url, author,
                        published_at, raw_content, summary, cover,
                        tags, language, content_hash, status,
                        created_at, updated_at
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(url) do update set
                      title=excluded.title,
                      author=excluded.author,
                      published_at=excluded.published_at,
                      raw_content=excluded.raw_content,
                      summary=excluded.summary,
                      cover=excluded.cover,
                      tags=excluded.tags,
                      language=excluded.language,
                      content_hash=excluded.content_hash,
                      status=excluded.status,
                      updated_at=excluded.updated_at
                    """,
                    (
                        payload["source_id"],
                        payload["source_type"],
                        payload["title"],
                        payload["url"],
                        payload.get("author"),
                        payload["published_at"],
                        payload["raw_content"],
                        payload.get("summary"),
                        payload.get("cover"),
                        json.dumps(payload.get("tags", []), ensure_ascii=False),
                        payload.get("language", "zh"),
                        payload["content_hash"],
                        payload.get("status", "raw"),
                        now,
                        now,
                    ),
                )

    def list_items_by_date(self, date_str: str) -> list[dict]:
        """返回指定日期的所有 item，按 published_at 降序排列。date_str 格式为 YYYY-MM-DD。"""
        start = f"{date_str}T00:00:00"
        end = f"{date_str}T23:59:59"
        with closing(get_connection(self.db_path)) as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    "select * from items where published_at between ? and ? order by published_at desc",
                    (start, end),
                ).fetchall()
            ]
        return rows
