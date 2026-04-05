"""RSS 今日 AI 文章采集入口。遍历所有 type=rss 的 source 并存入 DB。"""
import json
import sys
from pathlib import Path

from collectors.rss import RssCollector
from pipeline.normalize import normalize_rss_item
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

    all_sources = source_repo.list_sources()
    rss_sources = [s for s in all_sources if s.get("type") == "rss"]

    if not rss_sources:
        logger.warning("未找到 rss source，请先运行 python scripts/seed_sources.py")
        return

    total = 0
    errors = []

    for source in rss_sources:
        cfg = source.get("config") or {}
        # config 从 DB 读出是 JSON 字符串，需要反序列化
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except json.JSONDecodeError:
                cfg = {}
        feed_url = cfg.get("feed_url", "")
        if not feed_url:
            logger.warning("source %s 缺少 feed_url，跳过", source.get("name"))
            continue

        try:
            collector = RssCollector(
                feed_url=feed_url,
                source_name=source.get("name", ""),
                max_items=cfg.get("max_items", 8),
                days_back=cfg.get("days_back", 2),
            )
            items = collector.fetch_recent_items()
        except CollectorError as e:
            logger.warning("采集失败 [%s]: %s", source.get("name"), e)
            errors.append(source.get("name"))
            continue

        if not items:
            logger.info("[%s] 今日暂无 AI 相关文章", source.get("name"))
            continue

        for raw_item in items:
            item = normalize_rss_item(source, raw_item)
            item["tags"] = extract_tags(item)
            item_repo.upsert_item(item)
            total += 1

        logger.info("[%s] 写入 %d 条", source.get("name"), len(items))

    if errors:
        logger.warning("以下 RSS 源采集失败：%s", ", ".join(errors))

    logger.info("RSS 采集完成，共写入 %d 条 → %s", total, DB_PATH)


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("RSS 采集失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
