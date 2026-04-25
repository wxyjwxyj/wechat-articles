"""Hacker News 今日 AI 文章采集入口。从 HN Top Stories 筛选 AI 相关文章并存入 DB。"""
import sys
from pathlib import Path

from collectors.hackernews import HackerNewsCollector
from pipeline.normalize import normalize_hackernews_story
from pipeline.tagging import extract_tags
from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository
from utils.errors import News1Error, CollectorError
from utils.log import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent / "content.db"


def main() -> None:
    init_db(DB_PATH)

    source_repo = SourceRepository(DB_PATH)
    item_repo = ItemRepository(DB_PATH)

    # 查找 hackernews source
    sources = source_repo.list_sources()
    hn_source = next((s for s in sources if s.get("type") == "hackernews"), None)

    if not hn_source:
        logger.warning("未找到 hackernews source，请先运行 python scripts/seed_sources.py")
        return

    logger.info("采集 Hacker News AI 文章...")
    collector = HackerNewsCollector(
        min_score=20,
        max_stories=10,
        scan_limit=200,
    )

    stories = collector.fetch_top_ai_stories()  # 可能抛出 CollectorError
    if not stories:
        logger.info("今天暂无 AI 相关热门文章")
        return

    logger.info("找到 %d 篇 AI 相关文章", len(stories))
    total = 0
    for story in stories:
        logger.info("  [%d↑] %s", story['score'], story['title'][:60])
        item = normalize_hackernews_story(hn_source, story)
        item["tags"] = extract_tags(item)
        item_repo.upsert_item(item)
        total += 1

    logger.info("HN 采集完成，共写入 %d 篇文章 → %s", total, DB_PATH)


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("HN 采集失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
