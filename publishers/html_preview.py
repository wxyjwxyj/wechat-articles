"""根据 bundle 数据生成 HTML 预览页。"""
import html as _html
from collections import OrderedDict
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
        if not s.get("url") or not s.get("source_name"):
            continue
        color = _source_color(s["source_name"])
        parts.append(
            f"<a href='{_html.escape(s['url'])}' target='_blank' class='source-badge' "
            f"style='background:{color}22;color:{color};border-color:{color}44'>"
            f"{_html.escape(s['source_name'])}</a>"
        )
    return "".join(parts)


def render_bundle_html(bundle: dict) -> str:
    # 清空颜色缓存，保证每次生成颜色分配一致
    _source_color_cache.clear()

    items_flat = bundle.get("items_flat", [])
    total_articles = len(items_flat)
    # 原始文章总数（去重聚合前）= 所有 sources_list 的长度之和
    total_raw = sum(len(item.get("sources_list", [item])) for item in items_flat)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bundle_date = bundle.get("bundle_date", "")

    # 话题标签：按分类分组
    _CAT_LABELS = {
        "AI公司":   "🏢 AI公司",
        "AI技术":   "⚙️ AI技术",
        "行业应用": "🌐 行业应用",
        "宽泛":     "🔖 其他",
    }
    # 每个分类的主题色（与来源筛选保持同款轻量 chip 风格）
    _CAT_COLORS = {
        "AI公司":   "#3b82f6",
        "AI技术":   "#8b5cf6",
        "行业应用": "#f59e0b",
        "宽泛":     "#6b7280",
    }
    # 只展示这4行，学术/编程工具并入其他
    _CAT_ORDER = ["AI公司", "AI技术", "行业应用", "宽泛"]
    _MERGE_TO_OTHER = {"学术", "编程工具"}

    # 按分类归组，学术/编程工具 remap 到 宽泛
    cat_groups: dict[str, list] = OrderedDict((c, []) for c in _CAT_ORDER)
    for topic in bundle.get("topics", []):
        cat = topic.get("category", "宽泛")
        if cat in _MERGE_TO_OTHER:
            cat = "宽泛"
        if cat not in cat_groups:
            cat_groups[cat] = []
        cat_groups[cat].append(topic)

    topics_html = ""
    first_group = True
    for cat in _CAT_ORDER:
        group = cat_groups.get(cat, [])
        if not group:
            continue
        label = _CAT_LABELS.get(cat, cat)
        color = _CAT_COLORS.get(cat, "#6b7280")
        tags_html = ""
        for topic in sorted(group, key=lambda x: x.get("count", 0), reverse=True):
            tn = _html.escape(topic['name'])
            tags_html += (
                f"<span class='topic-tag' data-tag='{tn}' "
                f"style='background:{color}22;color:{color};border-color:{color}66'>"
                f"{tn} <em>{topic['count']}</em></span>"
            )
        # 第一行默认显示，后续行加 collapsible-group 类默认隐藏
        extra_class = "" if first_group else " collapsible-group"
        topics_html += f"<div class='topic-group{extra_class}'><span class='topic-cat-label'>{label}</span>{tags_html}</div>\n"
        first_group = False

    # 收集所有来源（去重，保持顺序），按 source_type 分两组
    # 公众号固定顺序，没有内容的置灰排末尾
    _WECHAT_ORDER = ["量子位", "AI寒武纪", "机器之心", "数字生命卡兹克", "APPSO", "36氪", "虎嗅APP", "新智元", "硅星人Pro"]
    _OVERSEAS_ORDER = ["Hacker News", "ArXiv", "GitHub Trending", "TechCrunch AI", "MIT Technology Review", "The Verge AI"]
    wechat_sources: list[str] = []
    wechat_inactive: list[str] = []
    other_sources: list[str] = []
    seen_sources: set[str] = set()
    # 用单来源条目建立准确的 source_name → source_type 映射
    name_to_type: dict[str, str] = {}
    for item in items_flat:
        for s in item.get("sources_list", []):
            name = s.get("source_name", "")
            # 优先用 sources_list 里自带的 source_type，没有则用主条目的
            stype = s.get("source_type") or item.get("source_type", "")
            if name and name not in name_to_type:
                name_to_type[name] = stype
    for item in items_flat:
        for s in item.get("sources_list", [{"source_name": item.get("source_name", "")}]):
            name = s.get("source_name", "")
            if not name or name in seen_sources:
                continue
            seen_sources.add(name)
            if name_to_type.get(name) == "wechat":
                wechat_sources.append(name)
            else:
                other_sources.append(name)
    # 按固定顺序排列公众号，未出现的置灰追加末尾
    wechat_inactive = [n for n in _WECHAT_ORDER if n not in wechat_sources]
    wechat_sources = [n for n in _WECHAT_ORDER if n in wechat_sources] + \
                     [n for n in wechat_sources if n not in _WECHAT_ORDER]
    # 按固定顺序排列海外源，未出现的置灰追加末尾
    other_inactive = [n for n in _OVERSEAS_ORDER if n not in other_sources]
    other_sources = [n for n in _OVERSEAS_ORDER if n in other_sources] + \
                    [n for n in other_sources if n not in _OVERSEAS_ORDER]

    def _filter_chips(names: list[str], inactive: set[str] | None = None) -> str:
        html = ""
        for name in names:
            color = _source_color(name)
            if inactive and name in inactive:
                html += (
                    f"<span class='source-filter inactive' data-source='{name}' "
                    f"style='color:#ccc;border-color:#e5e7eb;background:#fafafa;cursor:default'>"
                    f"{name}</span>\n"
                )
            else:
                html += (
                    f"<span class='source-filter' data-source='{name}' "
                    f"style='background:{color}22;color:{color};border-color:{color}66'>"
                    f"{name}</span>\n"
                )
        return html

    # 两行：公众号一行，海外/RSS源一行
    sources_filter_html = (
        f"<div class='source-row'>"
        f"<span class='source-row-label'>公众号</span>"
        f"{_filter_chips(wechat_sources + wechat_inactive, inactive=set(wechat_inactive))}</div>\n"
        f"<div class='source-row'>"
        f"<span class='source-row-label'>海外源</span>"
        f"{_filter_chips(other_sources + other_inactive, inactive=set(other_inactive))}</div>\n"
    )

    # 文章行
    rows_html = ""
    for item in items_flat:
        sources_list = item.get("sources_list", [{
            "source_name": item.get("source_name", ""),
            "url": item.get("url", ""),
        }])
        badges = _source_badges_html(sources_list)
        title_display = item.get("title_zh") or item["title"]
        summary = item.get("summary_zh") or item.get("summary", "")
        # 截断过长的 summary（超过 120 字折叠显示）
        summary_short = summary[:120] + "…" if len(summary) > 120 else summary
        summary_html = f"<div class='digest'>{summary_short}</div>" if summary_short else "<div class='digest no-digest'>暂无摘要</div>"

        # 时间：只显示 HH:MM
        pub = item.get("published_at", "")
        time_str = pub[11:16] if len(pub) >= 16 else ""

        # 重要性分数
        score = item.get("score", None)
        score_badge = f"<span class='score-badge'>{score}</span>" if score is not None else ""

        # 多来源时加聚合标记
        merged = len(sources_list) > 1
        merged_badge = "<span class='merged-badge'>多家</span>" if merged else ""

        # data-tags / data-sources 供 JS 过滤使用
        tags_attr = _html.escape(" ".join(item.get("tags", [])))
        sources_attr = _html.escape("|".join(s.get("source_name", "") for s in sources_list))
        title_display = _html.escape(title_display)
        rows_html += f"""<tr class='article-row{"" if not merged else " merged"}' data-tags='{tags_attr}' data-sources='{sources_attr}'>
  <td class='col-title'>
    {merged_badge}{score_badge}
    <span class='title-text'>{title_display}</span>
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
      background: #fff;
      padding: 10px 32px;
      border-bottom: 1px solid #eaecf0;
    }}
    .topic-group {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 5px;
      padding: 4px 0;
    }}
    .topic-group + .topic-group {{
      border-top: 1px solid #f3f4f6;
    }}
    .topic-cat-label {{
      font-size: 11px;
      color: #bbb;
      font-weight: 600;
      letter-spacing: 0.3px;
      white-space: nowrap;
      min-width: 44px;
      flex-shrink: 0;
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
      background: #f3f4f6;
      color: #555;
      border: 1px solid #e5e7eb;
      padding: 2px 9px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 400;
      cursor: pointer;
      user-select: none;
      transition: background 0.12s, color 0.12s, border-color 0.12s, transform 0.1s;
    }}
    .topic-tag em {{
      font-style: normal;
      font-size: 10px;
      color: #aaa;
    }}
    .topic-tag:hover {{
      background: #e9eaf0;
      color: #333;
      transform: translateY(-1px);
    }}
    .topic-tag.active {{
      box-shadow: 0 0 0 2px currentColor;
      font-weight: 500;
      opacity: 1;
    }}
    .topic-tag.dimmed {{ opacity: 0.35; }}

    /* 来源筛选栏 */
    .sources-bar {{
      background: #fff;
      padding: 10px 32px;
      border-bottom: 1px solid #eaecf0;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .source-row {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .source-row-label {{
      font-size: 11px;
      color: #aaa;
      font-weight: 600;
      letter-spacing: 0.3px;
      white-space: nowrap;
      min-width: 44px;
      flex-shrink: 0;
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
    .score-badge {{
      display: inline-block;
      background: #f0f0f0;
      color: #888;
      font-size: 10px;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 4px;
      margin-right: 6px;
      vertical-align: middle;
      font-variant-numeric: tabular-nums;
    }}
    tr.article-row:has(.score-badge) .score-badge {{
      background: #fff3e0;
      color: #e67e22;
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

    /* 话题栏折叠 */
    .topics-bar {{
      overflow: visible;
    }}
    .collapsible-group {{
      display: none;
    }}
    .topics-bar.expanded .collapsible-group {{
      display: flex;
    }}
    .topics-toggle {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      padding: 4px 32px;
      font-size: 11px;
      color: #bbb;
      cursor: pointer;
      user-select: none;
      border-bottom: 1px solid #eaecf0;
      background: #fff;
      transition: color 0.15s;
    }}
    .topics-toggle:hover {{ color: #667eea; }}

    /* ── 手机适配 ── */
    @media (max-width: 768px) {{
      .container {{ margin: 0; border-radius: 0; box-shadow: none; }}
      .header {{ padding: 16px 16px 14px; }}
      .header h1 {{ font-size: 18px; }}
      .header .meta {{ font-size: 11px; }}

      /* 标签栏手机端 */
      .topics-bar {{
        padding: 8px 16px;
      }}
      .topics-bar.expanded .collapsible-group {{
        display: flex;
      }}
      .topics-toggle {{
        display: block !important;
        text-align: center;
        padding: 6px 0;
        font-size: 11px;
        color: #999;
        cursor: pointer;
        user-select: none;
        background: #f8f9fb;
        border-bottom: 1px solid #eaecf0;
      }}
      .topics-toggle:active {{ color: #667eea; }}
      .topic-group {{
        gap: 4px;
        padding: 3px 0;
      }}
      .topic-cat-label {{
        font-size: 10px;
        min-width: 40px;
      }}
      .topic-tag {{
        font-size: 11px;
        padding: 2px 7px;
      }}

      /* 来源筛选栏 */
      .sources-bar {{
        padding: 8px 16px;
        gap: 4px;
      }}

      /* 表格 → 卡片布局 */
      .table-wrap {{ padding: 0; }}
      table {{ display: block; width: 100%; }}
      thead {{ display: none; }}
      tbody {{ display: block; }}
      tr.article-row {{
        display: block;
        padding: 12px 16px;
        border-bottom: 1px solid #f0f2f5;
      }}
      tr.article-row:hover td {{ background: transparent; }}
      td {{
        display: block;
        padding: 0;
        border: none;
      }}
      .col-title {{
        width: 100%;
        margin-bottom: 6px;
      }}
      .title-text {{
        font-size: 15px;
        line-height: 1.45;
      }}
      .col-digest {{
        display: block;
        width: 100%;
        margin-bottom: 6px;
      }}
      .digest {{
        font-size: 12px;
        color: #999;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }}
      .no-digest {{ display: none; }}
      .col-sources {{
        width: 100%;
        display: inline;
      }}
      .source-badge {{
        font-size: 11px;
        padding: 1px 6px;
        margin: 0 4px 0 0;
      }}
      .col-time {{
        display: inline;
        width: auto;
        font-size: 11px;
        color: #bbb;
        margin-left: 4px;
      }}
      .col-time::before {{
        content: '·';
        margin-right: 4px;
      }}
      .score-badge {{
        font-size: 9px;
        padding: 0 4px;
      }}
      .merged-badge {{
        font-size: 9px;
        padding: 0 4px;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📱 微信公众号文章汇总</h1>
      <div class="meta">获取时间：{generated_at} &nbsp;|&nbsp; 共采集 {total_raw} 篇，聚合为 {total_articles} 条资讯 &nbsp;|&nbsp; {bundle_date}</div>
    </div>

    <div class="topics-bar" id="topicsBar">
      {topics_html}
    </div>
    <div class="topics-toggle" id="topicsToggle" onclick="var bar=document.getElementById('topicsBar');bar.classList.toggle('expanded');this.textContent=bar.classList.contains('expanded')?'收起 ▲':'展开全部话题 ▼'">展开全部话题 ▼</div>

    <div class="sources-bar">
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
      if (btn.classList.contains('inactive')) return;
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
