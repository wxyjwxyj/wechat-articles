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

CONFIG_PATH = Path(__file__).parent / "config.json"
DB_PATH = Path(__file__).parent / "content.db"


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print("✗ 错误: 找不到 config.json")
        print("  请复制 config.example.json 为 config.json 并填写配置")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    config = load_config()
    init_db(DB_PATH)

    collector = WechatCollector(
        cdp_proxy=config.get("cdp_proxy", "http://localhost:3456"),
        token=config.get("token", ""),
        target_id=config.get("target_id", ""),
    )

    source_repo = SourceRepository(DB_PATH)
    item_repo = ItemRepository(DB_PATH)
    sources = source_repo.list_sources()

    if not sources:
        print("⚠ sources 表为空，请先运行 python scripts/seed_sources.py")
        return

    total = 0
    for source in sources:
        # 解析 config 字段（DB 中以 JSON 字符串存储）
        cfg = source.get("config", {})
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        fakeid = cfg.get("fakeid", source["external_id"])

        print(f"\n📡 抓取: {source['name']} (fakeid={fakeid})")
        articles = collector.fetch_articles(source["name"], fakeid)

        if articles:
            print(f"  找到 {len(articles)} 篇")
            for raw in articles:
                print(f"    {raw.get('time', '')} - {raw.get('title', '')[:50]}")
                item = normalize_wechat_article(source, raw)
                item["tags"] = extract_tags(item)
                item_repo.upsert_item(item)
                total += 1
        else:
            print("  今天暂无文章")

    print(f"\n✓ 采集完成，共写入 {total} 篇文章 → {DB_PATH}")


if __name__ == "__main__":
    main()
