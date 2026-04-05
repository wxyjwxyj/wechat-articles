"""Hacker News 今日 AI 文章采集入口。从 HN Top Stories 筛选 AI 相关文章并存入 DB。"""
import sys
from pathlib import Path

from collectors.hackernews import HackerNewsCollector
from pipeline.normalize import normalize_hackernews_story
from pipeline.tagging import extract_tags
from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository

DB_PATH = Path(__file__).parent / "content.db"


def main() -> None:
    init_db(DB_PATH)

    source_repo = SourceRepository(DB_PATH)
    item_repo = ItemRepository(DB_PATH)

    # 查找 hackernews source
    sources = source_repo.list_sources()
    hn_source = next((s for s in sources if s.get("type") == "hackernews"), None)

    if not hn_source:
        print("⚠ 未找到 hackernews source，请先运行 python scripts/seed_sources.py")
        return

    print("\n🔶 采集 Hacker News AI 文章...")
    collector = HackerNewsCollector(
        min_score=20,
        max_stories=10,
        scan_limit=200,
    )

    stories = collector.fetch_top_ai_stories()
    if not stories:
        print("  今天暂无 AI 相关热门文章")
        return

    print(f"  找到 {len(stories)} 篇 AI 相关文章")
    total = 0
    for story in stories:
        print(f"    [{story['score']}↑] {story['title'][:60]}")
        item = normalize_hackernews_story(hn_source, story)
        item["tags"] = extract_tags(item)
        item_repo.upsert_item(item)
        total += 1

    print(f"\n✓ HN 采集完成，共写入 {total} 篇文章 → {DB_PATH}")


if __name__ == "__main__":
    main()
