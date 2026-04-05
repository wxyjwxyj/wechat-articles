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
from utils.errors import News1Error, CDPConnectionError, LoginExpiredError, CollectorError
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
    all_sources = source_repo.list_sources()
    sources = [s for s in all_sources if s.get("type") == "wechat"]

    if not sources:
        logger.warning("未找到微信 source，请先运行 python scripts/seed_sources.py")
        return

    total = 0
    errors: list[str] = []
    for source in sources:
        # 解析 config 字段（DB 中以 JSON 字符串存储）
        cfg = source.get("config", {})
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        fakeid = cfg.get("fakeid", source["external_id"])

        logger.info("抓取: %s (fakeid=%s)", source['name'], fakeid)
        try:
            articles = collector.fetch_articles(source["name"], fakeid)
        except (CDPConnectionError, LoginExpiredError):
            # CDP 或登录态问题影响所有公众号，直接抛出终止
            raise
        except CollectorError as e:
            # 单个公众号采集失败，记录后继续
            logger.warning("[%s] 采集失败: %s", source['name'], e)
            errors.append(source['name'])
            continue

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

    if errors:
        logger.warning("以下公众号采集失败: %s", ", ".join(errors))

    logger.info("采集完成，共写入 %d 篇文章 → %s", total, DB_PATH)


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("采集失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
