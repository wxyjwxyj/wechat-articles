"""迁移：items 表冲突键从 url unique 改为 content_hash unique。

SQLite 不支持 DROP CONSTRAINT，用重建表方式迁移。
重复 content_hash 时保留 id 最大（最新）的一条。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.db import get_connection

DB_PATH = Path(__file__).parent.parent / "content.db"


def migrate(db_path):
    conn = get_connection(db_path)

    # PRAGMA foreign_keys 必须在事务外执行才生效
    conn.execute("PRAGMA foreign_keys = OFF")

    # 前置检查：是否存在重复 content_hash
    dups = conn.execute(
        "SELECT content_hash, count(*) c FROM items GROUP BY content_hash HAVING c > 1"
    ).fetchall()

    with conn:
        if dups:
            print(f"发现 {len(dups)} 组重复 content_hash，将保留每组最大 id 的记录")
            conn.execute("""
                DELETE FROM items WHERE id NOT IN (
                    SELECT max(id) FROM items GROUP BY content_hash
                )
            """)

        conn.execute("""
            CREATE TABLE items_new (
              id integer primary key autoincrement,
              source_id integer not null,
              source_type text not null,
              title text not null,
              url text not null,
              author text,
              published_at text not null,
              raw_content text not null,
              summary text,
              cover text,
              tags text not null default '[]',
              language text not null default 'zh',
              content_hash text not null unique,
              status text not null default 'raw',
              created_at text not null,
              updated_at text not null,
              foreign key(source_id) references sources(id)
            )
        """)
        conn.execute("INSERT INTO items_new SELECT * FROM items")
        conn.execute("DROP TABLE items")
        conn.execute("ALTER TABLE items_new RENAME TO items")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_published_at ON items(published_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_source_id ON items(source_id)")

    # 事务提交后再恢复外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    conn2 = get_connection(db_path)
    count = conn2.execute("SELECT count(*) FROM items").fetchone()[0]
    conn2.close()
    print(f"迁移完成，items 表共 {count} 条记录")


if __name__ == "__main__":
    migrate(DB_PATH)
