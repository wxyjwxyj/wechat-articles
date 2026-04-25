"""Research Hub 搜索历史数据访问层。"""
import json
from contextlib import closing
from pathlib import Path
from storage.db import get_connection, init_db


class ResearchRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = db_path
        init_db(db_path)  # 确保 research_sessions 表存在

    def save_session(self, topic: str, results: dict) -> int:
        """保存一次搜索记录，返回 session id。"""
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                cur = conn.execute(
                    "insert into research_sessions (topic, results_json) values (?, ?)",
                    (topic, json.dumps(results, ensure_ascii=False)),
                )
                return cur.lastrowid

    def list_sessions(self, limit: int = 50) -> list[dict]:
        """列出最近的搜索记录（不含 results_json，只返回摘要）。"""
        with closing(get_connection(self.db_path)) as conn:
            rows = conn.execute(
                "select id, topic, created_at from research_sessions order by created_at desc limit ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session(self, session_id: int) -> dict | None:
        """读取单条搜索记录（含完整 results）。"""
        with closing(get_connection(self.db_path)) as conn:
            row = conn.execute(
                "select id, topic, results_json, created_at from research_sessions where id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["results"] = json.loads(d.pop("results_json"))
            return d
