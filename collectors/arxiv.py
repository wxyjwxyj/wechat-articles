"""ArXiv 论文采集器。

使用 ArXiv API（免费，无需认证）采集 AI 相关最新论文。
支持按分类筛选（cs.AI、cs.CL、cs.CV、cs.LG 等）。
返回 Atom XML，用标准库 xml.etree 解析。
"""
import random
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

import requests

from utils.errors import CollectorError
from utils.http import retry_session
from utils.log import get_logger

logger = get_logger(__name__)

ARXIV_API = "https://export.arxiv.org/api/query"

# ArXiv 命名空间
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# AI 相关分类
AI_CATEGORIES = [
    "cs.AI",   # 人工智能
    "cs.CL",   # 计算语言学（NLP）
    "cs.CV",   # 计算机视觉
    "cs.LG",   # 机器学习
    "cs.MA",   # 多智能体系统
    "cs.RO",   # 机器人学（AI 相关）
    "stat.ML", # 统计机器学习
]

# 高价值关键词（标题匹配，用于加分排序）
HIGH_VALUE_KEYWORDS = [
    "llm", "large language model", "gpt", "claude", "gemini",
    "transformer", "attention", "agent", "reasoning",
    "rlhf", "rag", "retrieval", "fine-tun", "alignment",
    "diffusion", "multimodal", "vision-language",
    "benchmark", "scaling", "emergent",
    "deepseek", "llama", "mistral", "qwen",
    "world model",
    "mythos",
    "multimodal vision",
    "embodied world model",
    "mixture of experts",
]


def _build_query(categories: list[str]) -> str:
    """构建 ArXiv API 的分类查询字符串。

    例：cat:cs.AI OR cat:cs.CL OR cat:cs.LG
    """
    return " OR ".join(f"cat:{cat}" for cat in categories)


def _parse_entry(entry: ET.Element) -> dict:
    """解析单条 Atom entry 为论文字典。"""
    # 标题（去掉换行）
    title = (entry.findtext("atom:title", "", NS) or "").replace("\n", " ").strip()
    title = " ".join(title.split())  # 折叠多余空格

    # 摘要
    summary = (entry.findtext("atom:summary", "", NS) or "").strip()
    summary = " ".join(summary.split())

    # ArXiv ID（从 <id> 提取）
    arxiv_id_url = entry.findtext("atom:id", "", NS) or ""
    arxiv_id = arxiv_id_url.split("/abs/")[-1] if "/abs/" in arxiv_id_url else ""

    # URL
    url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else arxiv_id_url

    # PDF URL
    pdf_url = ""
    for link in entry.findall("atom:link", NS):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    # 发布时间
    published = entry.findtext("atom:published", "", NS) or ""

    # 作者列表
    authors = []
    for author_elem in entry.findall("atom:author", NS):
        name = author_elem.findtext("atom:name", "", NS)
        if name:
            authors.append(name.strip())

    # 分类列表
    categories = []
    for cat_elem in entry.findall("atom:category", NS):
        term = cat_elem.get("term", "")
        if term:
            categories.append(term)

    # 主分类
    primary_cat_elem = entry.find("arxiv:primary_category", NS)
    primary_category = primary_cat_elem.get("term", "") if primary_cat_elem is not None else ""

    # 评论（如 "Accepted at ICML 2026"）
    comment = entry.findtext("arxiv:comment", "", NS) or ""

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "summary": summary,
        "url": url,
        "pdf_url": pdf_url,
        "published": published,
        "authors": authors,
        "categories": categories,
        "primary_category": primary_category,
        "comment": comment,
    }


def _relevance_score(paper: dict) -> int:
    """基于标题关键词给论文一个相关度分数（用于排序）。"""
    title_lower = paper["title"].lower()
    score = 0
    for kw in HIGH_VALUE_KEYWORDS:
        if kw in title_lower:
            score += 2
    # 主分类是 AI 核心领域加分
    if paper.get("primary_category") in ("cs.AI", "cs.CL", "cs.LG"):
        score += 1
    # 被会议接收加分
    comment_lower = paper.get("comment", "").lower()
    if any(conf in comment_lower for conf in ["accepted", "icml", "neurips", "iclr", "acl", "emnlp", "cvpr", "eccv"]):
        score += 3
    return score


class ArxivCollector:
    """ArXiv AI 论文采集器。"""

    def __init__(
        self,
        categories: list[str] | None = None,
        max_results: int = 30,
        max_papers: int = 10,
        days_back: int = 2,
        timeout: int = 60,
    ):
        """
        Args:
            categories: 要查询的分类列表，默认 AI_CATEGORIES
            max_results: API 单次返回最大条数（用于候选池）
            max_papers: 最终返回的论文数上限
            days_back: 只保留最近 N 天的论文
            timeout: HTTP 请求超时秒数
        """
        self.categories = categories or AI_CATEGORIES
        self.max_results = max_results
        self.max_papers = max_papers
        self.days_back = days_back
        self.timeout = timeout
        # ArXiv 限流恢复慢，用更长退避（10s/20s/40s，最多60s）
        self._session = retry_session(retries=5, backoff=10.0, backoff_max=60.0)

    def fetch_recent_papers(self) -> list[dict]:
        """采集最近的 AI 论文。

        Raises:
            CollectorError: API 请求失败

        Returns:
            论文列表，每项包含 arxiv_id, title, summary, url, pdf_url,
            published, authors, categories, primary_category, comment, score
        """
        query = _build_query(self.categories)
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        logger.info("查询 ArXiv: %s (max_results=%d)", query[:60], self.max_results)

        # 随机 jitter 避免与其他采集线程同时请求被限流
        jitter = random.uniform(2, 8)
        logger.debug("ArXiv jitter: %.1fs", jitter)
        time.sleep(jitter)

        # 冷启动时 ArXiv 经常第一次超时，加应用层重试（最多 3 次，间隔 30s）
        for attempt in range(3):
            try:
                resp = self._session.get(ARXIV_API, params=params, timeout=self.timeout)
                resp.raise_for_status()
                break
            except requests.Timeout as e:
                if attempt < 2:
                    logger.warning("ArXiv 请求超时（第 %d 次），30s 后重试", attempt + 1)
                    time.sleep(30)
                else:
                    logger.warning("ArXiv 超时重试耗尽: %s", str(e)[:120])
                    raise CollectorError(f"ArXiv API 请求失败: {e}") from e
            except requests.RequestException as e:
                err_str = str(e)
                if "429" in err_str or "too many" in err_str.lower():
                    logger.warning("ArXiv 429 限流，重试已耗尽（backoff 最大 60s × 5次）: %s", err_str[:120])
                else:
                    logger.warning("ArXiv 请求失败: %s", err_str[:120])
                raise CollectorError(f"ArXiv API 请求失败: {e}") from e

        # 解析 XML
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            raise CollectorError(f"ArXiv XML 解析失败: {e}") from e

        entries = root.findall("atom:entry", NS)
        if not entries:
            logger.info("ArXiv 返回 0 条结果")
            return []

        logger.info("ArXiv 返回 %d 条候选论文", len(entries))

        # 解析所有论文
        papers = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.days_back)

        for entry in entries:
            paper = _parse_entry(entry)

            # 日期过滤：只保留最近 N 天
            try:
                pub_dt = datetime.fromisoformat(paper["published"].replace("Z", "+00:00"))
                if pub_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                continue

            # 计算相关度分数
            paper["score"] = _relevance_score(paper)
            papers.append(paper)

        # 按相关度分数降序排列
        papers.sort(key=lambda x: x["score"], reverse=True)

        # 取 top N
        result = papers[:self.max_papers]
        logger.info("筛选后保留 %d 篇（共 %d 篇候选，%d 天内）",
                     len(result), len(papers), self.days_back)

        return result

    def search_by_keyword(self, query: str, max_results: int = 10) -> list[dict]:
        """按关键词搜索 ArXiv 论文。

        Args:
            query: 搜索关键词（支持中英文，会在标题和摘要中搜索）
            max_results: 最多返回条数

        Raises:
            CollectorError: API 请求失败

        Returns:
            论文列表，格式同 fetch_recent_papers()
        """
        # 构建搜索查询：在标题或摘要中搜索关键词
        search_query = f"ti:{query} OR abs:{query}"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",  # 按相关度排序
            "sortOrder": "descending",
        }

        logger.info("ArXiv 关键词搜索: %s (max_results=%d)", query, max_results)

        try:
            resp = self._session.get(ARXIV_API, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CollectorError(f"ArXiv API 请求失败: {e}") from e

        # 解析 XML
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            raise CollectorError(f"ArXiv XML 解析失败: {e}") from e

        entries = root.findall("atom:entry", NS)
        if not entries:
            logger.info("ArXiv 关键词搜索返回 0 条结果")
            return []

        logger.info("ArXiv 关键词搜索返回 %d 条结果", len(entries))

        # 解析所有论文
        papers = []
        for entry in entries:
            paper = _parse_entry(entry)
            paper["score"] = _relevance_score(paper)
            papers.append(paper)

        return papers
