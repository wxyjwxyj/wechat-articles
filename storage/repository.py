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
    title_zh: Optional[str]
    summary_zh: Optional[str]


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
        插入或更新条目。如果 content_hash 已存在则更新可变字段（url 允许更新以修正采集错误）。
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
                    on conflict(content_hash) do update set
                      title=excluded.title,
                      url=excluded.url,
                      author=excluded.author,
                      published_at=excluded.published_at,
                      raw_content=excluded.raw_content,
                      summary=excluded.summary,
                      cover=excluded.cover,
                      tags=excluded.tags,
                      language=excluded.language,
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

    def update_item_summary(self, item_id: int, summary: str) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute(
                    "update items set summary=?, updated_at=? where id=?",
                    (summary, now, item_id),
                )

    def update_item_translations(self, item_id: int, title_zh: str, summary_zh: str) -> None:
        """回写翻译结果到数据库。"""
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute(
                    "update items set title_zh=?, summary_zh=?, updated_at=? where id=?",
                    (title_zh, summary_zh, now, item_id),
                )

    def list_items_by_date(self, date_str: str) -> list[dict]:
        """返回指定日期采集或发布的所有 item，按 published_at 降序排列。date_str 格式为 YYYY-MM-DD。
        published_at 按北京时间（UTC+8）换算日期，兼容带时区后缀（+00:00）和不带时区的 ISO 格式。
        """
        with closing(get_connection(self.db_path)) as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    "select * from items where date(created_at, '+8 hours') = ? or date(published_at, '+8 hours') = ? order by published_at desc",
                    (date_str, date_str),
                ).fetchall()
            ]
        return rows


class BundleRepository:
    """bundle、bundle_items、bundle_topics 的持久化接口。"""

    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def upsert_bundle(self, bundle: dict) -> int:
        """插入或更新 bundle，返回 bundle.id。"""
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute(
                    """
                    insert into bundles(bundle_date, title, intro, highlights, status, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?)
                    on conflict(bundle_date) do update set
                      title=excluded.title,
                      intro=excluded.intro,
                      highlights=excluded.highlights,
                      status=excluded.status,
                      updated_at=excluded.updated_at
                    """,
                    (
                        bundle["bundle_date"],
                        bundle["title"],
                        bundle["intro"],
                        json.dumps(bundle.get("highlights", []), ensure_ascii=False),
                        bundle.get("status", "draft"),
                        now,
                        now,
                    ),
                )
                row = conn.execute(
                    "select id from bundles where bundle_date = ?",
                    (bundle["bundle_date"],),
                ).fetchone()
        return row["id"]

    def replace_bundle_items(self, bundle_id: int, item_ids: list[int]) -> None:
        """替换 bundle 关联的 item 列表（先删后插）。"""
        # 保序去重，防止重复 item_id 触发唯一约束
        seen = set()
        unique_ids = [x for x in item_ids if not (x in seen or seen.add(x))]
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute("delete from bundle_items where bundle_id = ?", (bundle_id,))
                conn.executemany(
                    "insert into bundle_items(bundle_id, item_id, sort_order) values (?, ?, ?)",
                    [(bundle_id, item_id, i) for i, item_id in enumerate(unique_ids)],
                )

    def replace_bundle_topics(self, bundle_id: int, topic_ids: list[int]) -> None:
        """替换 bundle 关联的 topic 列表（先删后插）。"""
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute("delete from bundle_topics where bundle_id = ?", (bundle_id,))
                conn.executemany(
                    "insert into bundle_topics(bundle_id, topic_id) values (?, ?)",
                    [(bundle_id, topic_id) for topic_id in topic_ids],
                )

    def get_bundle_by_date(self, bundle_date: str) -> dict | None:
        """按日期获取 bundle。不存在时返回 None。"""
        with closing(get_connection(self.db_path)) as conn:
            row = conn.execute(
                "select * from bundles where bundle_date = ?",
                (bundle_date,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)
