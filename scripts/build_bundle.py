"""执行"标准化 → 去重 → 标签 → bundle"流水线，并将结果写入数据库与 bundle_today.json。"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository, BundleRepository
from pipeline.dedupe import dedupe_items
from pipeline.tagging import extract_tags
from pipeline.bundles import build_daily_bundle

DB_PATH = Path(__file__).parent.parent / "content.db"
OUTPUT_PATH = Path(__file__).parent.parent / "bundle_today.json"


def main() -> None:
    today = date.today().isoformat()
    init_db(DB_PATH)

    # 读取当日 item
    item_repo = ItemRepository(DB_PATH)
    raw_items = item_repo.list_items_by_date(today)

    if not raw_items:
        print(f"今日（{today}）暂无内容")
        return

    # 补充 source_name（从 source 表读取）
    source_repo = SourceRepository(DB_PATH)
    sources = {s["id"]: s for s in source_repo.list_sources()}
    for item in raw_items:
        item["source_name"] = sources.get(item["source_id"], {}).get("name", "未知来源")
        # tags 在 DB 中存为 JSON 字符串，需要反序列化
        if isinstance(item.get("tags"), str):
            item["tags"] = json.loads(item["tags"])
        # 如果 tags 为空，补充提取
        if not item.get("tags"):
            item["tags"] = extract_tags(item)

    # 去重
    items = dedupe_items(raw_items)

    # 生成 bundle
    bundle = build_daily_bundle(today, items)

    # 持久化到 DB
    bundle_repo = BundleRepository(DB_PATH)
    bundle_id = bundle_repo.upsert_bundle(bundle)
    # list_items_by_date 返回的 row 包含 DB 自增 id
    item_ids = [item["id"] for item in items if "id" in item]
    bundle_repo.replace_bundle_items(bundle_id, item_ids)

    # 输出 JSON 快照供 HTML/公众号稿件生成器使用
    # 将 items 按 source 分组，方便下游使用
    sources_grouped: dict[str, list[dict]] = {}
    for item in items:
        src = item["source_name"]
        sources_grouped.setdefault(src, []).append(
            {
                "title": item["title"],
                "summary": item.get("summary", ""),
                "published_at": item["published_at"],
                "url": item["url"],
            }
        )
    bundle["sources"] = sources_grouped

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    print(f"✓ bundle 已生成 → {OUTPUT_PATH}")
    print(f"  日期：{today}，条数：{len(items)}，话题：{len(bundle['topics'])}")


if __name__ == "__main__":
    main()
