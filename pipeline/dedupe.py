def dedupe_items(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        key = item.get("url") or item.get("content_hash")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
