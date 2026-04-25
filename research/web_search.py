"""Web 搜索 API 封装，优先使用 Exa AI，降级到 Google/Bing/DuckDuckGo。"""
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.errors import CollectorError
from utils.http import retry_session
from utils.log import get_logger

logger = get_logger(__name__)

GOOGLE_SEARCH_API = "https://www.googleapis.com/customsearch/v1"
BING_SEARCH_API = "https://api.bing.microsoft.com/v7.0/search"


class WebSearcher:
    """Web 搜索器（Exa 优先 → Google → Bing → DuckDuckGo）。"""

    def __init__(
        self,
        google_api_key: str = "",
        google_cx: str = "",
        bing_api_key: str = "",
        timeout: int = 15,
    ):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.google_cx = google_cx or os.getenv("GOOGLE_SEARCH_CX", "")
        self.bing_api_key = bing_api_key or os.getenv("BING_SEARCH_API_KEY", "")
        self.timeout = timeout
        self._session = retry_session()

    def search_articles(self, topic: str, max_results: int = 10, extra_queries: list[str] | None = None) -> list[dict]:
        """搜索技术文章。优先级：Exa → Google → Bing → DuckDuckGo。

        Args:
            topic: 主搜索词
            max_results: 每个 query 最多返回条数
            extra_queries: 额外的扩展 query 列表（由调用方提供，如 Claude 扩展的子查询）
        """
        # 优先 Exa
        try:
            results = self._search_exa_multi(topic, extra_queries or [], max_results)
            if results:
                logger.info("使用 Exa Search，返回 %d 条结果", len(results))
                return results
            else:
                logger.warning("Exa Search 返回空结果，降级到 Google/Bing")
        except Exception as e:
            logger.warning("Exa Search 失败: %s，降级到 Google/Bing", e)

        # 降级到 Google
        if self.google_api_key and self.google_cx:
            try:
                results = self._search_google(topic, max_results)
                logger.info("使用 Google Search，返回 %d 条结果", len(results))
                return results
            except Exception as e:
                logger.warning("Google Search 失败: %s，降级到 Bing", e)

        # 降级到 Bing
        if self.bing_api_key:
            try:
                results = self._search_bing(topic, max_results)
                logger.info("使用 Bing Search，返回 %d 条结果", len(results))
                return results
            except Exception as e:
                logger.warning("Bing Search 失败: %s，降级到 DuckDuckGo", e)

        # 最终降级：DuckDuckGo
        try:
            results = self._search_ddg(topic, max_results)
            logger.info("使用 DuckDuckGo，返回 %d 条结果", len(results))
            return results
        except Exception as e:
            raise CollectorError(f"所有搜索引擎都失败: {e}") from e

    def _search_exa_multi(self, topic: str, extra_queries: list[str], max_results: int) -> list[dict]:
        """并行执行多个 Exa query，结果合并去重（按 url）。"""
        # base query 保持原始 topic，extra_queries 由 Claude 扩展提供
        all_queries = [topic] + extra_queries
        seen_urls: set[str] = set()
        merged: list[dict] = []

        with ThreadPoolExecutor(max_workers=min(len(all_queries), 5)) as executor:
            futures = {executor.submit(self._search_exa, q, max_results): q for q in all_queries}
            for future in as_completed(futures):
                try:
                    for item in future.result():
                        if item["url"] not in seen_urls:
                            seen_urls.add(item["url"])
                            merged.append(item)
                except Exception as e:
                    logger.warning("Exa 子查询失败（%s）: %s", futures[future], e)

        logger.info("Exa 多 query 合并：%d 个 query → %d 条去重结果", len(all_queries), len(merged))
        return merged

    def _search_exa(self, query: str, max_results: int) -> list[dict]:
        """使用 Exa AI 搜索单个 query（通过 mcporter CLI）。"""
        logger.info("Exa 搜索: %s", query)
        # json.dumps 转义 query 中的特殊字符，int() 保证 numResults 类型安全
        # mcporter 将整个字符串作为表达式解析，不经过 shell，无二次注入风险
        call_expr = f"exa.web_search_exa(query: {json.dumps(query)}, numResults: {int(max_results)})"

        try:
            result = subprocess.run(
                ["mcporter", "call", call_expr],
                capture_output=True, text=True, timeout=30,
            )
        except FileNotFoundError:
            raise CollectorError("mcporter 未安装，无法使用 Exa Search")
        if result.returncode != 0:
            raise CollectorError(f"mcporter 调用失败: {result.stderr[:200]}")

        return self._parse_exa_output(result.stdout)

    def _parse_exa_output(self, output: str) -> list[dict]:
        """解析 mcporter exa 输出，格式为多段 Title/URL/Published/Author/Highlights。"""
        results = []
        # 按空行分割各条结果
        blocks = re.split(r'\n(?=Title:)', output.strip())
        for block in blocks:
            if not block.strip():
                continue
            title = re.search(r'^Title:\s*(.+)', block, re.MULTILINE)
            url = re.search(r'^URL:\s*(.+)', block, re.MULTILINE)
            published = re.search(r'^Published:\s*(.+)', block, re.MULTILINE)
            # Highlights 作为 snippet
            highlights = re.search(r'Highlights:\s*([\s\S]+?)(?=\nTitle:|\Z)', block)
            if not title or not url:
                continue
            snippet = highlights.group(1).strip()[:300] if highlights else ""
            results.append({
                "title": title.group(1).strip(),
                "url": url.group(1).strip(),
                "snippet": snippet,
                "published_date": published.group(1).strip() if published else "",
            })
        return results

    def _search_google(self, topic: str, max_results: int) -> list[dict]:
        """使用 Google Custom Search API 搜索"""
        query = f"{topic} 教程"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": min(10, max_results),
            "lr": "lang_zh-CN",
        }
        logger.info("Google 搜索: %s", query)
        resp = self._session.get(GOOGLE_SEARCH_API, params=params, timeout=self.timeout)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        results = []
        seen_urls = set()
        for item in items:
            url = item.get("link", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("snippet", ""),
                "published_date": "",
            })
            if len(results) >= max_results:
                break
        results.sort(key=lambda x: self._is_chinese(x["title"] + x["snippet"]), reverse=True)
        return results

    def _search_bing(self, topic: str, max_results: int) -> list[dict]:
        """使用 Bing Search API 搜索"""
        query = f"{topic} 教程"
        params = {"q": query, "count": min(10, max_results), "mkt": "zh-CN", "responseFilter": "Webpages"}
        headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
        logger.info("Bing 搜索: %s", query)
        resp = self._session.get(BING_SEARCH_API, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        web_pages = resp.json().get("webPages", {}).get("value", [])
        results = []
        seen_urls = set()
        for page in web_pages:
            url = page.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({
                "title": page.get("name", ""),
                "url": url,
                "snippet": page.get("snippet", ""),
                "published_date": page.get("datePublished", ""),
            })
            if len(results) >= max_results:
                break
        results.sort(key=lambda x: self._is_chinese(x["title"] + x["snippet"]), reverse=True)
        return results

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
        results.sort(key=lambda x: self._is_chinese(x["title"] + x["snippet"]), reverse=True)
        return results

    def _is_chinese(self, text: str) -> bool:
        return any('\u4e00' <= char <= '\u9fff' for char in text)
