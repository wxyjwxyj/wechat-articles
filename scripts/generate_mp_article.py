"""从 bundle JSON 文件生成公众号发布稿并输出到 mp_article_preview.json。

用法：python scripts/generate_mp_article.py [bundle_json_path]
  bundle_json_path  默认：bundle_today.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from publishers.mp_article import build_mp_article_payload

DEFAULT_BUNDLE = Path(__file__).parent.parent / "bundle_today.json"
OUTPUT_PATH = Path(__file__).parent.parent / "mp_article_preview.json"


def main() -> None:
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    payload = build_mp_article_payload(bundle)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✓ 公众号发布稿已生成 → {OUTPUT_PATH}")
    print(f"  标题：{payload['title']}")
    print(f"  状态：{payload['status']}")


if __name__ == "__main__":
    main()
