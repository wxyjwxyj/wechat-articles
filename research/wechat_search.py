"""本地公众号文章搜索，从 content.db 按关键词匹配。"""
import sqlite3
import json
from pathlib import Path
from utils.log import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent.parent / "content.db"


class WechatSearcher:
    """本地公众号文章搜索器。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)

    def search_articles(self, topic: str, max_results: int = 10) -> list[dict]:
        """按关键词搜索本地公众号文章。

        Args:
            topic: 搜索主题
            max_results: 最多返回条数

        Returns:
            文章列表，每项包含 title, url, author, summary, tags, published_at
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.warning("打开 content.db 失败: %s", e)
            return []

        try:
            # 用 title + summary + tags 做全文关键词匹配
            sql = """
                SELECT title, url, author, summary, tags, published_at
                FROM items
                WHERE source_type = 'wechat'
                  AND (
                    title LIKE :kw
                    OR summary LIKE :kw
                    OR tags LIKE :kw
                  )
                ORDER BY published_at DESC
                LIMIT :limit
            """
            rows = conn.execute(sql, {"kw": f"%{topic}%", "limit": max_results}).fetchall()
            logger.info("公众号搜索 '%s'：找到 %d 条", topic, len(rows))

            results = []
            for row in rows:
                tags = []
                try:
                    tags = json.loads(row["tags"]) if row["tags"] else []
                except Exception:
                    pass
                results.append({
                    "title": row["title"],
                    "url": row["url"],
                    "author": row["author"] or "",
                    "summary": (row["summary"] or "")[:200],
                    "tags": tags,
                    "published_at": (row["published_at"] or "")[:10],  # 只取日期部分
                })

            return results

        except Exception as e:
            logger.warning("公众号搜索失败: %s", e)
            return []
        finally:
            conn.close()
