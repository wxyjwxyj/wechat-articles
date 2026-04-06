"""Web 搜索 API 封装，支持 DuckDuckGo（无需 key）、Google 和 Bing，用于查找中文技术文章和教程。"""
import os
import requests
from utils.errors import CollectorError
from utils.log import get_logger

logger = get_logger(__name__)

GOOGLE_SEARCH_API = "https://www.googleapis.com/customsearch/v1"
BING_SEARCH_API = "https://api.bing.microsoft.com/v7.0/search"


class WebSearcher:
    """Web 搜索器（支持 Google Custom Search 和 Bing Search）。"""

    def __init__(
        self,
        google_api_key: str = "",
        google_cx: str = "",
        bing_api_key: str = "",
        timeout: int = 15,
    ):
        """
        Args:
            google_api_key: Google Custom Search API key（优先使用）
            google_cx: Google Custom Search Engine ID
            bing_api_key: Bing Search API key（降级使用）
            timeout: HTTP 请求超时秒数
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.google_cx = google_cx or os.getenv("GOOGLE_SEARCH_CX", "")
        self.bing_api_key = bing_api_key or os.getenv("BING_SEARCH_API_KEY", "")
        self.timeout = timeout

    def search_articles(
        self,
        topic: str,
        max_results: int = 10,
    ) -> list[dict]:
        """搜索技术文章和教程。

        优先级：Google → Bing → DuckDuckGo（无需 key，零配置）

        Args:
            topic: 搜索主题
            max_results: 最多返回条数

        Returns:
            文章列表，每项包含 title, url, snippet, published_date
        """
        # 优先尝试 Google
        if self.google_api_key and self.google_cx:
            try:
                results = self._search_google(topic, max_results)
                logger.info("使用 Google Search，返回 %d 条结果", len(results))
                return results
            except Exception as e:
                logger.warning("Google Search 失败: %s，尝试降级到 Bing", e)

        # 降级到 Bing
        if self.bing_api_key:
            try:
                results = self._search_bing(topic, max_results)
                logger.info("使用 Bing Search，返回 %d 条结果", len(results))
                return results
            except Exception as e:
                logger.warning("Bing Search 失败: %s，尝试降级到 DuckDuckGo", e)

        # 最终降级：DuckDuckGo（无需 key）
        try:
            results = self._search_ddg(topic, max_results)
            logger.info("使用 DuckDuckGo，返回 %d 条结果", len(results))
            return results
        except Exception as e:
            raise CollectorError(f"所有搜索引擎都失败: {e}") from e

    def _search_google(self, topic: str, max_results: int) -> list[dict]:
        """使用 Google Custom Search API 搜索"""
        # 主查询：直接搜索主题（后续可扩展为多 query）
        query = f"{topic} 教程"

        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": min(10, max_results),
            "lr": "lang_zh-CN",  # 优先中文
        }

        logger.info("Google 搜索: %s", query)

        resp = requests.get(
            GOOGLE_SEARCH_API,
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])

        all_results = []
        seen_urls = set()
        for item in items:
            url = item.get("link", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            all_results.append({
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("snippet", ""),
                "published_date": "",
            })
            if len(all_results) >= max_results:
                break

        # 中文内容排前面
        all_results.sort(
            key=lambda x: self._is_chinese(x["title"] + x["snippet"]),
            reverse=True
        )
        return all_results

    def _search_bing(self, topic: str, max_results: int) -> list[dict]:
        """使用 Bing Search API 搜索"""
        query = f"{topic} 教程"

        params = {
            "q": query,
            "count": min(10, max_results),
            "mkt": "zh-CN",
            "responseFilter": "Webpages",
        }

        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key,
        }

        logger.info("Bing 搜索: %s", query)

        resp = requests.get(
            BING_SEARCH_API,
            params=params,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        web_pages = data.get("webPages", {}).get("value", [])

        all_results = []
        seen_urls = set()
        for page in web_pages:
            url = page.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            all_results.append({
                "title": page.get("name", ""),
                "url": url,
                "snippet": page.get("snippet", ""),
                "published_date": page.get("datePublished", ""),
            })
            if len(all_results) >= max_results:
                break

        # 中文内容排前面
        all_results.sort(
            key=lambda x: self._is_chinese(x["title"] + x["snippet"]),
            reverse=True
        )
        return all_results

    def _search_ddg(self, topic: str, max_results: int) -> list[dict]:
        """使用 DuckDuckGo 搜索（无需 API key）"""
        try:
            from ddgs import DDGS
        except ImportError:
            raise CollectorError("ddgs 未安装，请运行: pip install ddgs")

        query = f"{topic} 教程"
        logger.info("DuckDuckGo 搜索: %s", query)

        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, region="cn-zh", max_results=max_results):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "published_date": "",
                })

        # 中文内容排前面
        results.sort(
            key=lambda x: self._is_chinese(x["title"] + x["snippet"]),
            reverse=True
        )
        return results

    def _is_chinese(self, text: str) -> bool:
        """判断文本是否包含中文字符"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
