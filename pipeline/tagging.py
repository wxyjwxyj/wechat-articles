# pipeline/tagging.py

# 关键词匹配规则：(标签名, 触发关键词列表)
PATTERNS = [
    ("Claude Code", ["Claude Code"]),
    ("Agent", ["Agent", "智能体"]),
    ("AI", ["AI", "人工智能"]),
    ("OpenAI", ["OpenAI"]),
    ("具身智能", ["具身智能"]),
]


def extract_tags(item: dict) -> list[str]:
    """从 title 和 summary 中提取标签，按 PATTERNS 顺序返回匹配的标签。"""
    text = f'{item.get("title", "")} {item.get("summary", "")}'
    tags = []
    for tag, keywords in PATTERNS:
        if any(keyword.lower() in text.lower() for keyword in keywords):
            tags.append(tag)
    return tags


def build_topics(items: list[dict]) -> list[dict]:
    """统计所有 item 的标签频次，返回按频次降序排列的 topic 列表。"""
    counts: dict[str, int] = {}
    for item in items:
        for tag in item.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return [
        {"name": name, "count": count, "keywords": [name]}
        for name, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]
