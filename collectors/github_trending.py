"""GitHub Trending 采集器。

抓取 GitHub Trending 页面，筛选 AI/ML 相关仓库。
无需认证，直接解析 HTML（页面结构稳定）。
未登录状态下每次返回约 25 个仓库。
"""
import re
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests

from utils.errors import CollectorError
from utils.http import retry_session
from utils.log import get_logger

logger = get_logger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"

# AI/ML 相关关键词（匹配仓库名或描述）
AI_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "gemini", "llama", "mistral",
    "machine learning", "deep learning", "neural", "transformer",
    "diffusion", "generative", "chatbot", "copilot", "agent",
    "rag", "embedding", "vector", "inference", "fine-tun",
    "openai", "anthropic", "hugging", "langchain", "multimodal",
    "vision", "nlp", "computer vision", "reinforcement",
    "deepseek", "qwen", "reasoning", "model", "dataset",
    "stable diffusion", "midjourney", "flux",
    "cuda", "gpu", "tpu", "nvidia",
]


def _is_ai_related(name: str, description: str) -> bool:
    """判断仓库是否与 AI/ML 相关。"""
    text = (name + " " + description).lower()
    return any(kw in text for kw in AI_KEYWORDS)


class _TrendingParser(HTMLParser):
    """解析 GitHub Trending 页面的 HTML。"""

    def __init__(self):
        super().__init__()
        self.repos: list[dict] = []
        self._current: dict = {}
        self._in_article = False
        self._in_desc_p = False
        self._in_repo_link = False
        self._desc_buf = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_d = dict(attrs)

        if tag == "article":
            self._in_article = True
            self._current = {}
            self._desc_buf = ""

        elif tag == "h2" and self._in_article:
            # 下一个 a 标签就是仓库链接
            self._in_repo_link = True

        elif tag == "a" and self._in_repo_link and self._in_article:
            href = attrs_d.get("href", "").strip()
            if href and href.count("/") == 2:  # /owner/repo 格式
                self._current["url"] = "https://github.com" + href
                self._current["name"] = href.strip("/")
            self._in_repo_link = False

        elif tag == "p" and self._in_article:
            cls = attrs_d.get("class", "")
            if "col-9" in cls or "color-fg-muted" in cls:
                self._in_desc_p = True
                self._desc_buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self._in_article:
            if self._current.get("name"):
                desc = self._desc_buf.strip()
                self._current["description"] = re.sub(r"\s+", " ", desc)
                self.repos.append(dict(self._current))
            self._in_article = False
            self._current = {}
            self._desc_buf = ""

        elif tag == "h2":
            self._in_repo_link = False

        elif tag == "p" and self._in_desc_p:
            self._in_desc_p = False

    def handle_data(self, data: str) -> None:
        if self._in_article and self._in_desc_p:
            self._desc_buf += data

        # 提取 "343 stars today" 或 "1,197 stars today"
        if self._in_article and "stars today" in data:
            m = re.search(r"([\d,]+)\s+stars today", data)
            if m:
                self._current["stars_today"] = int(m.group(1).replace(",", ""))

        # 提取总 star 数（在 stargazers 链接旁的文本）
        if self._in_article and re.search(r"^\s*[\d,]+\s*$", data):
            num_str = data.strip().replace(",", "")
            if num_str.isdigit():
                val = int(num_str)
                # 避免把其他数字误判，只更新 stars_total（取最大那个）
                if val > self._current.get("stars_total", 0):
                    self._current["stars_total"] = val


class GitHubTrendingCollector:
    """GitHub Trending AI/ML 仓库采集器。"""

    def __init__(
        self,
        since: str = "daily",
        language: str = "",
        max_repos: int = 10,
        timeout: int = 15,
    ):
        """
        Args:
            since: 时间范围 daily / weekly / monthly
            language: 筛选编程语言（如 "python"），空字符串表示不限语言
            max_repos: 最终返回条数上限
            timeout: HTTP 请求超时秒数
        """
        self.since = since
        self.language = language
        self.max_repos = max_repos
        self.timeout = timeout
        self._session = retry_session()

    def fetch_trending_repos(self) -> list[dict]:
        """采集 GitHub Trending AI/ML 仓库。

        Raises:
            CollectorError: HTTP 请求失败

        Returns:
            仓库列表，每项包含 name, url, description,
            stars_today, stars_total, language, fetched_at
        """
        url = GITHUB_TRENDING_URL
        if self.language:
            url = f"{url}/{self.language}"

        params = {"since": self.since}
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        logger.info("查询 GitHub Trending: since=%s language=%s",
                    self.since, self.language or "all")

        try:
            resp = self._session.get(
                url, params=params, headers=headers, timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CollectorError(f"GitHub Trending 请求失败: {e}") from e

        # 解析 HTML
        parser = _TrendingParser()
        try:
            parser.feed(resp.text)
        except Exception as e:
            raise CollectorError(f"GitHub Trending HTML 解析失败: {e}") from e

        all_repos = parser.repos
        logger.info("GitHub Trending 返回 %d 个仓库", len(all_repos))

        # 筛选 AI/ML 相关
        ai_repos = []
        for repo in all_repos:
            name = repo.get("name", "")
            desc = repo.get("description", "")
            if _is_ai_related(name, desc):
                repo["fetched_at"] = datetime.now(timezone.utc).isoformat()
                repo.setdefault("stars_today", 0)
                repo.setdefault("stars_total", 0)
                ai_repos.append(repo)

        # 按今日 star 数降序
        ai_repos.sort(key=lambda x: x.get("stars_today", 0), reverse=True)

        result = ai_repos[:self.max_repos]
        logger.info("筛选后保留 %d 个 AI/ML 相关仓库（共 %d 个候选）",
                    len(result), len(all_repos))
        return result
