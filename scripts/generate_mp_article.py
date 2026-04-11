"""从 bundle JSON 文件生成公众号发布稿并输出到 mp_article_preview.json。

用法：python scripts/generate_mp_article.py [bundle_json_path]
  bundle_json_path  默认：bundle_today.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from publishers.mp_article import build_mp_article_payload
from utils.config import get_claude_config
from utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_BUNDLE = Path(__file__).parent.parent / "bundle_today.json"
OUTPUT_PATH = Path(__file__).parent.parent / "mp_article_preview.json"


def main() -> None:
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE

    if not bundle_path.exists():
        logger.warning("bundle 文件不存在，跳过公众号稿生成：%s", bundle_path)
        return

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    api_key, base_url = get_claude_config()
    if api_key:
        logger.info("使用 Claude 生成编辑点评...")
    else:
        logger.info("未配置 claude_api_key，生成无点评版本")

    payload = build_mp_article_payload(bundle, api_key=api_key, base_url=base_url)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("公众号发布稿已生成 → %s", OUTPUT_PATH)
    logger.info("  标题：%s, 精选条数：%d 条, 状态：%s",
                payload['title'], len(payload.get('commentary', [])), payload['status'])


if __name__ == "__main__":
    main()
