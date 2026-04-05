"""微信公众号当日文章采集入口。从 content.db sources 表读取账号，抓取今日文章并存入 DB。"""
import json
import sys
import os
from pathlib import Path

from collectors.wechat_collector import WechatCollector
from pipeline.normalize import normalize_wechat_article
from pipeline.tagging import extract_tags
from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository
from utils.log import get_logger

logger = get_logger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"
DB_PATH = Path(__file__).parent / "content.db"


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        logger.error("找不到 config.json，请复制 config.example.json 为 config.json 并填写配置")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    config = load_config()
    init_db(DB_PATH)

    collector = WechatCollector(
        cdp_proxy=config.get("cdp_proxy", "http://localhost:3456"),
    )

    source_repo = SourceRepository(DB_PATH)
    item_repo = ItemRepository(DB_PATH)
    sources = source_repo.list_sources()

    if not sources:
        logger.warning("sources 表为空，请先运行 python scripts/seed_sources.py")
        return

    total = 0
    for source in sources:
        # 解析 config 字段（DB 中以 JSON 字符串存储）
        cfg = source.get("config", {})
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        fakeid = cfg.get("fakeid", source["external_id"])

        logger.info("抓取: %s (fakeid=%s)", source['name'], fakeid)
        articles = collector.fetch_articles(source["name"], fakeid)

        if articles:
            logger.info("  找到 %d 篇", len(articles))
            for raw in articles:
                logger.info("    %s - %s", raw.get('time', ''), raw.get('title', '')[:50])
                item = normalize_wechat_article(source, raw)
                item["tags"] = extract_tags(item)
                item_repo.upsert_item(item)
                total += 1
        else:
            logger.info("  今天暂无文章")

    logger.info("采集完成，共写入 %d 篇文章 → %s", total, DB_PATH)


if __name__ == "__main__":
    main()
