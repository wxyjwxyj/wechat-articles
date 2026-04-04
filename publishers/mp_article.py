"""根据 bundle 数据生成微信公众号发布稿 payload。"""


def build_mp_article_payload(bundle: dict) -> dict:
    """
    生成公众号发布稿所需的结构化 payload。
    返回 dict 包含：title、body_html、status、bundle_date。
    body_html 包含导语、热门主题块、按聚合后的 items_flat 列出的内容块。
    """
    topic_html = "".join(
        f"<li>{topic['name']}（{topic['count']}篇）</li>"
        for topic in bundle.get("topics", [])
    )

    items_html = ""
    for item in bundle.get("items_flat", []):
        sources_list = item.get("sources_list", [])
        # 每个来源生成独立链接
        if len(sources_list) == 1:
            link_html = f"<a href='{sources_list[0]['url']}'>查看原文 →</a>"
        else:
            links = " | ".join(
                f"<a href='{s['url']}'>{s['source_name']}</a>"
                for s in sources_list if s.get("url")
            )
            link_html = f"多家报道：{links}"

        summary = item.get("summary", "")
        summary_html = f"{summary}<br>" if summary else ""

        items_html += (
            f"<p><strong>{item['title']}</strong><br>"
            f"{summary_html}"
            f"{link_html}</p>\n"
        )

    body_html = f"""<h1>{bundle['title']}</h1>
<p>{bundle['intro']}</p>
<h2>热门主题</h2>
<ul>{topic_html}</ul>
<h2>今日内容</h2>
{items_html}
<p>更多内容可在小程序中查看。</p>"""

    return {
        "title": bundle["title"],
        "body_html": body_html,
        "status": "draft",
        "bundle_date": bundle["bundle_date"],
    }
