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
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _load_claude_config() -> tuple[str, str]:
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("claude_api_key", ""), cfg.get("claude_base_url", "https://api.anthropic.com")
    except Exception:
        return "", "https://api.anthropic.com"


def main() -> None:
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE

    if not bundle_path.exists():
        print(f"⚠ bundle 文件不存在，跳过公众号稿生成：{bundle_path}")
        return

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    api_key, base_url = _load_claude_config()
    if api_key:
        print(f"  🤖 使用 Claude 生成编辑点评...")
    else:
        print("  ℹ 未配置 claude_api_key，生成无点评版本")

    payload = build_mp_article_payload(bundle, api_key=api_key, base_url=base_url)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✓ 公众号发布稿已生成 → {OUTPUT_PATH}")
    print(f"  标题：{payload['title']}")
    print(f"  精选条数：{len(payload.get('commentary', []))} 条")
    print(f"  状态：{payload['status']}")


if __name__ == "__main__":
    main()
