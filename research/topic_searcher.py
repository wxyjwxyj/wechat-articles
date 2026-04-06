"""主题搜索聚合器，并行调用多个数据源。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collectors.arxiv import ArxivCollector
from research.github_search import GitHubSearcher
from research.hn_search import HNSearcher
from research.doc_library import search_docs
from research.web_search import WebSearcher
from research.wechat_search import WechatSearcher
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
            }
            每项资源都包含 score 和 comment 字段（Claude 评分）
        """
        logger.info("开始搜索主题: %s", topic)

        # 并行调用各数据源
        results = {
            "papers": [],
            "repositories": [],
            "discussions": [],
            "docs": [],
            "articles": [],
            "wechat": [],
        }

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._search_arxiv, topic): "papers",
                executor.submit(self._search_github, topic): "repositories",
                executor.submit(self._search_hn, topic): "discussions",
                executor.submit(self._search_docs, topic): "docs",
                executor.submit(self._search_web, topic): "articles",
                executor.submit(self._search_wechat, topic): "wechat",
            }

            for future in as_completed(futures):
                category = futures[future]
                try:
                    data = future.result()
                    results[category] = data
                    logger.info("%s: 获取 %d 条结果", category, len(data))
                except Exception as e:
                    logger.warning("%s 搜索失败: %s", category, e)
                    results[category] = []

        # Claude 评分（除了 docs，因为 docs 是预设的权威资源）
        scorer = ClaudeScorer(api_key=self.api_key, base_url=self.base_url)

        for category in ["papers", "repositories", "discussions", "articles", "wechat"]:
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

        logger.info("搜索完成：论文 %d, 仓库 %d, 讨论 %d, 文档 %d, 文章 %d, 公众号 %d",
                    len(results["papers"]), len(results["repositories"]),
                    len(results["discussions"]), len(results["docs"]),
                    len(results["articles"]), len(results["wechat"]))

        return results

    def _search_arxiv(self, topic: str) -> list[dict]:
        """搜索 ArXiv 论文"""
        collector = ArxivCollector()
        papers = collector.search_by_keyword(topic, max_results=self.max_papers)
        return papers

    def _search_github(self, topic: str) -> list[dict]:
        """搜索 GitHub 仓库"""
        searcher = GitHubSearcher()
        repos = searcher.search_repositories(topic, max_results=self.max_repos)
        return repos

    def _search_hn(self, topic: str) -> list[dict]:
        """搜索 HN 讨论"""
        searcher = HNSearcher()
        stories = searcher.search_stories(topic, max_results=self.max_discussions)
        return stories

    def _search_docs(self, topic: str) -> list[dict]:
        """搜索文档库"""
        docs = search_docs(topic, max_results=self.max_docs)
        return docs

    def _search_web(self, topic: str) -> list[dict]:
        """搜索 Web 文章（Google 优先 → Bing 降级 → DuckDuckGo 兜底）"""
        searcher = WebSearcher(
            google_api_key=self.google_api_key,
            google_cx=self.google_cx,
            bing_api_key=self.bing_api_key,
        )
        try:
            articles = searcher.search_articles(topic, max_results=self.max_articles)
        except Exception as e:
            logger.warning("Web 搜索失败: %s", e)
            articles = []
        return articles

    def _search_wechat(self, topic: str) -> list[dict]:
        """搜索本地公众号文章（content.db）"""
        searcher = WechatSearcher()
        return searcher.search_articles(topic, max_results=self.max_articles)

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
        return normalized
