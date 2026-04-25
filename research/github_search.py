"""GitHub Search API 封装，按关键词搜索仓库。"""
from utils.errors import CollectorError
from utils.http import retry_session
from utils.log import get_logger

logger = get_logger(__name__)

GITHUB_SEARCH_API = "https://api.github.com/search/repositories"


class GitHubSearcher:
    """GitHub 仓库搜索器。"""

    def __init__(self, timeout: int = 15):
        """
        Args:
            timeout: HTTP 请求超时秒数
        """
        self.timeout = timeout
        self._session = retry_session()

    def search_repositories(
        self,
        query: str,
        max_results: int = 10,
        language: str = "",
    ) -> list[dict]:
        """按关键词搜索 GitHub 仓库。

        Args:
            query: 搜索关键词
            max_results: 最多返回条数
            language: 筛选编程语言（如 "python"），空字符串表示不限

        Raises:
            CollectorError: API 请求失败

        Returns:
            仓库列表，每项包含 name, full_name, url, description,
            stars, language, updated_at
        """
        # 构建搜索查询
        search_query = query
        if language:
            search_query += f" language:{language}"

        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max_results, 100),  # GitHub API 限制单页最多100条
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Mozilla/5.0 (compatible; NewsAggregator/1.0)",
        }

        logger.info("GitHub 搜索: %s (max_results=%d)", query, max_results)

        try:
            resp = self._session.get(
                GITHUB_SEARCH_API,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception as e:
            raise CollectorError(f"GitHub Search API 请求失败: {e}") from e

        try:
            data = resp.json()
        except ValueError as e:
            raise CollectorError(f"GitHub API 返回非 JSON: {e}") from e

        items = data.get("items", [])
        logger.info("GitHub 搜索返回 %d 个仓库", len(items))

        results = []
        for item in items[:max_results]:
            results.append({
                "name": item.get("name", ""),
                "full_name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "updated_at": item.get("updated_at", ""),
            })

        return results
