"""Hacker News 采集器。

使用 HN 官方 Firebase API（完全免费，无需认证）获取热门 AI 相关文章。
筛选逻辑：标题匹配 AI 关键词 + score 阈值过滤。
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from utils.errors import CollectorError
from utils.http import retry_session
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
    "embodied ai",
    "world model",
    "mythos",
    "cursor",
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


def _fetch_story(story_id: int, session, timeout: int = 10) -> dict | None:
    """获取单条 HN story 详情。单条失败只记日志，不中断整体流程。"""
    try:
        resp = session.get(
            f"{HN_API}/item/{story_id}.json",
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.debug("HN story %d 获取失败: %s", story_id, e)
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
        self._session = retry_session()

    def fetch_top_ai_stories(self) -> list[dict]:
        """获取 HN Top Stories 中与 AI 相关的文章。

        Raises:
            CollectorError: 无法获取 Top Stories 列表

        Returns:
            列表，每项包含 id, title, url, score, comments, time, hn_url, by
        """
        # 获取 Top Stories ID 列表
        try:
            resp = self._session.get(
                f"{HN_API}/topstories.json",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            story_ids = resp.json()[:self.scan_limit]
        except requests.RequestException as e:
            raise CollectorError(f"获取 HN Top Stories 失败: {e}") from e

        # 并发获取所有 story 详情
        ai_stories = []
        with ThreadPoolExecutor(max_workers=min(len(story_ids), 10)) as executor:
            futures = {executor.submit(_fetch_story, sid, self._session, self.timeout): sid for sid in story_ids}
            for future in as_completed(futures):
                story = future.result()
                if not story or story.get("type") != "story":
                    continue
                title = story.get("title", "")
                score = story.get("score", 0)
                if not _is_ai_related(title) or score < self.min_score:
                    continue
                ts = story.get("time", 0)
                pub_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                story_id = story["id"]
                hn_url = f"https://news.ycombinator.com/item?id={story_id}"
                ai_stories.append({
                    "id": story_id,
                    "title": title,
                    "url": story.get("url", hn_url),
                    "score": score,
                    "comments": story.get("descendants", 0),
                    "time": pub_time.isoformat(),
                    "hn_url": hn_url,
                    "by": story.get("by", ""),
                })

        # 按 score 降序，取前 max_stories 条
        ai_stories.sort(key=lambda x: x["score"], reverse=True)
        return ai_stories[:self.max_stories]
