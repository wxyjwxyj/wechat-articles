"""GitHub Trending 今日 AI/ML 仓库采集入口。"""
import sys
from pathlib import Path

from collectors.github_trending import GitHubTrendingCollector
from pipeline.normalize import normalize_github_trending_repo
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

    # 查找 github_trending source
    sources = source_repo.list_sources()
    gh_source = next((s for s in sources if s.get("type") == "github_trending"), None)

    if not gh_source:
        logger.warning("未找到 github_trending source，请先运行 python scripts/seed_sources.py")
        return

    logger.info("采集 GitHub Trending AI/ML 仓库...")
    collector = GitHubTrendingCollector(
        since="daily",
        max_repos=10,
    )

    repos = collector.fetch_trending_repos()  # 可能抛出 CollectorError
    if not repos:
        logger.info("今日暂无 AI/ML 相关 trending 仓库")
        return

    logger.info("找到 %d 个 AI/ML trending 仓库", len(repos))
    total = 0
    for repo in repos:
        logger.info("  [%d⭐今日] %s", repo.get('stars_today', 0), repo['name'])
        item = normalize_github_trending_repo(gh_source, repo)
        item["tags"] = extract_tags(item)
        item_repo.upsert_item(item)
        total += 1

    logger.info("GitHub Trending 采集完成，共写入 %d 个仓库 → %s", total, DB_PATH)


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("GitHub Trending 采集失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
