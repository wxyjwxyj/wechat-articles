from datetime import datetime, timezone
import hashlib
import json
import re


def _clean_text(text: str) -> str:
    """去除 HTML 标签，折叠多余空白。"""
    text = re.sub(r"<[^>]+>", "", text)          # 去 HTML 标签
    text = re.sub(r"[\r\n]+", " ", text)          # 换行转空格
    text = re.sub(r"\s{2,}", " ", text)           # 折叠多余空格
    return text.strip()


def normalize_wechat_article(source: dict, raw_article: dict) -> dict:
    time_str = raw_article.get("time")
    published_at = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") if time_str else datetime.now()
    
    source_name = source.get("name", "")
    title = raw_article.get("title", "")
    link = raw_article.get("link", "")
    
    content_hash = hashlib.sha256(
        f'{source_name}|{title}|{link}'.encode("utf-8")
    ).hexdigest()

    raw_summary = raw_article.get("digest", "")
    summary = _clean_text(raw_summary)

    return {
        "source_id": source.get("id"),
        "source_type": source.get("type", "wechat"),
        "title": title,
        "url": link,
        "author": source_name,
        "published_at": published_at.isoformat(),
        "raw_content": json.dumps(raw_article, ensure_ascii=False),
        "summary": summary,
        "cover": raw_article.get("cover", ""),
        "tags": [],
        "language": "zh",
        "content_hash": content_hash,
        "status": "raw",
    }


def normalize_hackernews_story(source: dict, raw_story: dict) -> dict:
    """将 HN collector 返回的 story 转换为 ItemPayload 格式。

    raw_story 字段（来自 HackerNewsCollector.fetch_top_ai_stories）:
        id, title, url, score, comments, time, hn_url, by
    """
    title = raw_story.get("title", "")
    url = raw_story.get("url", "")
    hn_url = raw_story.get("hn_url", "")

    content_hash = hashlib.sha256(
        f'hackernews|{title}|{url}'.encode("utf-8")
    ).hexdigest()

    # 拼接摘要：HN 帖子没有正文摘要，用 score + 评论数作为描述
    score = raw_story.get("score", 0)
    comments = raw_story.get("comments", 0)
    summary = f"HN {score} points · {comments} comments · {hn_url}"

    # 解析发布时间
    time_str = raw_story.get("time", "")
    try:
        published_at = datetime.fromisoformat(time_str)
    except (ValueError, TypeError):
        published_at = datetime.now()

    return {
        "source_id": source.get("id"),
        "source_type": "hackernews",
        "title": title,
        "url": url,
        "author": raw_story.get("by", ""),
        "published_at": published_at.isoformat(),
        "raw_content": json.dumps(raw_story, ensure_ascii=False),
        "summary": summary,
        "cover": "",
        "tags": [],
        "language": "en",
        "content_hash": content_hash,
        "status": "raw",
    }


def normalize_arxiv_paper(source: dict, raw_paper: dict) -> dict:
    """将 ArxivCollector 返回的论文字典转换为 ItemPayload 格式。

    raw_paper 字段（来自 ArxivCollector.fetch_recent_papers）：
        arxiv_id, title, summary, url, pdf_url, published,
        authors, categories, primary_category, comment, score
    """
    title = raw_paper.get("title", "")
    url = raw_paper.get("url", "")
    arxiv_id = raw_paper.get("arxiv_id", "")

    content_hash = hashlib.sha256(
        f'arxiv|{arxiv_id}|{title}'.encode("utf-8")
    ).hexdigest()

    # 摘要：取前 200 字符，避免过长
    summary_raw = raw_paper.get("summary", "")
    summary = _clean_text(summary_raw)
    if len(summary) > 200:
        summary = summary[:197] + "..."

    # 作者列表：取前 3 个，多的用 et al.
    authors = raw_paper.get("authors", [])
    if len(authors) > 3:
        author_str = ", ".join(authors[:3]) + " et al."
    else:
        author_str = ", ".join(authors) if authors else ""

    # 解析发布时间
    published_str = raw_paper.get("published", "")
    try:
        published_at = datetime.fromisoformat(
            published_str.replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        published_at = datetime.now(timezone.utc)

    # 分类标签
    categories = raw_paper.get("categories", [])
    tags = [cat for cat in categories if cat.startswith(("cs.", "stat."))]

    return {
        "source_id": source.get("id"),
        "source_type": "arxiv",
        "title": title,
        "url": url,
        "author": author_str,
        "published_at": published_at.isoformat(),
        "raw_content": json.dumps(raw_paper, ensure_ascii=False),
        "summary": summary,
        "cover": "",
        "tags": tags,
        "language": "en",
        "content_hash": content_hash,
        "status": "raw",
    }