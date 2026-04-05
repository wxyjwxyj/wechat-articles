"""执行"标准化 → 去重 → 标签 → bundle"流水线，并将结果写入数据库与 bundle_today.json。"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository, BundleRepository
from pipeline.dedupe import dedupe_items
from pipeline.tagging import extract_tags, extract_tags_batch_with_claude
from pipeline.bundles import build_daily_bundle
from utils.errors import News1Error, PipelineError
from utils.log import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent.parent / "content.db"
OUTPUT_PATH = Path(__file__).parent.parent / "bundle_today.json"
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _load_claude_config() -> tuple[str, str]:
    """从 config.json 读取 Claude API 配置，返回 (api_key, base_url)。"""
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("claude_api_key", ""), cfg.get("claude_base_url", "https://api.anthropic.com")
    except Exception:
        return "", "https://api.anthropic.com"


def _tag_items(items: list[dict], api_key: str, base_url: str) -> None:
    """为 items 打标签，优先用 Claude，无 key 或失败时降级到关键词匹配。"""
    if api_key:
        logger.info("使用 Claude 打标签（共 %d 篇）...", len(items))
        claude_results = extract_tags_batch_with_claude(items, api_key, base_url)
        if claude_results:
            for item, result in zip(items, claude_results):
                item["tags"] = result["tags"] or extract_tags(item)  # Claude 返回空则兜底
                item["score"] = result["score"]
            logger.info("Claude 打标签完成")
            return
    # 降级：关键词匹配
    if not api_key:
        logger.info("未配置 claude_api_key，使用关键词匹配打标签")
    for item in items:
        if not item.get("tags"):
            item["tags"] = extract_tags(item)


def main() -> None:
    today = date.today().isoformat()
    init_db(DB_PATH)

    # 读取当日 item
    item_repo = ItemRepository(DB_PATH)
    raw_items = item_repo.list_items_by_date(today)

    if not raw_items:
        logger.info("今日（%s）暂无内容", today)
        return

    # 补充 source_name（从 source 表读取）
    source_repo = SourceRepository(DB_PATH)
    sources = {s["id"]: s for s in source_repo.list_sources()}
    for item in raw_items:
        item["source_name"] = sources.get(item["source_id"], {}).get("name", "未知来源")
        # tags 在 DB 中存为 JSON 字符串，需要反序列化
        if isinstance(item.get("tags"), str):
            item["tags"] = json.loads(item["tags"])

    # 读取 Claude 配置（去重和打标签共用）
    api_key, base_url = _load_claude_config()

    # 去重（Claude 优先，降级到关键词匹配）
    items = dedupe_items(raw_items, api_key=api_key, base_url=base_url)

    # 打标签（Claude 优先，降级到关键词匹配）
    _tag_items(items, api_key, base_url)

    # 生成 bundle
    bundle = build_daily_bundle(today, items)

    # 持久化到 DB
    bundle_repo = BundleRepository(DB_PATH)
    bundle_id = bundle_repo.upsert_bundle(bundle)
    item_ids = [item["id"] for item in items if "id" in item]
    bundle_repo.replace_bundle_items(bundle_id, item_ids)

    # 按重要性分数降序排列
    items.sort(key=lambda x: x.get("score", 5), reverse=True)

    # 输出 JSON 快照供 HTML/公众号稿件生成器使用
    bundle["items_flat"] = [
        {
            "title": item["title"],
            "summary": item.get("summary", ""),
            "published_at": item["published_at"],
            "url": item.get("url", ""),
            "source_name": item.get("source_name", ""),
            "source_type": item.get("source_type", ""),
            "sources_list": item.get("sources_list", [{
                "source_name": item.get("source_name", ""),
                "url": item.get("url", ""),
            }]),
            "tags": item.get("tags", []),
            "score": item.get("score", 5),
        }
        for item in items
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    logger.info("bundle 已生成 → %s", OUTPUT_PATH)
    logger.info("  日期：%s，条数：%d，话题：%d", today, len(items), len(bundle['topics']))


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("bundle 生成失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
