from datetime import datetime
import hashlib
import json


def normalize_wechat_article(source: dict, raw_article: dict) -> dict:
    time_str = raw_article.get("time")
    published_at = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") if time_str else datetime.now()
    
    source_name = source.get("name", "")
    title = raw_article.get("title", "")
    link = raw_article.get("link", "")
    
    content_hash = hashlib.sha256(
        f'{source_name}|{title}|{link}'.encode("utf-8")
    ).hexdigest()

    return {
        "source_id": source.get("id"),
        "source_type": source.get("type", "wechat"),
        "title": title,
        "url": link,
        "author": source_name,
        "published_at": published_at.isoformat(),
        "raw_content": json.dumps(raw_article, ensure_ascii=False),
        "summary": raw_article.get("digest", ""),
        "cover": raw_article.get("cover", ""),
        "tags": [],
        "language": "zh",
        "content_hash": content_hash,
        "status": "raw",
    }
