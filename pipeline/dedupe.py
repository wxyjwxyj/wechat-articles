import re

# 品牌/实体别名映射，合并后统一用规范词替换
_ALIASES: list[tuple[str, str]] = [
    ("claude", "anthropic"),
    ("openai", "gpt"),
    ("gemini", "google"),
]


def _tokenize(text: str) -> set[str]:
    """分词：CamelCase 拆分 + 中英文边界切割 + 按非字符切割，保留长度 >= 2 的词元。并应用别名归一化。"""
    # CamelCase 拆分：OpenClaw → Open Claw
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    # 中英文边界插入空格：封杀OpenClaw → 封杀 Open Claw
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])([\u4e00-\u9fff])", r"\1 \2", text)
    tokens = re.split(r"[^\u4e00-\u9fffA-Za-z0-9]+", text.lower())
    result = set()
    for t in tokens:
        if len(t) < 2:
            continue
        for alias, canonical in _ALIASES:
            if t == alias:
                t = canonical
                break
        result.add(t)
    return result


def _similar(a: set, b: set, threshold: float) -> bool:
    """
    两个词集相似性判断：
    1. Jaccard >= threshold，或
    2. 共享词数 >= 2（捕获专有名词重叠，如 openclaw + 龙虾）
    """
    if not a or not b:
        return False
    intersection = a & b
    jaccard_score = len(intersection) / len(a | b)
    return jaccard_score >= threshold or len(intersection) >= 2


def _merge_group(group: list[dict]) -> dict:
    """
    将一组相似文章合并为一条。
    - 保留摘要最长的那篇内容作为主体
    - sources_list 记录所有来源（去重，保持顺序）
    """
    # 选摘要最长的作为主体
    primary = max(group, key=lambda x: len(x.get("summary", "")))
    merged = dict(primary)

    # 收集所有来源（去重）
    seen_sources = set()
    sources_list = []
    for item in group:
        key = (item.get("source_name", ""), item.get("url", ""))
        if key not in seen_sources:
            seen_sources.add(key)
            sources_list.append({
                "source_name": item.get("source_name", ""),
                "url": item.get("url", ""),
            })

    merged["sources_list"] = sources_list
    # source_name 改为所有来源的联合展示
    merged["source_name"] = " / ".join(s["source_name"] for s in sources_list)
    return merged


def dedupe_items(items: list[dict], sim_threshold: float = 0.4) -> list[dict]:
    """
    两阶段去重：
    1. URL / content_hash 精确去重
    2. 标题 Jaccard 相似度 >= sim_threshold 的文章聚合为一条
    """
    # 第一阶段：精确去重
    seen_keys: set[str] = set()
    exact_deduped = []
    for item in items:
        key = item.get("url") or item.get("content_hash")
        if key is None:
            exact_deduped.append(item)
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        exact_deduped.append(item)

    # 第二阶段：标题相似度聚合
    # 给每个 item 预计算标题词集
    token_sets = [_tokenize(item.get("title", "")) for item in exact_deduped]

    # 并查集：合并相似 item
    parent = list(range(len(exact_deduped)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(len(exact_deduped)):
        for j in range(i + 1, len(exact_deduped)):
            if _similar(token_sets[i], token_sets[j], sim_threshold):
                union(i, j)

    # 按组收集
    groups: dict[int, list[dict]] = {}
    for i, item in enumerate(exact_deduped):
        root = find(i)
        groups.setdefault(root, []).append(item)

    # 按第一次出现顺序输出（保持原始顺序）
    order = []
    seen_roots = set()
    for i in range(len(exact_deduped)):
        root = find(i)
        if root not in seen_roots:
            seen_roots.add(root)
            order.append(root)

    result = []
    for root in order:
        group = groups[root]
        if len(group) == 1:
            # 单篇：补 sources_list 字段保持结构一致
            item = dict(group[0])
            item.setdefault("sources_list", [{
                "source_name": item.get("source_name", item.get("author", "")),
                "url": item.get("url", ""),
            }])
            result.append(item)
        else:
            result.append(_merge_group(group))

    return result
