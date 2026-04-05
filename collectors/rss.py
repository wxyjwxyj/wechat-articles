"""通用 RSS/Atom Feed 采集器。

支持任意 RSS 2.0 / Atom feed，通过关键词过滤 AI 相关条目。
使用 feedparser 解析，无需处理各站点格式差异。
"""
import re
import feedparser
from datetime import datetime, timezone, timedelta

from utils.errors import CollectorError
from utils.log import get_logger

logger = get_logger(__name__)

# AI 相关关键词（标题或摘要匹配任意一个即通过）
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "llama",
    "openai", "anthropic", "google deepmind", "mistral", "deepseek",
    "chatbot", "neural network", "transformer", "diffusion model",
    "agent", "rag", "fine-tun", "generative", "foundation model",
    "robotics", "computer vision", "nlp", "natural language",
]


def _is_ai_related(title: str, summary: str) -> bool:
    """判断条目是否 AI 相关（标题或摘要包含关键词）。"""
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_published(entry) -> datetime:
    """从 feedparser entry 解析发布时间，失败返回当前时间。"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc)


class RssCollector:
    """通用 RSS/Atom Feed 采集器。"""

    def __init__(
        self,
        feed_url: str,
        source_name: str = "",
        max_items: int = 10,
        days_back: int = 2,
        timeout: int = 30,
    ):
        """
        Args:
            feed_url: RSS/Atom feed 地址
            source_name: 来源名称（用于日志）
            max_items: 最多返回条数
            days_back: 只保留最近 N 天的文章
            timeout: HTTP 请求超时秒数
        """
        self.feed_url = feed_url
        self.source_name = source_name or feed_url
        self.max_items = max_items
        self.days_back = days_back
        self.timeout = timeout

    def fetch_recent_items(self) -> list[dict]:
        """采集 feed 中的 AI 相关最新条目。

        Raises:
            CollectorError: feed 解析失败

        Returns:
            条目列表，每项包含 title, url, summary, published, source_name
        """
        logger.info("采集 RSS: %s", self.source_name)

        try:
            feed = feedparser.parse(
                self.feed_url,
                request_headers={"User-Agent": "Mozilla/5.0 (news1-rss-collector/1.0)"},
            )
        except Exception as e:
            raise CollectorError(f"RSS 请求失败 [{self.source_name}]: {e}") from e

        if feed.bozo and not feed.entries:
            raise CollectorError(f"RSS 解析失败 [{self.source_name}]: {feed.bozo_exception}")

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        results = []

        for entry in feed.entries:
            title = getattr(entry, "title", "") or ""
            url = getattr(entry, "link", "") or ""
            # 摘要优先取 summary，部分 feed 用 content
            summary = getattr(entry, "summary", "") or ""
            if not summary and hasattr(entry, "content") and entry.content:
                summary = entry.content[0].get("value", "")

            # 去掉 HTML 标签
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = " ".join(summary.split())[:300]  # 最多 300 字符

            if not title or not url:
                continue

            # 日期过滤
            published = _parse_published(entry)
            if published < cutoff:
                continue

            # AI 关键词过滤
            if not _is_ai_related(title, summary):
                continue

            results.append({
                "title": title,
                "url": url,
                "summary": summary,
                "published": published.isoformat(),
                "source_name": self.source_name,
            })

            if len(results) >= self.max_items:
                break

        logger.info(
            "%s: 找到 %d 条 AI 相关文章（共 %d 条候选）",
            self.source_name, len(results), len(feed.entries)
        )
        return results
