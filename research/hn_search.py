"""Hacker News Algolia Search API 封装。"""
from utils.errors import CollectorError
from utils.http import retry_session
from utils.log import get_logger

logger = get_logger(__name__)

HN_SEARCH_API = "https://hn.algolia.com/api/v1/search"


class HNSearcher:
    """Hacker News 搜索器。"""

    def __init__(self, timeout: int = 15):
        """
        Args:
            timeout: HTTP 请求超时秒数
        """
        self.timeout = timeout
        self._session = retry_session()

    def search_stories(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """按关键词搜索 HN 讨论。

        Args:
            query: 搜索关键词
            max_results: 最多返回条数

        Raises:
            CollectorError: API 请求失败

        Returns:
            讨论列表，每项包含 id, title, url, score, comments,
            created_at, author, hn_url
        """
        params = {
            "query": query,
            "tags": "story",  # 只搜索 story 类型（不含 comment/poll）
            "hitsPerPage": min(max_results, 100),
        }

        logger.info("HN 搜索: %s (max_results=%d)", query, max_results)

        try:
            resp = self._session.get(
                HN_SEARCH_API,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception as e:
            raise CollectorError(f"HN Search API 请求失败: {e}") from e

        try:
            data = resp.json()
        except ValueError as e:
            raise CollectorError(f"HN API 返回非 JSON: {e}") from e

        hits = data.get("hits", [])
        logger.info("HN 搜索返回 %d 条结果", len(hits))

        results = []
        for hit in hits[:max_results]:
            story_id = hit.get("objectID", "")
            results.append({
                "id": story_id,
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "score": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "author": hit.get("author", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
            })

        return results
