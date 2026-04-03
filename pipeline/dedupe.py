def dedupe_items(items: list[dict]) -> list[dict]:
    """
    基于 url 或 content_hash 去重。
    优先使用 url 作为去重键；url 为空时降级到 content_hash。
    两者均缺失的 item 视为无法去重，直接保留（不参与去重逻辑）。
    """
    seen: set[str] = set()
    result = []
    for item in items:
        key = item.get("url") or item.get("content_hash")
        if key is None:
            # 没有去重键，直接保留
            result.append(item)
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
