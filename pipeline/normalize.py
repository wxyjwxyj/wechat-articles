from datetime import datetime
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
