"""根据 bundle 数据生成 HTML 预览页。"""
from datetime import datetime


# 来源名固定颜色，超出则循环
_SOURCE_COLORS = [
    "#667eea", "#f093fb", "#4facfe", "#43e97b", "#fa709a",
    "#a18cd1", "#fccb90", "#84fab0", "#f5576c", "#4481eb",
]
_source_color_cache: dict[str, str] = {}


def _source_color(name: str) -> str:
    if name not in _source_color_cache:
        idx = len(_source_color_cache) % len(_SOURCE_COLORS)
        _source_color_cache[name] = _SOURCE_COLORS[idx]
    return _source_color_cache[name]


def _source_badges_html(sources_list: list[dict]) -> str:
    """将 sources_list 渲染为带颜色的来源徽章。"""
    parts = []
    for s in sources_list:
        if not s.get("url"):
            continue
        color = _source_color(s["source_name"])
        parts.append(
            f"<a href='{s['url']}' target='_blank' class='source-badge' "
            f"style='background:{color}22;color:{color};border-color:{color}44'>"
            f"{s['source_name']}</a>"
        )
    return "".join(parts)


def render_bundle_html(bundle: dict) -> str:
    # 清空颜色缓存，保证每次生成颜色分配一致
    _source_color_cache.clear()

    items_flat = bundle.get("items_flat", [])
    total_articles = len(items_flat)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bundle_date = bundle.get("bundle_date", "")

    # 话题标签
    topics_html = ""
    for topic in bundle.get("topics", []):
        topics_html += f"<span class='topic-tag' data-tag='{topic['name']}'>{topic['name']} <em>{topic['count']}</em></span>\n"

    # 收集所有来源（去重，保持顺序）
    seen_sources: list[str] = []
    for item in items_flat:
        for s in item.get("sources_list", [{"source_name": item.get("source_name", "")}]):
            name = s.get("source_name", "")
            if name and name not in seen_sources:
                seen_sources.append(name)

    # 来源筛选按钮
    sources_filter_html = ""
    for name in seen_sources:
        color = _source_color(name)
        sources_filter_html += (
            f"<span class='source-filter' data-source='{name}' "
            f"style='background:{color}18;color:{color};border-color:{color}55'>"
            f"{name}</span>\n"
        )

    # 文章行
    rows_html = ""
    for item in items_flat:
        sources_list = item.get("sources_list", [{
            "source_name": item.get("source_name", ""),
            "url": item.get("url", ""),
        }])
        badges = _source_badges_html(sources_list)
        summary = item.get("summary", "")
        # 截断过长的 summary（超过 120 字折叠显示）
        summary_short = summary[:120] + "…" if len(summary) > 120 else summary
        summary_html = f"<div class='digest'>{summary_short}</div>" if summary_short else "<div class='digest no-digest'>暂无摘要</div>"

        # 时间：只显示 HH:MM
        pub = item.get("published_at", "")
        time_str = pub[11:16] if len(pub) >= 16 else ""

        # 多来源时加聚合标记
        merged = len(sources_list) > 1
        merged_badge = "<span class='merged-badge'>多家</span>" if merged else ""

        # data-tags / data-sources 供 JS 过滤使用
        tags_attr = " ".join(item.get("tags", []))
        sources_attr = "|".join(s.get("source_name", "") for s in sources_list)
        rows_html += f"""<tr class='article-row{"" if not merged else " merged"}' data-tags='{tags_attr}' data-sources='{sources_attr}'>
  <td class='col-title'>
    {merged_badge}
    <span class='title-text'>{item['title']}</span>
  </td>
  <td class='col-digest'>{summary_html}</td>
  <td class='col-sources'>{badges}</td>
  <td class='col-time'>{time_str}</td>
</tr>\n"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>微信公众号文章汇总 - {bundle_date}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: #f0f2f5;
      line-height: 1.6;
      color: #333;
    }}
    .container {{
      max-width: 1200px;
      margin: 24px auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      overflow: hidden;
    }}

    /* 顶部 Header */
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 28px 32px 24px;
    }}
    .header h1 {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.3px;
      margin-bottom: 6px;
    }}
    .header .meta {{
      font-size: 13px;
      opacity: 0.8;
    }}

    /* 话题栏 */
    .topics-bar {{
      background: #f8f9fb;
      padding: 16px 32px;
      border-bottom: 1px solid #eaecf0;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .topics-label {{
      font-size: 12px;
      color: #999;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-right: 4px;
    }}
    .topic-tag {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      user-select: none;
      transition: opacity 0.15s, transform 0.1s;
    }}
    .topic-tag:hover {{ opacity: 0.85; transform: translateY(-1px); }}
    .topic-tag.active {{
      box-shadow: 0 0 0 3px rgba(102,126,234,0.35);
      transform: translateY(-1px);
    }}
    .topic-tag.dimmed {{ opacity: 0.35; }}

    /* 来源筛选栏 */
    .sources-bar {{
      background: #fff;
      padding: 12px 32px;
      border-bottom: 1px solid #eaecf0;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .source-filter {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid;
      cursor: pointer;
      user-select: none;
      transition: opacity 0.15s, transform 0.1s, box-shadow 0.1s;
      white-space: nowrap;
    }}
    .source-filter:hover {{ opacity: 0.8; transform: translateY(-1px); }}
    .source-filter.active {{ box-shadow: 0 0 0 2px currentColor; transform: translateY(-1px); }}
    .source-filter.dimmed {{ opacity: 0.3; }}

    /* 表格 */
    .table-wrap {{ padding: 0 32px 28px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }}
    th {{
      background: #f8f9fb;
      padding: 10px 12px;
      text-align: left;
      font-size: 12px;
      font-weight: 600;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 2px solid #eaecf0;
    }}
    td {{
      padding: 14px 12px;
      border-bottom: 1px solid #f0f2f5;
      vertical-align: top;
    }}
    tr.article-row:hover td {{ background: #fafbff; }}
    tr.merged td {{ background: #fdf9ff; }}
    tr.merged:hover td {{ background: #f8f2ff; }}

    /* 标题列 */
    .col-title {{ width: 44%; }}
    .title-text {{
      font-size: 14px;
      font-weight: 500;
      color: #1a1a2e;
      line-height: 1.5;
    }}
    .merged-badge {{
      display: inline-block;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      font-size: 10px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
      margin-right: 6px;
      vertical-align: middle;
      letter-spacing: 0.5px;
    }}

    /* 摘要列 */
    .col-digest {{ width: 32%; }}
    .digest {{
      font-size: 13px;
      color: #666;
      line-height: 1.5;
    }}
    .no-digest {{ color: #bbb; font-style: italic; }}

    /* 来源列 */
    .col-sources {{ width: 16%; }}
    .source-badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 500;
      text-decoration: none;
      border: 1px solid;
      margin: 2px 2px 2px 0;
      transition: opacity 0.15s;
      white-space: nowrap;
    }}
    .source-badge:hover {{ opacity: 0.7; }}

    /* 时间列 */
    .col-time {{ width: 8%; white-space: nowrap; }}
    .col-time {{ font-size: 13px; color: #aaa; text-align: right; }}

    /* 底部 */
    .footer {{
      text-align: center;
      padding: 16px;
      font-size: 12px;
      color: #bbb;
      border-top: 1px solid #f0f2f5;
    }}

    @media (max-width: 768px) {{
      .container {{ margin: 10px; border-radius: 8px; }}
      .header {{ padding: 20px; }}
      .header h1 {{ font-size: 20px; }}
      .table-wrap {{ padding: 0 16px 20px; }}
      .col-digest {{ display: none; }}
      .col-time {{ display: none; }}
      .col-title {{ width: 60%; }}
      .col-sources {{ width: 40%; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📱 微信公众号文章汇总</h1>
      <div class="meta">获取时间：{generated_at} &nbsp;|&nbsp; 共 {total_articles} 条资讯 &nbsp;|&nbsp; {bundle_date}</div>
    </div>

    <div class="topics-bar">
      <span class="topics-label">🔥 热点</span>
      {topics_html}
    </div>

    <div class="sources-bar">
      <span class="topics-label">📰 来源</span>
      {sources_filter_html}
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>标题</th>
            <th>摘要</th>
            <th>来源</th>
            <th style="text-align:right">时间</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>

    <div class="footer">由 Claude 自动生成 · {generated_at}</div>
  </div>

  <script>
    const topicBtns  = document.querySelectorAll('.topic-tag');
    const sourceBtns = document.querySelectorAll('.source-filter');
    const rows = document.querySelectorAll('.article-row');

    let activeTag    = null;
    let activeSource = null;

    function applyFilter() {{
      rows.forEach(r => {{
        const rowTags    = r.dataset.tags    || '';
        const rowSources = r.dataset.sources || '';
        const tagOk    = !activeTag    || rowTags.includes(activeTag);
        const sourceOk = !activeSource || rowSources.split('|').includes(activeSource);
        r.style.display = (tagOk && sourceOk) ? '' : 'none';
      }});
    }}

    topicBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        const name = btn.dataset.tag;
        activeTag = (activeTag === name) ? null : name;
        topicBtns.forEach(b => {{
          b.classList.toggle('active',  b.dataset.tag === activeTag && activeTag !== null);
          b.classList.toggle('dimmed',  activeTag !== null && b.dataset.tag !== activeTag);
        }});
        applyFilter();
      }});
    }});

    sourceBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        const name = btn.dataset.source;
        activeSource = (activeSource === name) ? null : name;
        sourceBtns.forEach(b => {{
          b.classList.toggle('active',  b.dataset.source === activeSource && activeSource !== null);
          b.classList.toggle('dimmed',  activeSource !== null && b.dataset.source !== activeSource);
        }});
        applyFilter();
      }});
    }});
  </script>
</body>
</html>"""
    return html
