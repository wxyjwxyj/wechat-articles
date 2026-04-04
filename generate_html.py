"""从 bundle JSON 文件生成 HTML 预览页。

用法：python generate_html.py [bundle_json_path] [output_html_path]
  bundle_json_path  默认：bundle_today.json
  output_html_path  默认：today.html
"""
import json
import sys
from pathlib import Path

from publishers.html_preview import render_bundle_html

DEFAULT_BUNDLE = Path(__file__).parent / "bundle_today.json"
DEFAULT_OUTPUT = Path(__file__).parent / "today.html"


def main() -> None:
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    html = render_bundle_html(bundle)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ HTML 已生成 → {output_path}")


if __name__ == "__main__":
    main()
