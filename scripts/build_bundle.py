"""执行"标准化 → 去重 → 标签 → bundle"流水线，并将结果写入数据库与 bundle_today.json。"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone, timedelta
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

_CST = timezone(timedelta(hours=8))

DB_PATH = Path(__file__).parent.parent / "content.db"
OUTPUT_PATH = Path(__file__).parent.parent / "bundle_today.json"


def _published_date_cst(item: dict) -> str:
    """将 published_at 转换为北京时间日期字符串（YYYY-MM-DD）。假设 DB 中所有 published_at 均为 UTC。"""
    raw = item.get("published_at", "")
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_CST).date().isoformat()
    except (ValueError, TypeError):
        return raw[:10]


def _translate_overseas_items(items: list[dict], item_repo) -> None:
    """为非 wechat 条目并发翻译 title/summary，写入 title_zh/summary_zh 并回写 DB。"""
    from utils.claude import claude_call
    overseas = [i for i in items if i.get("source_type") != "wechat" and i.get("language", "en") != "zh"]
    targets = [i for i in overseas if not i.get("title_zh")]  # 已有翻译则跳过
    skipped = len(overseas) - len(targets)
    if not targets:
        if overseas:
            logger.info("翻译跳过（全部已缓存，共 %d 条）", len(overseas))
        return

    def _translate_one(item: dict) -> bool:
        prompt = (
            f'Translate the following title and summary into Chinese. '
            f'Return JSON only, format: {{"title_zh": "...", "summary_zh": "..."}}. '
            f'Use 「」instead of double quotes within translated text. Do not use " in the output.\n'
            f'title: {item["title"]}\nsummary: {item.get("summary", "")}'
        )
        try:
            raw = claude_call(prompt, max_tokens=512)
            start, end = raw.find("{"), raw.rfind("}") + 1
            if start == -1:
                raise ValueError("无 JSON 对象")
            r = json.loads(raw[start:end])
            item["title_zh"] = r.get("title_zh", "") or item["title"]
            item["summary_zh"] = r.get("summary_zh", "")
            if item.get("id"):
                item_repo.update_item_translations(item["id"], item["title_zh"], item["summary_zh"])
            else:
                logger.warning("item 缺少 id，跳过回写: %s", item["title"][:30])
            return True
        except Exception as e:
            logger.warning("翻译失败（%s）: %s", item["title"][:30], e)
            return False

    success = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_translate_one, item): item for item in targets}
        for future in as_completed(futures):
            if future.result():
                success += 1
    logger.info("翻译完成（新翻译 %d 条，缓存复用 %d 条）", success, skipped)


def _is_wechat_source(s: dict) -> bool:
    """判断 source 是否为微信公众号（type=wechat 或 config.is_wechat=True）。"""
    if s.get("type") == "wechat":
        return True
    cfg = s.get("config", {})
    if isinstance(cfg, str):
        try:
            cfg = json.loads(cfg)
        except Exception:
            cfg = {}
    return bool(cfg.get("is_wechat"))


def _tag_items(items: list[dict]) -> None:
    """为 items 打标签，优先用 Claude，失败时降级到关键词匹配。"""
    logger.info("使用 Claude 打标签（共 %d 篇）...", len(items))
    claude_results = extract_tags_batch_with_claude(items)
    if claude_results:
        for item, result in zip(items, claude_results):
            item["tags"] = result["tags"] or extract_tags(item)  # Claude 返回空则兜底
            item["score"] = result["score"]
        logger.info("Claude 打标签完成")
        return
    # 降级：关键词匹配
    logger.info("Claude 打标签失败，使用关键词匹配")
    for item in items:
        if not item.get("tags"):
            item["tags"] = extract_tags(item)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat(), help="指定日期 YYYY-MM-DD")
    args = parser.parse_args()
    today = args.date
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

    # 微信公众号严格按发布日期过滤：只保留采集日当天发布的文章
    # 判断条件：source_type=wechat 或 config.is_wechat=True
    wechat_source_ids = {s["id"] for s in sources.values() if _is_wechat_source(s)}
    logger.debug("识别到微信源 %d 个: %s", len(wechat_source_ids), wechat_source_ids)
    before = len(raw_items)
    raw_items = [
        item for item in raw_items
        if item.get("source_id") not in wechat_source_ids
        or _published_date_cst(item) == today
    ]
    filtered = before - len(raw_items)
    if filtered:
        logger.info("微信公众号日期过滤：移除 %d 条非采集日文章（采集日=%s）", filtered, today)

    items = dedupe_items(raw_items)

    # 打标签（Claude 优先，降级到关键词匹配）
    _tag_items(items)

    # 多来源加成：每多一家报道 +0.5，上限 10（无论打标签是否用 Claude）
    for item in items:
        source_count = len(item.get("sources_list", []))
        if source_count > 1 and item.get("score") is not None:
            item["score"] = min(10, item["score"] + (source_count - 1) * 0.5)

    # 翻译海外源标题/摘要（已有翻译的跳过，翻译结果回写 DB）
    _translate_overseas_items(items, item_repo)

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
            "title_zh": item.get("title_zh", ""),
            "summary": item.get("summary", ""),
            "summary_zh": item.get("summary_zh", ""),
            "published_at": item["published_at"],
            "url": item.get("url", ""),
            "source_name": item.get("source_name", ""),
            "source_type": item.get("source_type", ""),
            "sources_list": item.get("sources_list", [{
                "source_name": item.get("source_name", ""),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
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
