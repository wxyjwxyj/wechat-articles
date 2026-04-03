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


class SourceRepository:
    """管理数据源（sources）的仓库类。"""

    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def upsert_source(self, payload: SourcePayload) -> None:
        """
        插入或更新数据源信息。如果名称（name）已存在则更新其他字段。
        """
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.execute(
                    """
                    insert into sources(type, name, external_id, status, config, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?)
                    on conflict(name) do update set
                      type=excluded.type,
                      external_id=excluded.external_id,
                      status=excluded.status,
                      config=excluded.config,
                      updated_at=excluded.updated_at
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

    def list_sources(self) -> list[dict]:
        """列表所有数据源。"""
        with closing(get_connection(self.db_path)) as conn:
            rows = [dict(row) for row in conn.execute("select * from sources order by id asc").fetchall()]
        return rows
