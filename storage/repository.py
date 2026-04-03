# storage/repository.py
import json
from datetime import datetime, timezone
from pathlib import Path

from storage.db import get_connection


class SourceRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = db_path

    def upsert_source(self, payload: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
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
        conn.commit()
        conn.close()

    def list_sources(self) -> list[dict]:
        conn = get_connection(self.db_path)
        rows = [dict(row) for row in conn.execute("select * from sources order by id asc").fetchall()]
        conn.close()
        return rows
