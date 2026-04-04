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
    """渲染完整公众号 HTML。"""
    has_commentary = bool(commentary_list and any(commentary_list))

    # 导语
    intro_html = (
        f"<p>今日精选 {len(highlights)} 条 AI 资讯，快速掌握行业动态。</p>"
    )

    # 内容块
    items_parts = []
    for i, item in enumerate(highlights):
        sources_list = item.get("sources_list", [])
        if len(sources_list) == 1 and sources_list[0].get("url"):
            link_html = f"<a href='{sources_list[0]['url']}'>查看原文 →</a>"
        elif sources_list:
            links = " | ".join(
                f"<a href='{s['url']}'>{s['source_name']}</a>"
                for s in sources_list if s.get("url")
            )
            link_html = f"多家报道：{links}" if links else ""
        else:
            link_html = ""

        summary = _clean_summary(item.get("summary", ""))
        # 摘要截断：超过100字折叠
        summary_short = summary[:100] + "…" if len(summary) > 100 else summary

        # 点评块（有点评时显示）
        comment = commentary_list[i] if has_commentary and i < len(commentary_list) else ""
        comment_html = (
            f"<p style='background:#fffbe6;border-left:3px solid #f0a500;"
            f"padding:6px 10px;margin:8px 0;color:#555;font-size:14px;'>"
            f"💬 {comment}</p>\n"
            if comment else ""
        )

        # 来源徽章
        source_names = " · ".join(
            s.get("source_name", "") for s in sources_list if s.get("source_name")
        ) or item.get("source_name", "")

        summary_html = f"<p style='color:#666;font-size:14px'>{summary_short}</p>" if summary_short else ""

        items_parts.append(
            f"<h3 style='margin-top:24px'>{item['title']}</h3>\n"
            f"{comment_html}"
            f"{summary_html}\n"
            f"<p style='font-size:13px;color:#999'>📰 {source_names} &nbsp; {link_html}</p>"
        )

    items_html = "\n".join(items_parts)

    # 结尾
    outro_html = "<p style='color:#999;font-size:13px;text-align:center'>— 以上为今日导读，完整列表见 HTML 预览页 —</p>"

    return (
        f"<h1>{title}</h1>\n"
        f"{intro_html}\n"
        f"<hr>\n"
        f"{items_html}\n"
        f"<hr>\n"
        f"{outro_html}"
    )
