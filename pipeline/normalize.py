from datetime import datetime
import hashlib
import json


def normalize_wechat_article(source: dict, raw_article: dict) -> dict:
    published_at = datetime.strptime(raw_article["time"], "%Y-%m-%d %H:%M:%S")
    content_hash = hashlib.sha256(
        f'{source["name"]}|{raw_article["title"]}|{raw_article["link"]}'.encode("utf-8")
    ).hexdigest()

    return {
        "source_id": source["id"],
        "source_type": source["type"],
        "title": raw_article["title"],
        "url": raw_article["link"],
        "author": source["name"],
        "published_at": published_at.isoformat(),
        "raw_content": json.dumps(raw_article, ensure_ascii=False),
        "summary": raw_article.get("digest", ""),
        "cover": raw_article.get("cover", ""),
        "tags": [],
        "language": "zh",
        "content_hash": content_hash,
        "status": "raw",
    }
