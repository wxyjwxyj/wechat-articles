"""RSS 今日 AI 文章采集入口。遍历所有 type=rss 的 source 并存入 DB。"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def _fetch_source(source):
        cfg = source.get("config") or {}
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except json.JSONDecodeError:
                cfg = {}
        feed_url = cfg.get("feed_url", "")
        if not feed_url:
            logger.warning("source %s 缺少 feed_url，跳过", source.get("name"))
            return [], None
        try:
            collector = RssCollector(
                feed_url=feed_url,
                source_name=source.get("name", ""),
                max_items=cfg.get("max_items", 8),
                days_back=cfg.get("days_back", 2),
            )
            items = collector.fetch_recent_items()
            return items, source
        except CollectorError as e:
            logger.warning("采集失败 [%s]: %s", source.get("name"), e)
            return [], source.get("name")

    with ThreadPoolExecutor(max_workers=min(len(rss_sources), 10)) as executor:
        futures = {executor.submit(_fetch_source, s): s for s in rss_sources}
        results = []
        for future in as_completed(futures):
            items, source = future.result()
            if isinstance(source, str):
                errors.append(source)
                continue
            if not items or source is None:
                if source:
                    logger.info("[%s] 今日暂无 AI 相关文章", source.get("name"))
                continue
            for raw_item in items:
                item = normalize_rss_item(source, raw_item)
                item["tags"] = extract_tags(item)
                item_repo.upsert_item(item)
                results.append(item)
            logger.info("[%s] 写入 %d 条", source.get("name"), len(items))
    total = len(results)

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
