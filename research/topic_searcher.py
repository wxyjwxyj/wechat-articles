"""主题搜索聚合器，并行调用多个数据源。"""
import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from collectors.arxiv import ArxivCollector
from research.github_search import GitHubSearcher
from research.hn_search import HNSearcher
from research.doc_library import search_docs
from research.web_search import WebSearcher
from research.wechat_search import WechatSearcher
from research.xhs_search import XhsSearcher
from research.claude_scorer import ClaudeScorer
from utils.log import get_logger

logger = get_logger(__name__)


class TopicSearcher:
    """主题搜索聚合器。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        max_papers: int = 10,
        max_repos: int = 10,
        max_discussions: int = 10,
        max_docs: int = 10,
        max_articles: int = 10,
        google_api_key: str = "",
        google_cx: str = "",
        bing_api_key: str = "",
        max_xhs: int = 10,
    ):
        """
        Args:
            api_key: Claude API key（用于评分）
            base_url: Claude API base URL
            max_papers: ArXiv 论文最多返回条数
            max_repos: GitHub 最多返回条数
            max_discussions: HN 最多返回条数
            max_docs: 文档库最多返回条数
            max_articles: Web 搜索文章最多返回条数
            google_api_key: Google Custom Search API key（留空则读环境变量）
            google_cx: Google Custom Search Engine ID（留空则读环境变量）
            bing_api_key: Bing Search API key（留空则读环境变量）
            max_xhs: 小红书最多返回条数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.max_papers = max_papers
        self.max_repos = max_repos
        self.max_discussions = max_discussions
        self.max_docs = max_docs
        self.max_articles = max_articles
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        self.bing_api_key = bing_api_key
        self.max_xhs = max_xhs

    def search_topic(self, topic: str) -> dict:
        """搜索主题相关的学习资料。

        Args:
            topic: 搜索主题（如"强化学习"、"RAG"）

        Returns:
            按类型分类的结果字典：
            {
                "papers": [...],      # ArXiv 论文
                "repositories": [...], # GitHub 仓库
                "discussions": [...],  # HN 讨论
                "docs": [...],         # 官方文档
                "articles": [...],     # Web 搜索文章
                "wechat": [...],       # 本地公众号文章
                "xhs": [...],          # 小红书笔记
            }
            每项资源都包含 score 和 comment 字段（Claude 评分）
        """
        logger.info("开始搜索主题: %s", topic)

        results = {
            "papers": [],
            "repositories": [],
            "discussions": [],
            "docs": [],
            "articles": [],
            "wechat": [],
            "xhs": [],
        }

        extra_data: dict[str, list] = {}

        # 并行：query 扩展与其他数据源同时启动
        with ThreadPoolExecutor(max_workers=12) as executor:
            # 先提交 query 扩展（与其他源并行）
            expand_future = executor.submit(self._expand_queries, topic)

            futures = {
                executor.submit(self._search_arxiv, topic): "papers",
                executor.submit(self._search_github, topic): "repositories",
                executor.submit(self._search_hn, topic): "discussions",
                executor.submit(self._search_docs, topic): "docs",
                executor.submit(self._search_wechat, topic): "wechat",
                executor.submit(self._search_xhs, topic): "xhs",
            }

            # 等 query 扩展完成，再提交依赖扩展结果的搜索
            extra_queries = expand_future.result() or []
            futures[executor.submit(self._search_web, topic, extra_queries)] = "articles"
            futures[executor.submit(self._search_arxiv_multi, topic, extra_queries)] = "papers_extra"
            futures[executor.submit(self._search_github_multi, topic, extra_queries)] = "repos_extra"
            futures[executor.submit(self._search_hn_multi, topic, extra_queries)] = "discussions_extra"
            futures[executor.submit(self._search_wechat_multi, topic, extra_queries)] = "wechat_extra"
            futures[executor.submit(self._search_xhs_multi, topic, extra_queries)] = "xhs_extra"

            for future in as_completed(futures):
                category = futures[future]
                try:
                    data = future.result()
                    if category in ("papers_extra", "repos_extra", "discussions_extra", "wechat_extra", "xhs_extra"):
                        extra_data[category] = data
                    else:
                        results[category] = data
                        logger.info("%s: 获取 %d 条结果", category, len(data))
                except Exception as e:
                    logger.warning("%s 搜索失败: %s", category, e)
                    if category not in ("papers_extra", "repos_extra", "discussions_extra", "wechat_extra", "xhs_extra"):
                        results[category] = []

        # 所有主结果就绪后，合并扩展 query 的补充结果
        _dedup_key = {
            "papers_extra": "arxiv_id", "repos_extra": "full_name",
            "discussions_extra": "id", "wechat_extra": "url", "xhs_extra": "url",
        }
        _main_cat = {
            "papers_extra": "papers", "repos_extra": "repositories",
            "discussions_extra": "discussions", "wechat_extra": "wechat", "xhs_extra": "xhs",
        }
        for cat, data in extra_data.items():
            key = _dedup_key[cat]
            main = _main_cat[cat]
            seen = {item.get(key) for item in results[main]}
            new_items = [item for item in data if item.get(key) not in seen]
            results[main].extend(new_items)
            logger.info("%s 扩展补充 %d 条（去重后）", main, len(new_items))

        # Claude 评分（除了 docs，因为 docs 是预设的权威资源）
        scorer = ClaudeScorer(api_key=self.api_key, base_url=self.base_url)

        for category in ["papers", "repositories", "discussions", "articles", "wechat", "xhs"]:
            if results[category]:
                try:
                    # 统一格式：确保每项都有 title 和 summary
                    normalized = self._normalize_for_scoring(results[category], category)
                    scored = scorer.score_resources(normalized, topic=topic)
                    results[category] = scored
                except Exception as e:
                    logger.warning("%s 评分失败: %s", category, e)

        # docs 不需要评分，直接标记为高分
        for doc in results["docs"]:
            doc["score"] = 9
            doc["comment"] = "官方文档，权威可靠"

        logger.info("搜索完成：论文 %d, 仓库 %d, 讨论 %d, 文档 %d, 文章 %d, 公众号 %d, 小红书 %d",
                    len(results["papers"]), len(results["repositories"]),
                    len(results["discussions"]), len(results["docs"]),
                    len(results["articles"]), len(results["wechat"]), len(results["xhs"]))

        return results

    def _search_multi(self, search_fn, queries: list[str], dedup_key: str) -> list[dict]:
        """通用多 query 并行搜索，按 dedup_key 去重后返回合并结果。"""
        if not queries:
            return []
        seen: set = set()
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=min(len(queries), 4)) as ex:
            futures = [ex.submit(search_fn, q) for q in queries]
            for f in as_completed(futures):
                try:
                    for item in f.result():
                        key = item.get(dedup_key)
                        if key and key not in seen:
                            seen.add(key)
                            results.append(item)
                except Exception as e:
                    logger.warning("扩展查询失败: %s", e)
        return results

    def _search_arxiv(self, topic: str) -> list[dict]:
        """搜索 ArXiv 论文"""
        collector = ArxivCollector()
        return collector.search_by_keyword(topic, max_results=self.max_papers)

    def _search_arxiv_multi(self, topic: str, extra_queries: list[str]) -> list[dict]:
        """用扩展 query 并行搜索 ArXiv，返回补充结果。"""
        collector = ArxivCollector()
        return self._search_multi(
            lambda q: collector.search_by_keyword(q, self.max_papers),
            extra_queries, "arxiv_id",
        )

    def _search_github(self, topic: str) -> list[dict]:
        """搜索 GitHub 仓库"""
        searcher = GitHubSearcher()
        return searcher.search_repositories(topic, max_results=self.max_repos)

    def _search_github_multi(self, topic: str, extra_queries: list[str]) -> list[dict]:
        """用扩展 query 并行搜索 GitHub，返回补充结果。"""
        searcher = GitHubSearcher()
        return self._search_multi(
            lambda q: searcher.search_repositories(q, self.max_repos),
            extra_queries, "full_name",
        )

    def _search_hn(self, topic: str) -> list[dict]:
        """搜索 HN 讨论"""
        searcher = HNSearcher()
        return searcher.search_stories(topic, max_results=self.max_discussions)

    def _search_hn_multi(self, topic: str, extra_queries: list[str]) -> list[dict]:
        """用扩展 query 并行搜索 HN，返回补充结果。"""
        searcher = HNSearcher()
        return self._search_multi(
            lambda q: searcher.search_stories(q, self.max_discussions),
            extra_queries, "id",
        )

    def _search_docs(self, topic: str) -> list[dict]:
        """搜索文档库"""
        docs = search_docs(topic, max_results=self.max_docs)
        return docs

    def _search_web(self, topic: str, extra_queries: list[str] | None = None) -> list[dict]:
        """搜索 Web 文章（Exa 优先，支持多 query 扩展）"""
        searcher = WebSearcher(
            google_api_key=self.google_api_key,
            google_cx=self.google_cx,
            bing_api_key=self.bing_api_key,
        )
        try:
            articles = searcher.search_articles(topic, max_results=self.max_articles, extra_queries=extra_queries or [])
        except Exception as e:
            logger.warning("Web 搜索失败: %s", e)
            articles = []
        return articles

    def _expand_queries(self, topic: str) -> list[str]:
        """用 Claude 将 topic 扩展为中英双语子查询，提升搜索召回率。"""
        if not self.api_key:
            return []
        prompt = (
            f'Given the technical topic "{topic}", generate 4 related search phrases to find relevant resources:\n'
            f'- 2 English phrases (for papers, docs, GitHub)\n'
            f'- 2 Chinese phrases (for Chinese tech articles)\n'
            f'- Each phrase should be 3-6 words\n'
            f'Return only a JSON array: ["phrase1", "phrase2", "phrase3", "phrase4"]'
        )
        try:
            client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            resp = client.messages.create(
                model="claude-opus-4-6", max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            logger.info("Query 扩展原始响应: %s", raw[:200])
            start, end = raw.find("["), raw.rfind("]") + 1
            if start == -1:
                logger.warning("Query 扩展：响应中未找到 JSON 数组，原始内容: %s", raw[:200])
                return []
            queries = json.loads(raw[start:end])
            logger.info("Query 扩展：%s → %s", topic, queries)
            return [q for q in queries if isinstance(q, str) and q.strip()]
        except Exception as e:
            logger.warning("Query 扩展失败: %s", e)
            return []

    def _search_wechat(self, topic: str) -> list[dict]:
        """搜索本地公众号文章（content.db）"""
        searcher = WechatSearcher()
        return searcher.search_articles(topic, max_results=self.max_articles)

    def _search_wechat_multi(self, topic: str, extra_queries: list[str]) -> list[dict]:
        """用扩展 query 并行搜索本地公众号，返回补充结果。"""
        searcher = WechatSearcher()
        return self._search_multi(
            lambda q: searcher.search_articles(q, self.max_articles),
            extra_queries, "url",
        )

    def _search_xhs(self, topic: str) -> list[dict]:
        """搜索小红书笔记（需提前 xhs login）"""
        searcher = XhsSearcher()
        return searcher.search_notes(topic, max_results=self.max_xhs)

    def _search_xhs_multi(self, topic: str, extra_queries: list[str]) -> list[dict]:
        """用扩展 query 并行搜索小红书，返回补充结果。"""
        searcher = XhsSearcher()
        return self._search_multi(
            lambda q: searcher.search_notes(q, self.max_xhs),
            extra_queries, "url",
        )

    def _normalize_for_scoring(self, items: list[dict], category: str) -> list[dict]:
        """统一格式以便 Claude 评分"""
        normalized = []
        for item in items:
            if category == "papers":
                normalized.append({
                    **item,
                    "title": item.get("title", ""),
                    "summary": item.get("summary", "")[:200],
                })
            elif category == "repositories":
                normalized.append({
                    **item,
                    "title": item.get("full_name", item.get("name", "")),
                    "summary": item.get("description", ""),
                })
            elif category == "discussions":
                normalized.append({
                    **item,
                    "title": item.get("title", ""),
                    "summary": f"HN讨论，{item.get('score', 0)}分，{item.get('comments', 0)}条评论",
                })
            elif category == "articles":
                normalized.append({
                    **item,
                    "title": item.get("title", ""),
                    "summary": item.get("snippet", ""),
                })
            elif category == "wechat":
                normalized.append({
                    **item,
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                })
            elif category == "xhs":
                normalized.append({
                    **item,
                    "title": item.get("title", ""),
                    "summary": f"小红书笔记，❤️{item.get('liked_count', 0)} ⭐{item.get('collected_count', 0)}",
                })
        return normalized
