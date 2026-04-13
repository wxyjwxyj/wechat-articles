import json
import re
import time

from utils.log import get_logger

logger = get_logger(__name__)

# 品牌/实体别名映射，合并后统一用规范词替换
_ALIASES: list[tuple[str, str]] = [
    ("claude", "anthropic"),
    ("openai", "gpt"),
    ("gemini", "google"),
]


def _tokenize(text: str) -> set[str]:
    """
    分词：CamelCase 拆分 + 中英文边界切割 + 按非字符切割，保留长度 >= 2 的词元。
    并应用别名归一化。
    对中文连续串额外生成双字 bigram，改善中文标题匹配效果。
    """
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
        # 别名归一化
        for alias, canonical in _ALIASES:
            if t == alias:
                t = canonical
                break
        result.add(t)
        # 中文连续串额外生成双字 bigram，增强部分匹配能力
        # 例如 "龙虾之父回应" → {龙虾, 虾之, 之父, 父回, 回应}
        if re.fullmatch(r"[\u4e00-\u9fff]{3,}", t):
            for i in range(len(t) - 1):
                result.add(t[i:i+2])

    return result


def _similar(a: set, b: set, threshold: float) -> bool:
    """
    两个词集相似性判断：仅用 Jaccard >= threshold。
    不用"共享词数 >= N"条件，避免 open/ai 这类泛词触发误合并。
    """
    if not a or not b:
        return False
    jaccard_score = len(a & b) / len(a | b)
    return jaccard_score >= threshold


def _merge_group(group: list[dict]) -> dict:
    """
    将一组相似文章合并为一条。
    - 保留摘要最长的那篇内容作为主体
    - sources_list 记录所有来源（去重，保持顺序）
    """
    # 选摘要最长的作为主体
    primary = max(group, key=lambda x: len(x.get("summary", "")))
    merged = dict(primary)

    # 收集所有来源（按 source_name 去重，URL 保留第一个出现的）
    seen_sources: set[str] = set()
    sources_list = []
    for item in group:
        name = item.get("source_name", "")
        if name and name not in seen_sources:
            seen_sources.add(name)
            sources_list.append({
                "source_name": name,
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
            })

    merged["sources_list"] = sources_list
    # source_name 改为所有来源的联合展示
    merged["source_name"] = " / ".join(s["source_name"] for s in sources_list)
    return merged


def _keyword_dedupe(items: list[dict], sim_threshold: float = 0.4) -> list[dict]:
    """
    基于标题关键词的去重聚合（兜底方案）。
    两轮聚合：
    1. 代表文章匹配（每篇和已有组的代表比较）
    2. 组间合并（把相似的组再合并一次，解决代表风格差异导致的漏合并）
    """
    token_sets = [_tokenize(item.get("title", "")) for item in items]

    # 第一轮：代表文章匹配
    groups: list[list[int]] = []      # 每组存 item 下标
    group_repr: list[set] = []        # 每组代表文章的 token set

    for i, ts in enumerate(token_sets):
        merged = False
        for g_idx, repr_ts in enumerate(group_repr):
            if _similar(ts, repr_ts, sim_threshold):
                groups[g_idx].append(i)
                merged = True
                break
        if not merged:
            groups.append([i])
            group_repr.append(ts)

    # 第二轮：组间合并（合并相似的组）
    merged_flags = [False] * len(groups)
    final_groups: list[list[int]] = []

    for i in range(len(groups)):
        if merged_flags[i]:
            continue
        current = list(groups[i])
        for j in range(i + 1, len(groups)):
            if merged_flags[j]:
                continue
            if _similar(group_repr[i], group_repr[j], sim_threshold):
                current.extend(groups[j])
                merged_flags[j] = True
        final_groups.append(current)

    # 组装结果
    result = []
    for group_indices in final_groups:
        group = [items[i] for i in group_indices]
        if len(group) == 1:
            item = dict(group[0])
            item.setdefault("sources_list", [{
                "source_name": item.get("source_name", item.get("author", "")),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
            }])
            result.append(item)
        else:
            result.append(_merge_group(group))

    return result


def _claude_dedupe(
    items: list[dict],
    api_key: str,
    base_url: str = "https://api.anthropic.com",
) -> list[list[int]] | None:
    """
    用 Claude 判断哪些文章报道同一事件，返回分组（下标列表的列表）。
    失败时返回 None，由调用方降级到关键词方案。
    """
    titles_text = "\n".join(
        f"{i+1}. {item.get('title', '')}"
        for i, item in enumerate(items)
    )

    prompt = (
        "You are an editorial assistant. Below are today's article titles collected from various sources. "
        "Please identify articles that report on the same event and group them together.\n\n"
        "Rules:\n"
        "- Same event: different media outlets reporting on the EXACT same news/release/announcement\n"
        "- Articles must share the same core fact to be grouped (e.g. both report 'Company X released product Y')\n"
        "- Merely sharing a keyword, product name, or topic is NOT enough — the reported event must be identical\n"
        "- Different angles, opinions, analyses, or aspects of the same subject are NOT the same event\n"
        "- Example of NOT same event: 'GPT-5 technical details' vs 'Trump officials encourage banks to test GPT-5' — both mention GPT-5 but report different events\n"
        "- Example of SAME event: 'OpenAI launches GPT-5' vs 'OpenAI发布GPT-5' — same announcement, different languages\n"
        "- When in doubt, keep articles in separate groups\n"
        "- Articles with no duplicates should be in their own group\n\n"
        f"Article list:\n{titles_text}\n\n"
        "Return strictly in JSON format, no other text:\n"
        '{"groups": [[1,2], [3], [4,5,6], ...]}'
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        for attempt in range(3):
            try:
                message = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                )
                break
            except anthropic.RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise
        if not message.content:
            logger.warning("Claude 去重返回空内容，降级到关键词方案")
            return None
        raw = message.content[0].text.strip()
        logger.info("Claude 去重原始响应: %s", raw[:500])
    except ImportError:
        logger.warning("未安装 anthropic 库，降级到关键词方案")
        return None
    except anthropic.APIError as e:
        logger.warning("Claude 去重 API 错误（%s），降级到关键词方案", e)
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Claude 去重响应解析失败（%s），降级到关键词方案", e)
        return None

    try:
        # 取最后一个完整 JSON 对象（Claude 有时会先输出错误答案再自我纠正）
        end = raw.rfind("}") + 1
        start = raw.rfind("{", 0, end)
        if start == -1 or end == 0:
            logger.warning("Claude 去重响应不含 JSON 对象，降级到关键词方案")
            return None
        data = json.loads(raw[start:end])
        groups = data.get("groups", [])
        # 验证格式：每组是下标列表，下标在合法范围内
        n = len(items)
        valid_groups = []
        for g in groups:
            valid = [idx - 1 for idx in g if isinstance(idx, int) and 1 <= idx <= n]
            if valid:
                valid_groups.append(valid)
        # 确保所有下标都被覆盖
        covered = {idx for g in valid_groups for idx in g}
        for i in range(n):
            if i not in covered:
                valid_groups.append([i])
        return valid_groups
    except Exception as e:
        logger.warning("Claude 去重结果解析失败（%s），降级到关键词方案", e)
        return None


def dedupe_items(
    items: list[dict],
    sim_threshold: float = 0.4,
    api_key: str = "",
    base_url: str = "https://api.anthropic.com",
) -> list[dict]:
    """
    两阶段去重：
    1. URL / content_hash 精确去重
    2. 标题相似度聚合：优先用 Claude，失败时降级到关键词匹配

    Claude 方案：将所有标题发给 Claude，让它判断哪些报道同一事件。
    关键词兜底：双字 bigram + Jaccard 相似度 + 两轮聚合。
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

    if len(exact_deduped) <= 1:
        for item in exact_deduped:
            item.setdefault("sources_list", [{
                "source_name": item.get("source_name", ""),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
            }])
        return exact_deduped

    # 第二阶段：相似度聚合
    groups: list[list[int]] | None = None

    if api_key:
        logger.info("使用 Claude 去重（共 %d 篇）...", len(exact_deduped))
        groups = _claude_dedupe(exact_deduped, api_key, base_url)
        if groups is not None:
            logger.info("Claude 去重完成，聚合为 %d 条", len(groups))

    if groups is None:
        logger.info("使用关键词方案去重...")
        deduped = _keyword_dedupe(exact_deduped, sim_threshold)
        return deduped

    # 按 Claude 分组结果组装
    result = []
    for group_indices in groups:
        group = [exact_deduped[i] for i in group_indices]
        if len(group) == 1:
            item = dict(group[0])
            item.setdefault("sources_list", [{
                "source_name": item.get("source_name", ""),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
            }])
            result.append(item)
        else:
            result.append(_merge_group(group))

    return result
