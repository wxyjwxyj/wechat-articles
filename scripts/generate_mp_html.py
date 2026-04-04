"""从 bundle_today.json + mp_article_preview.json 生成导读风 HTML。

用法：python scripts/generate_mp_html.py [bundle_json] [preview_json]
  默认读取项目根目录的 bundle_today.json 和 mp_article_preview.json
  输出到 mp_article_preview.html（根目录）和 archive/digest_YYYY-MM-DD.html
"""
import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_BUNDLE  = PROJECT_DIR / "bundle_today.json"
DEFAULT_PREVIEW = PROJECT_DIR / "mp_article_preview.json"
OUTPUT_HTML     = PROJECT_DIR / "mp_article_preview.html"
ARCHIVE_DIR     = PROJECT_DIR / "archive"


def clean(text: str) -> str:
    return re.sub(r"##[^#]+##", "", text or "").strip()


def source_link(item: dict) -> tuple[str, str]:
    sources = item.get("sources_list", [])
    if len(sources) == 1 and sources[0].get("url"):
        return (
            f'<a href="{sources[0]["url"]}" target="_blank">查看原文 →</a>',
            sources[0].get("source_name", ""),
        )
    elif len(sources) > 1:
        names = " · ".join(s.get("source_name", "") for s in sources if s.get("source_name"))
        links = " ".join(
            f'<a href="{s["url"]}" target="_blank">{s["source_name"]}</a>'
            for s in sources if s.get("url")
        )
        return links, names
    return "", item.get("source_name", "")


def build_html(bundle: dict, preview: dict) -> str:
    items_flat  = bundle.get("items_flat", [])
    highlights  = [item for item in items_flat if item.get("score", 5) >= 6][:8]
    if len(highlights) < 3:
        highlights = items_flat[:8]

    commentary  = preview.get("commentary", [])
    bundle_date = bundle.get("bundle_date", "")
    title       = preview.get("title", f"AI 日报导读 · {bundle_date}")

    cards_html = ""
    for i, item in enumerate(highlights):
        num     = str(i + 1).zfill(2)
        comment = commentary[i] if i < len(commentary) else ""
        summary = clean(item.get("summary", ""))
        summary_short = summary[:100] + "…" if len(summary) > 100 else summary
        link_html, source_name = source_link(item)
        score  = item.get("score", "")
        merged = len(item.get("sources_list", [])) > 1

        comment_block = f"""
      <div class="comment">
        <span class="comment-mark">编辑点评</span>
        <p>{comment}</p>
      </div>""" if comment else ""

        summary_block = f'<p class="summary">{summary_short}</p>' if summary_short else ""
        merged_tag    = '<span class="merged-tag">多家报道</span>' if merged else ""

        cards_html += f"""
    <article class="card" style="animation-delay: {i * 0.08:.2f}s">
      <div class="card-num">{num}</div>
      <div class="card-body">
        <div class="card-meta">
          <span class="source-name">{source_name}</span>
          {merged_tag}
          <span class="score-tag">{score}分</span>
        </div>
        <h2 class="card-title">{item["title"]}</h2>
        {comment_block}
        {summary_block}
        <div class="card-footer">{link_html}</div>
      </div>
    </article>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Noto+Serif+SC:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:      #0c0c0e;
      --border:  #222228;
      --text:    #f0ece2;
      --muted:   #6b6b7a;
      --accent:  #f5a623;
      --accent2: #e8845a;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Noto Serif SC', 'PingFang SC', serif;
      min-height: 100vh;
      background-image: radial-gradient(circle, #ffffff08 1px, transparent 1px);
      background-size: 28px 28px;
    }}
    .masthead {{
      max-width: 760px; margin: 0 auto; padding: 60px 32px 0;
    }}
    .masthead-eyebrow {{
      font-family: 'Playfair Display', serif;
      font-size: 11px; letter-spacing: 4px; text-transform: uppercase;
      color: var(--accent); margin-bottom: 14px;
    }}
    .masthead-title {{
      font-family: 'Playfair Display', serif;
      font-size: clamp(32px, 6vw, 56px); font-weight: 900;
      line-height: 1.08; letter-spacing: -1px;
      color: var(--text); margin-bottom: 20px;
    }}
    .masthead-title em {{ font-style: italic; color: var(--accent); }}
    .masthead-rule {{
      display: flex; align-items: center; gap: 16px; margin-bottom: 12px;
    }}
    .masthead-rule::before, .masthead-rule::after {{
      content: ''; flex: 1; height: 1px; background: var(--border);
    }}
    .masthead-rule span {{
      font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
      color: var(--muted); white-space: nowrap;
    }}
    .masthead-sub {{
      font-size: 13px; color: var(--muted);
      padding-bottom: 32px; border-bottom: 1px solid var(--border);
    }}
    .masthead-sub strong {{ color: var(--accent); font-weight: 600; }}
    .feed {{ max-width: 760px; margin: 0 auto; padding: 0 32px 80px; }}
    .card {{
      display: grid; grid-template-columns: 52px 1fr; gap: 0 20px;
      padding: 32px 0; border-bottom: 1px solid var(--border);
      opacity: 0; transform: translateY(16px);
      animation: rise 0.5s ease forwards;
    }}
    @keyframes rise {{ to {{ opacity: 1; transform: translateY(0); }} }}
    .card-num {{
      font-family: 'Playfair Display', serif;
      font-size: 48px; font-weight: 900; color: var(--border);
      line-height: 1; padding-top: 4px; user-select: none;
      transition: color 0.2s;
    }}
    .card:hover .card-num {{ color: var(--accent); }}
    .card-body {{ min-width: 0; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
    .source-name {{
      font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
      color: var(--muted);
    }}
    .merged-tag {{
      font-size: 10px; background: var(--accent2); color: #fff;
      padding: 1px 6px; border-radius: 3px; letter-spacing: 0.5px;
    }}
    .score-tag {{
      font-size: 10px; color: var(--accent); border: 1px solid #f5a62344;
      padding: 1px 6px; border-radius: 3px; margin-left: auto;
    }}
    .card-title {{
      font-size: 18px; font-weight: 600; line-height: 1.55;
      color: var(--text); margin-bottom: 14px; transition: color 0.2s;
    }}
    .card:hover .card-title {{ color: #fff; }}
    .comment {{
      background: #f5a62309; border-left: 2px solid var(--accent);
      padding: 10px 14px; margin-bottom: 12px; border-radius: 0 6px 6px 0;
    }}
    .comment-mark {{
      display: inline-block; font-size: 9px; letter-spacing: 2px;
      text-transform: uppercase; color: var(--accent); margin-bottom: 5px;
    }}
    .comment p {{ font-size: 13px; line-height: 1.7; color: #c8c4b8; }}
    .summary {{ font-size: 13px; line-height: 1.75; color: var(--muted); margin-bottom: 14px; }}
    .card-footer a {{
      font-size: 12px; color: var(--accent); text-decoration: none;
      letter-spacing: 0.5px; transition: opacity 0.15s;
    }}
    .card-footer a:hover {{ opacity: 0.7; }}
    .card-footer a + a {{ margin-left: 12px; }}
    .page-footer {{
      text-align: center; padding: 24px 32px 48px;
      font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #2e2e38;
    }}
    @media (max-width: 600px) {{
      .masthead, .feed {{ padding-left: 20px; padding-right: 20px; }}
      .card {{ grid-template-columns: 36px 1fr; gap: 0 12px; }}
      .card-num {{ font-size: 32px; }}
    }}
  </style>
</head>
<body>
  <div class="masthead">
    <div class="masthead-eyebrow">AI Daily Digest</div>
    <h1 class="masthead-title">今日 <em>AI</em><br>资讯速览</h1>
    <div class="masthead-rule"><span>{bundle_date}</span></div>
    <p class="masthead-sub">编辑精选 <strong>{len(highlights)} 条</strong>重要资讯 &nbsp;·&nbsp; 自动采集 + Claude 导读</p>
  </div>
  <div class="feed">
    {cards_html}
  </div>
  <div class="page-footer">AI Daily · {bundle_date} · Powered by Claude</div>
</body>
</html>"""


def main() -> None:
    bundle_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    preview_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PREVIEW

    if not bundle_path.exists():
        print(f"⚠ bundle 文件不存在：{bundle_path}")
        return
    if not preview_path.exists():
        print(f"⚠ preview 文件不存在：{preview_path}")
        return

    bundle  = json.loads(bundle_path.read_text(encoding="utf-8"))
    preview = json.loads(preview_path.read_text(encoding="utf-8"))

    html = build_html(bundle, preview)

    # 写到根目录
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"✓ 导读 HTML 已生成 → {OUTPUT_HTML}")

    # 同时归档一份
    bundle_date = bundle.get("bundle_date", "")
    if bundle_date:
        ARCHIVE_DIR.mkdir(exist_ok=True)
        archive_path = ARCHIVE_DIR / f"digest_{bundle_date}.html"
        archive_path.write_text(html, encoding="utf-8")
        print(f"✓ 归档 → {archive_path}")


if __name__ == "__main__":
    main()
