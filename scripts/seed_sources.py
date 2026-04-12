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
    # ── 微信公众号（CDP 采集）──
    {"type": "wechat", "name": "AI寒武纪", "external_id": "Mzg3MTkxMjYzOA==", "status": "active", "config": {"fakeid": "Mzg3MTkxMjYzOA=="}},
    {"type": "wechat", "name": "36氪", "external_id": "MzI2NDk5NzA0Mw==", "status": "active", "config": {"fakeid": "MzI2NDk5NzA0Mw=="}},
    {"type": "wechat", "name": "虎嗅APP", "external_id": "MTQzMjE1NjQwMQ==", "status": "active", "config": {"fakeid": "MTQzMjE1NjQwMQ=="}},
    {"type": "wechat", "name": "硅星人Pro", "external_id": "MzkyNjU2ODM2NQ==", "status": "active", "config": {"fakeid": "MzkyNjU2ODM2NQ=="}},
    # ── 微信公众号（Wechat2RSS 免费 RSS）──
    {"type": "rss", "name": "量子位", "external_id": "wechat_qbitai", "status": "active", "config": {"feed_url": "https://wechat2rss.xlab.app/feed/7131b577c61365cb47e81000738c10d872685908.xml", "max_items": 10, "days_back": 2, "language": "zh", "use_original_time": True, "is_wechat": True}},
    {"type": "rss", "name": "机器之心", "external_id": "wechat_synced", "status": "active", "config": {"feed_url": "https://wechat2rss.xlab.app/feed/51e92aad2728acdd1fda7314be32b16639353001.xml", "max_items": 10, "days_back": 2, "language": "zh", "use_original_time": True, "is_wechat": True}},
    {"type": "rss", "name": "新智元", "external_id": "wechat_aiysjy", "status": "active", "config": {"feed_url": "https://wechat2rss.xlab.app/feed/ede30346413ea70dbef5d485ea5cbb95cca446e7.xml", "max_items": 10, "days_back": 2, "language": "zh", "use_original_time": True, "is_wechat": True}},
    # ── 微信公众号（wechatrss.waytomaster.com）──
    {"type": "rss", "name": "APPSO", "external_id": "wechat_appso", "status": "active", "config": {"feed_url": "https://wechatrss.waytomaster.com/api/rss/MjM5MjAyNDUyMA==?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NjYiLCJ0eXBlIjoicnNzIn0.gt9W9A_sdYmfnamvSobqyhLklPBOHVMQEyOYLyI3n6Y", "max_items": 10, "days_back": 2, "language": "zh", "use_original_time": True, "is_wechat": True}},
    {"type": "rss", "name": "数字生命卡兹克", "external_id": "wechat_kazke", "status": "active", "config": {"feed_url": "https://wechatrss.waytomaster.com/api/rss/MzIyMzA5NjEyMA==?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NjYiLCJ0eXBlIjoicnNzIn0.gt9W9A_sdYmfnamvSobqyhLklPBOHVMQEyOYLyI3n6Y", "max_items": 10, "days_back": 2, "language": "zh", "use_original_time": True, "is_wechat": True}},
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
            "feed_url": "https://www.theverge.com/rss/index.xml",
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
