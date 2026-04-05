"""Hacker News 采集器。

使用 HN 官方 Firebase API（完全免费，无需认证）获取热门 AI 相关文章。
筛选逻辑：标题匹配 AI 关键词 + score 阈值过滤。
"""
import requests
from datetime import datetime, timezone

from utils.log import get_logger

logger = get_logger(__name__)

HN_API = "https://hacker-news.firebaseio.com/v0"

# AI 相关关键词（不区分大小写匹配）
AI_KEYWORDS = [
    "ai", "gpt", "llm", "claude", "openai", "anthropic",
    "machine learning", "deep learning", "neural",
    "transformer", "diffusion", "generative",
    "chatbot", "copilot", "gemini", "llama", "mistral",
    "deepseek", "reasoning", "agi", "artificial intelligence",
    "fine-tun", "embedding", "vector database",
    "langchain", "rag", "agent", "multimodal",
    "stable diffusion", "midjourney", "sora",
    "nvidia", "cuda", "gpu", "tpu",
]

# 排除的关键词（减少误匹配）
EXCLUDE_KEYWORDS = [
    "hiring", "who is hiring", "freelancer",
    "ask hn: who", "tell hn",
]


def _is_ai_related(title: str) -> bool:
    """判断标题是否与 AI 相关。"""
    title_lower = title.lower()
    # 先排除
    for kw in EXCLUDE_KEYWORDS:
        if kw in title_lower:
            return False
    # 再匹配
    return any(kw in title_lower for kw in AI_KEYWORDS)


def _fetch_story(story_id: int, timeout: int = 10) -> dict | None:
    """获取单条 HN story 详情。"""
    try:
        resp = requests.get(
            f"{HN_API}/item/{story_id}.json",
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


class HackerNewsCollector:
    """Hacker News AI 文章采集器。"""

    def __init__(
        self,
        min_score: int = 20,
        max_stories: int = 10,
        scan_limit: int = 200,
        timeout: int = 10,
    ):
        """
        Args:
            min_score: 最低 upvote 分数阈值
            max_stories: 最多返回条数
            scan_limit: 扫描 Top Stories 的前 N 条
            timeout: 单次 HTTP 请求超时秒数
        """
        self.min_score = min_score
        self.max_stories = max_stories
        self.scan_limit = scan_limit
        self.timeout = timeout

    def fetch_top_ai_stories(self) -> list[dict]:
        """
        获取 HN Top Stories 中与 AI 相关的文章。

        返回列表，每项包含:
            - id: HN story ID
            - title: 标题
            - url: 原文链接（部分 HN 帖子无外链，此时为 HN 讨论页）
            - score: upvote 分数
            - comments: 评论数
            - time: 发布时间（ISO 格式字符串）
            - hn_url: HN 讨论页链接
        """
        # 获取 Top Stories ID 列表
        try:
            resp = requests.get(
                f"{HN_API}/topstories.json",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            story_ids = resp.json()[:self.scan_limit]
        except Exception as e:
            logger.error("获取 HN Top Stories 失败: %s", e)
            return []

        # 逐条获取并筛选
        ai_stories = []
        for story_id in story_ids:
            story = _fetch_story(story_id, self.timeout)
            if not story or story.get("type") != "story":
                continue

            title = story.get("title", "")
            score = story.get("score", 0)

            # 筛选：AI 相关 + score 达标
            if not _is_ai_related(title):
                continue
            if score < self.min_score:
                continue

            # 发布时间
            ts = story.get("time", 0)
            pub_time = datetime.fromtimestamp(ts, tz=timezone.utc)

            hn_url = f"https://news.ycombinator.com/item?id={story_id}"
            url = story.get("url", hn_url)  # 无外链时用 HN 讨论页

            ai_stories.append({
                "id": story_id,
                "title": title,
                "url": url,
                "score": score,
                "comments": story.get("descendants", 0),
                "time": pub_time.isoformat(),
                "hn_url": hn_url,
                "by": story.get("by", ""),
            })

            if len(ai_stories) >= self.max_stories:
                break

        # 按 score 降序排列
        ai_stories.sort(key=lambda x: x["score"], reverse=True)
        return ai_stories
