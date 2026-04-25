"""ArXiv 今日 AI 论文采集入口。从 ArXiv 筛选 AI 相关最新论文并存入 DB。"""
import sys
from pathlib import Path

from collectors.arxiv import ArxivCollector
from pipeline.normalize import normalize_arxiv_paper
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

    # 查找 arxiv source
    sources = source_repo.list_sources()
    arxiv_source = next((s for s in sources if s.get("type") == "arxiv"), None)

    if not arxiv_source:
        logger.warning("未找到 arxiv source，请先运行 python scripts/seed_sources.py")
        return

    logger.info("采集 ArXiv AI 论文...")
    collector = ArxivCollector(
        max_results=50,
        max_papers=10,
        days_back=3,
    )

    papers = collector.fetch_recent_papers()  # 可能抛出 CollectorError
    if not papers:
        logger.info("最近暂无 AI 相关新论文")
        return

    logger.info("找到 %d 篇 AI 论文", len(papers))
    total = 0
    for paper in papers:
        logger.info("  [%d分] %s", paper.get('score', 0), paper['title'][:60])
        item = normalize_arxiv_paper(arxiv_source, paper)
        item["tags"] = extract_tags(item)
        item_repo.upsert_item(item)
        total += 1

    logger.info("ArXiv 采集完成，共写入 %d 篇论文 → %s", total, DB_PATH)


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("ArXiv 采集失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
