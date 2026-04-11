"""根据 bundle 数据生成微信公众号发布稿 payload（导读风）。"""
import json
import re

from utils.log import get_logger

logger = get_logger(__name__)


def _clean_summary(text: str) -> str:
    """去掉微信原始 ##hashtag## 标签，清理多余空白。"""
    text = re.sub(r"##[^#]+##", "", text)
    return text.strip()


def _select_highlights(items_flat: list[dict], min_score: int = 6, max_count: int = 6) -> list[dict]:
    """
    多样性选取：HN/GitHub 各保底1条（ArXiv 靠分数自然竞争），剩余按分数补齐，最多 max_count 条。
    """
    if not items_flat:
        return []

    # HN 和 GitHub Trending 各取分数最高的1条（ArXiv 不保底，靠分数竞争）
    guaranteed_types = {"hackernews", "github_trending"}
    seen_types: set[str] = set()
    guaranteed: list[dict] = []
    for item in sorted(items_flat, key=lambda x: x.get("score", 5), reverse=True):
        stype = item.get("source_type", "")
        if stype in guaranteed_types and stype not in seen_types:
            guaranteed.append(item)
            seen_types.add(stype)

    # 剩余名额从高分条目里按分数补齐
    guaranteed_urls = {i.get("url") for i in guaranteed}
    remaining = [
        item for item in items_flat
        if item.get("url") not in guaranteed_urls and item.get("score", 5) >= min_score
    ]

    # 合并后统一按分数降序排列（保底不强制排前面）
    candidates = guaranteed + remaining
    candidates.sort(key=lambda x: x.get("score", 5), reverse=True)
    highlights = candidates[:max_count]

    # 不足时降低阈值补齐
    if len(highlights) < 2:
        highlights = items_flat[:max_count]

    return highlights


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
    调用 Claude 为每篇精选文章生成一句编辑点评。
    优先用 Haiku（便宜快速），失败时降级到无点评模式。
    """
    if not api_key:
        return []

    articles_text = "\n".join(
        f"{i+1}. 【{item.get('score','?')}分】{item['title']}\n"
        f"   摘要：{_clean_summary(item.get('summary',''))[:120]}\n"
        f"   来源：{_get_source_name(item)}"
        for i, item in enumerate(highlights)
    )

    prompt = f"""你是「AI日报」的主编，每天为读者精选 AI 领域最值得关注的新闻并撰写点评。

你的点评风格：
- 像资深科技记者跟同行聊天，不是写新闻稿
- 有观点、有态度，敢说"这很重要"或"这没啥新意"
- 善用类比让技术变得好懂（比如"相当于给大模型装了后视镜"）
- 偶尔带点幽默，但不尬

要求：
- 每条点评 20-40 字
- 不要重复标题已有的信息
- 要补充标题没说的背景、影响、或你的判断
- 如果多条新闻有关联，可以在点评中串联

今日 {len(highlights)} 条精选：
{articles_text}

严格按 JSON 格式返回，不要有任何其他文字：
{{"comments": ["第1条点评", "第2条点评", ...]}}"""

    # 模型优先级：Haiku（快且便宜）→ Sonnet（兜底）
    models = ["claude-haiku-4-5-20251001", "claude-opus-4-6"]

    for model in models:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            if not message.content:
                logger.warning("%s 返回空内容，尝试下一个模型", model)
                continue
            raw = message.content[0].text.strip()
            logger.info("使用 %s 生成点评", model)
            break
        except ImportError:
            logger.warning("未安装 anthropic 库，跳过点评生成")
            return []
        except Exception as e:
            logger.warning("%s 调用失败（%s），尝试下一个模型", model, e)
            continue
    else:
        logger.warning("所有模型均失败，跳过点评生成")
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
        logger.warning("点评解析失败（%s），跳过", e)
        return []


def _get_source_name(item: dict) -> str:
    """从 item 中提取来源名称。"""
    sources_list = item.get("sources_list", [])
    if sources_list:
        return " · ".join(s.get("source_name", "") for s in sources_list if s.get("source_name"))
    return item.get("source_name", "未知来源")


def _render_html(
    title: str,
    bundle_date: str,
    highlights: list[dict],
    commentary_list: list[str],
) -> str:
    """渲染公众号正文 HTML（适配微信编辑器，纯内联样式）。

    设计风格：科技杂志编辑部 — 大号编号、蓝色点评边框、精致排版。
    不使用 h1（公众号自带标题栏）、不使用 class/flex/grid/渐变/动画。
    """
    has_commentary = bool(commentary_list and any(commentary_list))

    # 根据是否有点评动态调整描述
    edition_label = "编辑点评版" if has_commentary else "精选速览版"

    # ── 头部引导语 ──
    header_html = (
        '<section style="margin:0 0 4px;padding:0;">'
        '<section style="text-align:center;padding:20px 0 14px;">'
        '<p style="font-size:11px;color:#999;letter-spacing:4px;margin:0;">'
        'DAILY · AI · BRIEFING</p>'
        '</section>'
        # 居中粗线装饰
        '<section style="border-top:1px solid #e0e0e0;margin:0;">'
        '<section style="border-top:2px solid #1a1a1a;'
        'width:48px;margin:-1px auto 0;"></section>'
        '</section>'
        '<section style="padding:14px 0 16px;">'
        f'<p style="font-size:13px;color:#999;letter-spacing:0.5px;'
        f'margin:0;text-align:center;">'
        f'{bundle_date} · 精选 '
        f'<strong style="color:#1a1a1a;">{len(highlights)}</strong>'
        f' 条 · {edition_label}</p>'
        '</section>'
        '<section style="border-bottom:1px solid #e8e8e8;margin:0 0 6px;">'
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

        # 多源报道标签
        merged_tag = ""
        if len(sources_list) > 1:
            merged_tag = (
                '<span style="display:inline-block;font-size:10px;color:#e8713a;'
                'border:1px solid #f0d4c0;border-radius:2px;padding:0 5px;'
                'margin-left:6px;vertical-align:middle;line-height:16px;">'
                '综合报道</span>'
            )

        # 链接
        if len(sources_list) == 1 and sources_list[0].get("url"):
            link_html = (
                f'<p style="margin:0;">'
                f'<a style="font-size:12px;color:#576b95;'
                f'text-decoration:none;letter-spacing:0.3px;" '
                f"href='{sources_list[0]['url']}'>阅读原文 →</a></p>"
            )
        elif len(sources_list) > 1:
            link_parts = []
            for s in sources_list:
                if s.get("url"):
                    link_parts.append(
                        f'<a style="font-size:12px;color:#576b95;'
                        f"text-decoration:none;letter-spacing:0.3px;\" "
                        f"href='{s['url']}'>{s['source_name']}</a>"
                    )
            links = (
                '<span style="font-size:12px;color:#ddd;margin:0 6px;">｜</span>'
            ).join(link_parts)
            link_html = f'<p style="margin:0;">{links}</p>'
        else:
            link_html = ""

        # 摘要
        summary = _clean_summary(item.get("summary", ""))
        summary_short = summary[:100] + "…" if len(summary) > 100 else summary
        summary_html = (
            f'<p style="font-size:14px;color:#888;line-height:1.75;'
            f'margin:0 0 10px;">{summary_short}</p>'
            if summary_short else ""
        )

        # 编辑点评
        comment = (
            commentary_list[i]
            if has_commentary and i < len(commentary_list)
            else ""
        )
        comment_html = ""
        if comment:
            comment_html = (
                '<section style="border-left:3px solid #1e6fff;'
                'padding:8px 0 8px 14px;margin:0 0 12px;">'
                '<p style="font-size:13px;color:#555;line-height:1.8;margin:0;">'
                '<span style="font-size:11px;color:#1e6fff;font-weight:bold;'
                'letter-spacing:1px;margin-right:2px;">主编说</span>'
                f'{comment}</p>'
                '</section>'
            )

        items_parts.append(
            f'<section style="margin:24px 0 0;padding:0 0 22px;'
            f'border-bottom:1px solid #efefef;">'
            # 编号 + 短横线 + 来源
            f'<section style="margin:0 0 12px;">'
            f'<span style="display:inline-block;font-size:22px;font-weight:bold;'
            f'color:#1a1a1a;line-height:1;vertical-align:middle;'
            f'margin-right:10px;letter-spacing:-1px;">{num}</span>'
            f'<span style="display:inline-block;width:16px;border-top:1px solid #ccc;'
            f'vertical-align:middle;margin-right:10px;"></span>'
            f'<span style="font-size:12px;color:#999;letter-spacing:0.5px;'
            f'vertical-align:middle;">{source_names}</span>'
            f'{merged_tag}'
            f'</section>'
            # 标题
            f'<p style="font-size:17px;font-weight:bold;color:#1a1a1a;'
            f'line-height:1.65;margin:0 0 12px;letter-spacing:0.3px;">'
            f'{item["title"]}</p>'
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
        '<section style="text-align:center;margin:32px 0 20px;">'
        # 居中粗线装饰（与头部呼应）
        '<section style="border-top:1px solid #e0e0e0;margin:0;">'
        '<section style="border-top:2px solid #1a1a1a;'
        'width:48px;margin:-1px auto 0;"></section>'
        '</section>'
        '<p style="font-size:11px;color:#bbb;letter-spacing:3px;'
        'margin:16px 0 0;">AI DAILY BRIEFING</p>'
        '<p style="font-size:11px;color:#ccc;letter-spacing:0.5px;'
        'margin:6px 0 0;">自动采集 · Claude 编辑点评 · 每日更新</p>'
        '</section>'
        # ── AI 内容标注（合规要求） ──
        '<section style="margin:16px 0 0;padding:14px 0 0;'
        'border-top:1px solid #f0f0f0;">'
        '<p style="font-size:11px;color:#bbb;line-height:1.6;'
        'margin:0;text-align:center;">'
        '📌 本文由 AI 辅助采集和整理，经人工审核后发布</p>'
        '</section>'
    )

    return f"{header_html}\n{items_html}\n{footer_html}"
