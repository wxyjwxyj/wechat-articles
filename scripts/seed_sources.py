"""初始化微信公众号 source。如果已存在则更新。"""
import sys
from pathlib import Path

# 让 scripts/ 目录下的脚本可以 import 项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.db import init_db
from storage.repository import SourceRepository
from utils.log import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent.parent / "content.db"

SOURCES = [
    {"type": "wechat", "name": "量子位", "external_id": "MzIzNjc1NzUzMw==", "status": "active", "config": {"fakeid": "MzIzNjc1NzUzMw=="}},
    {"type": "wechat", "name": "AI寒武纪", "external_id": "Mzg3MTkxMjYzOA==", "status": "active", "config": {"fakeid": "Mzg3MTkxMjYzOA=="}},
    {"type": "wechat", "name": "机器之心", "external_id": "MzA3MzI4MjgzMw==", "status": "active", "config": {"fakeid": "MzA3MzI4MjgzMw=="}},
    {"type": "wechat", "name": "数字生命卡兹克", "external_id": "MzIyMzA5NjEyMA==", "status": "active", "config": {"fakeid": "MzIyMzA5NjEyMA=="}},
    {"type": "wechat", "name": "APPSO", "external_id": "MjM5MjAyNDUyMA==", "status": "active", "config": {"fakeid": "MjM5MjAyNDUyMA=="}},
    {"type": "wechat", "name": "36氪", "external_id": "MzI2NDk5NzA0Mw==", "status": "active", "config": {"fakeid": "MzI2NDk5NzA0Mw=="}},
    {"type": "wechat", "name": "虎嗅APP", "external_id": "MTQzMjE1NjQwMQ==", "status": "active", "config": {"fakeid": "MTQzMjE1NjQwMQ=="}},
    {"type": "wechat", "name": "新智元", "external_id": "MzI3MTA0MTk1MA==", "status": "active", "config": {"fakeid": "MzI3MTA0MTk1MA=="}},
    {"type": "wechat", "name": "硅星人Pro", "external_id": "MzkyNjU2ODM2NQ==", "status": "active", "config": {"fakeid": "MzkyNjU2ODM2NQ=="}},
    # ── 海外源 ──
    {"type": "hackernews", "name": "Hacker News", "external_id": "hackernews", "status": "active", "config": {"min_score": 20, "max_stories": 10}},
    {"type": "arxiv", "name": "ArXiv", "external_id": "arxiv", "status": "active", "config": {"max_results": 50, "max_papers": 10, "days_back": 2}},
    {"type": "github_trending", "name": "GitHub Trending", "external_id": "github_trending", "status": "active", "config": {"since": "daily", "max_repos": 10}},
    # ── RSS 源 ──
    {
        "type": "rss",
        "name": "TechCrunch AI",
        "external_id": "techcrunch_ai",
        "status": "active",
        "config": {
            "feed_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "max_items": 8,
            "days_back": 2,
        },
    },
    {
        "type": "rss",
        "name": "MIT Technology Review",
        "external_id": "mit_tech_review",
        "status": "active",
        "config": {
            "feed_url": "https://www.technologyreview.com/feed/",
            "max_items": 8,
            "days_back": 2,
        },
    },
    {
        "type": "rss",
        "name": "The Verge AI",
        "external_id": "theverge_ai",
        "status": "active",
        "config": {
            "feed_url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
            "max_items": 8,
            "days_back": 2,
        },
    },
]


def main() -> None:
    init_db(DB_PATH)
    repo = SourceRepository(DB_PATH)
    for source in SOURCES:
        repo.upsert_source(source)
        logger.info("source: %s", source['name'])
    logger.info("已初始化 %d 个 source → %s", len(SOURCES), DB_PATH)


if __name__ == "__main__":
    main()
