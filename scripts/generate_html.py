"""从 bundle JSON 文件生成 HTML 预览页。

用法：python generate_html.py [bundle_json_path] [output_html_path]
  bundle_json_path  默认：bundle_today.json
  output_html_path  默认：today.html
"""
import json
import sys
from pathlib import Path

from publishers.html_preview import render_bundle_html
from utils.log import get_logger

logger = get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = _PROJECT_ROOT / "bundle_today.json"
DEFAULT_OUTPUT = _PROJECT_ROOT / "today.html"


def main() -> None:
    bundle_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    html = render_bundle_html(bundle)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("HTML 已生成 → %s", output_path)


if __name__ == "__main__":
    main()
