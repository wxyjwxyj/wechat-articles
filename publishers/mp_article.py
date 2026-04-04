"""根据 bundle 数据生成微信公众号发布稿 payload（导读风）。"""
import json
import re


def _clean_summary(text: str) -> str:
    """去掉微信原始 ##hashtag## 标签，清理多余空白。"""
    text = re.sub(r"##[^#]+##", "", text)
    return text.strip()


def _select_highlights(items_flat: list[dict], min_score: int = 6, max_count: int = 8) -> list[dict]:
    """
    从 items_flat（已按 score 降序）中精选亮点文章。
    优先取 score >= min_score 的，不足时往下补，最多 max_count 条。
    """
    high = [item for item in items_flat if item.get("score", 5) >= min_score]
    if len(high) >= 3:
        return high[:max_count]
    # 不足3条时直接取前 max_count 条
    return items_flat[:max_count]


def _build_highlight_html(highlights: list[dict]) -> str:
    """将精选条目渲染为公众号 HTML，无点评版本（纯本地）。"""
    parts = []
    for item in highlights:
        sources_list = item.get("sources_list", [])
        if len(sources_list) == 1:
            link_html = f"<a href='{sources_list[0]['url']}'>查看原文 →</a>"
        else:
            links = " | ".join(
                f"<a href='{s['url']}'>{s['source_name']}</a>"
                for s in sources_list if s.get("url")
            )
            link_html = f"多家报道：{links}"

        summary = _clean_summary(item.get("summary", ""))
        summary_html = f"<p>{summary}</p>" if summary else ""

        score = item.get("score")
        score_tag = f"<small style='color:#e67e22;font-weight:bold'>[{score}分]</small> " if score is not None else ""

        parts.append(
            f"<h3>{score_tag}{item['title']}</h3>\n"
            f"{summary_html}"
            f"<p>{link_html}</p>"
        )
    return "\n".join(parts)


def build_mp_article_payload(
    bundle: dict,
    api_key: str = "",
    base_url: str = "https://api.anthropic.com",
) -> dict:
    """
    生成公众号发布稿（导读风格）。
    若提供 api_key，调用 Claude 生成每条的点评；否则仅输出标题+摘要。
    返回 dict：title、body_html、commentary（列表）、status、bundle_date。
    """
    items_flat = bundle.get("items_flat", [])
    highlights = _select_highlights(items_flat)
    bundle_date = bundle.get("bundle_date", "")
    bundle_title = bundle.get("title", f"AI 日报 · {bundle_date}")

    # 尝试用 Claude 生成点评
    commentary_list = _generate_commentary(highlights, api_key, base_url)

    # 渲染 HTML
    body_html = _render_html(bundle_title, bundle_date, highlights, commentary_list)

    return {
        "title": bundle_title,
        "body_html": body_html,
        "commentary": commentary_list,
        "status": "draft",
        "bundle_date": bundle_date,
    }


def _generate_commentary(
    highlights: list[dict],
    api_key: str,
    base_url: str,
) -> list[str]:
    """
    调用 Claude 为每篇精选文章生成一句20-30字的编辑点评。
    失败时返回空列表（调用方降级到无点评模式）。
    """
    if not api_key:
        return []

    articles_text = "\n".join(
        f"{i+1}. 【{item.get('score','?')}分】{item['title']}"
        f"  摘要：{_clean_summary(item.get('summary',''))[:80]}"
        for i, item in enumerate(highlights)
    )

    prompt = f"""你是一位科技资讯编辑，正在为 AI 日报撰写导读点评。

以下是今日精选的 {len(highlights)} 条重要资讯，请为每条写一句简短的编辑点评：
- 字数：20-35字
- 风格：犀利、有观点，像老编辑写的小评语，而非官方介绍
- 不要重复标题的内容，要有增量信息或洞见
- 可以表达态度（重要、值得关注、有意思等）

文章列表：
{articles_text}

严格按 JSON 格式返回，不要有任何其他文字：
{{"comments": ["第1条点评", "第2条点评", ...]}}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        if not message.content:
            print("  ⚠ Claude 返回空内容（代理限制？），跳过点评生成")
            return []
        raw = message.content[0].text.strip()
    except ImportError:
        print("  ⚠ 未安装 anthropic 库，跳过点评生成")
        return []
    except Exception as e:
        print(f"  ⚠ Claude 点评生成失败（{e}），跳过")
        return []

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        comments = data.get("comments", [])
        # 补齐或截断到 highlights 长度
        while len(comments) < len(highlights):
            comments.append("")
        return comments[:len(highlights)]
    except Exception as e:
        print(f"  ⚠ 点评解析失败（{e}），跳过")
        return []


def _render_html(
    title: str,
    bundle_date: str,
    highlights: list[dict],
    commentary_list: list[str],
) -> str:
    """渲染公众号正文 HTML（适配微信编辑器，纯内联样式）。

    设计风格：精致编辑部 — 深色线条分隔、浅灰卡片点评、红色编号徽章。
    不使用 h1（公众号自带标题栏）、不使用 class/flex/grid/渐变/动画。
    """
    has_commentary = bool(commentary_list and any(commentary_list))

    # ── 头部引导语 ──
    header_html = (
        '<section style="margin:0 0 8px;padding:0;">'
        '<section style="text-align:center;padding:16px 0 12px;">'
        '<p style="font-size:13px;color:#888;letter-spacing:2px;margin:0;">DAILY AI BRIEFING</p>'
        '</section>'
        '<section style="border-top:2px solid #222;border-bottom:1px solid #e5e5e5;padding:10px 0;margin:0 0 6px;">'
        f'<p style="font-size:13px;color:#999;letter-spacing:1px;margin:0;text-align:center;">'
        f'{bundle_date} · 精选 <strong style="color:#c0392b;">{len(highlights)}</strong> 条 · 编辑点评版</p>'
        '</section>'
        '</section>'
    )

    # ── 内容卡片 ──
    items_parts = []
    for i, item in enumerate(highlights):
        num = str(i + 1).zfill(2)
        sources_list = item.get("sources_list", [])

        # 来源名称
        source_names = " · ".join(
            s.get("source_name", "") for s in sources_list if s.get("source_name")
        ) or item.get("source_name", "")

        # 多家报道标签
        merged_tag = ""
        if len(sources_list) > 1:
            merged_tag = (
                '<span style="display:inline-block;font-size:10px;color:#c0392b;'
                'border:1px solid #e8c8c8;border-radius:2px;padding:0 4px;'
                'margin-left:6px;vertical-align:middle;line-height:16px;">多家报道</span>'
            )

        # 链接
        if len(sources_list) == 1 and sources_list[0].get("url"):
            link_html = (
                f'<p style="margin:0;"><a style="font-size:12px;color:#576b95;'
                f'text-decoration:none;letter-spacing:0.5px;" '
                f'href=\'{sources_list[0]["url"]}\'>阅读原文 →</a></p>'
            )
        elif len(sources_list) > 1:
            links = " ｜ ".join(
                f'<a style="color:#576b95;text-decoration:none;" '
                f'href=\'{s["url"]}\'>{s["source_name"]}</a>'
                for s in sources_list if s.get("url")
            )
            link_html = f'<p style="margin:0;font-size:12px;color:#999;">{links}</p>'
        else:
            link_html = ""

        # 摘要
        summary = _clean_summary(item.get("summary", ""))
        summary_short = summary[:100] + "…" if len(summary) > 100 else summary
        summary_html = (
            f'<p style="font-size:14px;color:#888;line-height:1.7;margin:0 0 8px;">'
            f'{summary_short}</p>'
            if summary_short else ""
        )

        # 编辑点评
        comment = commentary_list[i] if has_commentary and i < len(commentary_list) else ""
        comment_html = ""
        if comment:
            comment_html = (
                '<section style="background:#f7f7f7;border-radius:6px;padding:10px 14px;margin:0 0 10px;">'
                '<p style="font-size:13px;color:#666;line-height:1.75;margin:0;">'
                '<span style="color:#c0392b;font-weight:bold;margin-right:4px;">编辑观点</span>'
                f'{comment}</p>'
                '</section>'
            )

        items_parts.append(
            f'<section style="margin:22px 0 0;padding:0 0 20px;border-bottom:1px solid #f0f0f0;">'
            # 编号 + 来源
            f'<section style="margin:0 0 10px;">'
            f'<span style="display:inline-block;background:#c0392b;color:#fff;font-size:11px;'
            f'font-weight:bold;min-width:20px;height:20px;line-height:20px;text-align:center;'
            f'border-radius:3px;margin-right:8px;vertical-align:middle;letter-spacing:0;'
            f'padding:0 4px;white-space:nowrap;">{num}</span>'
            f'<span style="font-size:12px;color:#999;letter-spacing:1px;vertical-align:middle;">'
            f'{source_names}</span>'
            f'{merged_tag}'
            f'</section>'
            # 标题
            f'<p style="font-size:17px;font-weight:bold;color:#1a1a1a;line-height:1.6;'
            f'margin:0 0 10px;letter-spacing:0.5px;">{item["title"]}</p>'
            # 点评
            f'{comment_html}'
            # 摘要
            f'{summary_html}'
            # 链接
            f'{link_html}'
            f'</section>'
        )

    items_html = "\n".join(items_parts)

    # ── 尾部 ──
    footer_html = (
        '<section style="text-align:center;margin:28px 0 16px;">'
        '<section style="border-top:2px solid #222;width:40px;margin:0 auto 14px;"></section>'
        '<p style="font-size:11px;color:#bbb;letter-spacing:3px;margin:0;">AI DAILY BRIEFING</p>'
        '<p style="font-size:11px;color:#ccc;letter-spacing:1px;margin:6px 0 0;">'
        '自动采集 · Claude 编辑点评 · 每日更新</p>'
        '</section>'
    )

    return f"{header_html}\n{items_html}\n{footer_html}"
