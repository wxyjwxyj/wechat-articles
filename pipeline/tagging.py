# pipeline/tagging.py
#
# 规则说明：
#   - 每条规则 (标签名, 分类, [触发关键词])，关键词不区分大小写
#   - 规则顺序 = 优先级：更具体的放前面，宽泛的（如"大模型"）放后面
#   - 一篇文章可匹配多个标签，但最多取前 MAX_TAGS 个
#
# 分类用于 topics 排序：同分类内按文章数降序，分类间按固定顺序
#
import json

from utils.log import get_logger

logger = get_logger(__name__)

MAX_TAGS = 4

# 分类顺序定义（值越小越靠前）
_CATEGORY_ORDER = {
    "编程工具": 0,
    "AI公司":   1,
    "AI技术":   2,
    "行业应用": 3,
    "学术":     4,
    "宽泛":     5,
}

# (标签名, 分类, 触发关键词列表)
PATTERNS = [
    # ── 编程 / 开发工具 ──────────────────────────────────────────
    ("Claude Code",  "编程工具", ["Claude Code"]),
    ("Vibe Coding",  "编程工具", ["Vibe Coding", "vibe coding"]),
    ("开源",         "编程工具", ["开源", "open source", "Apache 2.0", "MIT license"]),

    # ── AI 产品 / 公司 ───────────────────────────────────────────
    ("OpenAI",   "AI公司", ["OpenAI", "ChatGPT", "GPT-4", "GPT-5", "Sora", "o3", "o4"]),
    ("Anthropic","AI公司", ["Anthropic", "Claude", "Mythos"]),
    ("Google",   "AI公司", ["Google", "Gemini", "Gemma", "DeepMind", "谷歌"]),
    ("Meta",     "AI公司", ["Meta", "Llama", "LLaMA"]),
    ("DeepSeek", "AI公司", ["DeepSeek", "深度求索"]),
    ("Kimi",     "AI公司", ["Kimi", "月之暗面"]),
    ("阿里",     "AI公司", ["阿里", "通义", "千问", "Qwen", "阿里云"]),
    ("字节",     "AI公司", ["字节", "豆包", "抖音", "Bytedance", "ByteDance"]),
    ("腾讯",     "AI公司", ["腾讯", "混元", "微信", "WeChat"]),
    ("百度",     "AI公司", ["百度", "文心", "ERNIE"]),
    ("小米",     "AI公司", ["小米", "Xiaomi"]),
    ("苹果",     "AI公司", ["苹果", "Apple", "iPhone", "Siri", "iOS"]),
    ("英伟达",   "AI公司", ["英伟达", "NVIDIA", "CUDA", "GPU"]),
    ("商汤",     "AI公司", ["商汤", "SenseTime"]),

    # ── AI 技术方向 ───────────────────────────────────────────────
    ("Agent",   "AI技术", ["Agent", "智能体", "多智能体", "AgentOS", "agentic"]),
    ("具身智能","AI技术", ["具身智能", "机器人", "robot", "humanoid", "导航"]),
    ("多模态",  "AI技术", ["多模态", "multimodal", "视觉语言", "VLM", "图像语音"]),
    ("视频生成","AI技术", ["视频生成", "AI视频", "文生视频", "video generation"]),
    ("RAG",     "AI技术", ["RAG", "知识库", "检索增强", "向量数据库"]),
    ("强化学习","AI技术", ["强化学习", "RL", "RLHF", "奖励模型", "reward model"]),
    ("推理",    "AI技术", ["推理能力", "reasoning", "思维链", "chain of thought", "CoT"]),
    ("模型训练","AI技术", ["SFT", "微调", "fine-tune", "预训练", "蒸馏", "distill"]),
    ("AI安全",  "AI技术", ["AI安全", "对齐", "alignment", "越狱", "jailbreak", "勒索", "情绪"]),

    # ── 行业应用 ─────────────────────────────────────────────────
    ("AI编程","行业应用", ["Copilot", "代码生成", "编程助手", "coding"]),
    ("Cursor","编程工具", ["Cursor"]),  # AI 编程 IDE
    ("AI搜索","行业应用", ["AI搜索", "搜索引擎", "Perplexity"]),
    ("AR/VR", "行业应用", ["AR", "VR", "XR", "眼镜", "XREAL", "空间计算"]),
    ("芯片",  "行业应用", ["芯片", "算力", "TPU", "NPU", "半导体", "内存"]),
    ("创业",  "行业应用", ["创业", "融资", "估值", "IPO", "上市", "投资"]),
    ("招聘",  "行业应用", ["招聘", "内推", "实习", "offer"]),

    # ── 学术 / 会议 ───────────────────────────────────────────────
    ("学术", "学术", ["CVPR", "NeurIPS", "ICLR", "ICML", "AAAI", "论文", "arxiv", "基准"]),

    # ── 兜底：宽泛标签放最后 ──────────────────────────────────────
    ("大模型", "宽泛", ["大模型", "LLM", "语言模型", "基础模型", "foundation model",
                        "token", "Token", "参数", "亿参"]),
    ("AI",     "宽泛", ["AI", "人工智能"]),

    ("Vercel", "AI公司", ["Vercel", "vercel-labs"]),  # auto-added: appeared in GitHub Trending with AI skills project

    ("Tencent", "AI公司", ["腾讯", "Tencent", "混元"]),  # auto-added: appeared in 1 article but Tencent is major AI play

    ("Huawei", "AI芯片", ["华为芯片", "Huawei chip", "Huawei"]),  # auto-added: emerging hardware partnership trend with DeepSeek

    ("Tencent Hunyuan", "AI公司", ["腾讯 Hy3", "Hunyuan", "混元"]),  # auto-added: Tencent's competing model appearing in news cycle
]

# 标签名 -> 分类，供 build_topics 排序
_TAG_CATEGORY: dict[str, str] = {tag: cat for tag, cat, _ in PATTERNS}

# 标签名 -> 关键词列表，供 build_topics 输出
_PATTERN_KEYWORDS: dict[str, list[str]] = {tag: kws for tag, _, kws in PATTERNS}

# 所有合法标签名，供 Claude 参考
ALL_TAGS = [tag for tag, _, _ in PATTERNS]

# 关键词匹配用的简化列表 (标签名, 关键词列表)
_MATCH_PATTERNS = [(tag, kws) for tag, _, kws in PATTERNS]


def extract_tags(item: dict) -> list[str]:
    """从 title 和 summary 中提取标签，按 PATTERNS 顺序返回，最多 MAX_TAGS 个。"""
    text = f'{item.get("title", "")} {item.get("summary", "")}'
    text_lower = text.lower()
    tags = []
    for tag, keywords in _MATCH_PATTERNS:
        if len(tags) >= MAX_TAGS:
            break
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(tag)
    return tags


BATCH_SIZE = 15  # 每批最多处理条数，避免 JSON 过长解析失败


def _call_claude_batch(
    items: list[dict],
    id_offset: int,
) -> list[dict]:
    """调用 Claude 为一批文章打标签+评分，返回与 items 等长的结果列表。"""
    from utils.claude import claude_call

    articles_text = "\n".join(
        f"{id_offset + i + 1}. 标题：{item.get('title', '')}  摘要：{item.get('summary', '')[:80]}"
        for i, item in enumerate(items)
    )
    tags_list = "、".join(ALL_TAGS)

    prompt = f"""You are a tech news editorial assistant. For each article below:
1. Select the most appropriate tags (1-{MAX_TAGS}) from the tag library
2. Assign an importance score (0-10):
   - 9-10: Major industry events, top model releases, important policies
   - 7-8: Notable product updates, research results, company news
   - 5-6: General news, feature updates, industry data
   - 3-4: Advertorials, job postings, event notices, loosely AI-related
   - 0-2: Irrelevant content, ads

Tag library: {tags_list}

Articles:
{articles_text}

Requirements:
- Tags must come from the tag library; prefer specific tags (e.g. "OpenAI", "具身智能") over broad ones
- Return strictly in JSON format, no other text

Format:
{{"results": [{{"id": {id_offset + 1}, "tags": ["标签A", "标签B"], "score": 8}}, ...]}}"""

    raw = claude_call(prompt, max_tokens=1024)

    from utils.claude import extract_json
    data = extract_json(raw)
    results = data.get("results", [])

    tag_set = set(ALL_TAGS)
    output = [{"tags": [], "score": 5} for _ in items]
    for r in results:
        # id 是全局编号，转换为批内下标
        idx = r.get("id", 0) - id_offset - 1
        if 0 <= idx < len(items):
            output[idx] = {
                "tags": [t for t in r.get("tags", []) if t in tag_set][:MAX_TAGS],
                "score": int(r.get("score", 5)),
            }
    return output


def extract_tags_batch_with_claude(
    items: list[dict],
    api_key: str = "",
    base_url: str = "",
) -> list[dict]:
    """
    用 Claude API 批量为文章打标签，同时打重要性分数（0-10）。
    自动分批（每批 BATCH_SIZE 条），避免 JSON 过长解析失败。
    返回与 items 等长的列表，每项为 {"tags": [...], "score": int}。
    失败时返回空列表，由调用方降级到关键词匹配。

    注意：api_key/base_url 参数已废弃，配置统一由 utils.claude 管理。
    """
    output: list[dict] = []
    for batch_start in range(0, len(items), BATCH_SIZE):
        batch = items[batch_start: batch_start + BATCH_SIZE]
        try:
            batch_result = _call_claude_batch(batch, batch_start)
            output.extend(batch_result)
            logger.debug("批次 %d-%d 打标签完成", batch_start + 1, batch_start + len(batch))
        except (json.JSONDecodeError, KeyError, IndexError, Exception) as e:
            logger.warning("批次 %d-%d 打标签失败（%s），该批降级到关键词匹配",
                           batch_start + 1, batch_start + len(batch), e)
            output.extend([{"tags": [], "score": 5} for _ in batch])

    return output


def build_topics(items: list[dict]) -> list[dict]:
    """
    统计所有 item 的标签频次，返回按「分类顺序 → 文章数降序」排列的 topic 列表。
    分类顺序：编程工具 → AI公司 → AI技术 → 行业应用 → 学术 → 宽泛
    每条 topic 带有 category 字段，供前端分组显示。
    """
    counts: dict[str, int] = {}
    for item in items:
        for tag in item.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1

    def sort_key(item):
        name, count = item
        cat = _TAG_CATEGORY.get(name, "宽泛")
        cat_order = _CATEGORY_ORDER.get(cat, 99)
        return (cat_order, -count, name)

    return [
        {
            "name": name,
            "count": count,
            "category": _TAG_CATEGORY.get(name, "宽泛"),
            "keywords": _PATTERN_KEYWORDS.get(name, [name]),
        }
        for name, count in sorted(counts.items(), key=sort_key)
    ]
