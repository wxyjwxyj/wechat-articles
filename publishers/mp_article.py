"""根据 bundle 数据生成微信公众号发布稿 payload。"""


def build_mp_article_payload(bundle: dict) -> dict:
    """
    生成公众号发布稿所需的结构化 payload。
    返回 dict 包含：title、body_html、status、bundle_date。
    body_html 包含导语、热门主题块、按来源分组的内容块。
    """
    topic_html = "".join(
        f"<li>{topic['name']}（{topic['count']}篇）</li>"
        for topic in bundle.get("topics", [])
    )

    source_html = ""
    for source_name, articles in bundle.get("sources", {}).items():
        source_html += f"<h2>{source_name}</h2>\n"
        for article in articles:
            source_html += (
                f"<p><strong>{article['title']}</strong><br>"
                f"{article.get('summary', '')}"
                f"<br><a href='{article['url']}'>查看原文 →</a></p>\n"
            )

    body_html = f"""<h1>{bundle['title']}</h1>
<p>{bundle['intro']}</p>
<h2>热门主题</h2>
<ul>{topic_html}</ul>
<h2>今日内容</h2>
{source_html}
<p>更多内容可在小程序中查看。</p>"""

    return {
        "title": bundle["title"],
        "body_html": body_html,
        "status": "draft",
        "bundle_date": bundle["bundle_date"],
    }
