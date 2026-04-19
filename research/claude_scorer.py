"""Claude 评分器，为学习资料打分并生成点评。"""
import json
from contextlib import closing
from pathlib import Path
from utils.errors import AIApiError
from utils.log import get_logger

logger = get_logger(__name__)


class ClaudeScorer:
    """Claude 资源评分器。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-6",
        min_score: int = 6,
        db_path: Path | str | None = None,
    ):
        """
        Args:
            api_key: Anthropic API key
            base_url: API base URL
            model: 使用的模型
            min_score: 最低分数阈值（低于此分数的资源会被过滤）
            db_path: SQLite 数据库路径，用于评分缓存；为 None 则不缓存
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.min_score = min_score
        self.db_path = db_path
        if db_path:
            self._ensure_cache_table(db_path)

    def _ensure_cache_table(self, db_path: Path | str) -> None:
        """确保缓存表存在。"""
        from storage.db import get_connection, init_db
        init_db(db_path)

    def _get_cached_scores(self, urls: list[str], topic: str) -> dict[str, dict]:
        """从缓存中批量查询评分结果，返回 {url: {score, comment}} 字典。"""
        if not self.db_path or not urls:
            return {}
        from storage.db import get_connection
        placeholders = ",".join("?" * len(urls))
        with closing(get_connection(self.db_path)) as conn:
            rows = conn.execute(
                f"select url, score, comment from research_score_cache "
                f"where url in ({placeholders}) and topic = ?",
                (*urls, topic),
            ).fetchall()
        return {row["url"]: {"score": row["score"], "comment": row["comment"]} for row in rows}

    def _save_scores_to_cache(self, scored: list[dict], topic: str) -> None:
        """将评分结果批量写入缓存。"""
        if not self.db_path or not scored:
            return
        from storage.db import get_connection
        rows = [
            (r.get("url", ""), topic, r["score"], r.get("comment", ""))
            for r in scored
            if r.get("url")
        ]
        if not rows:
            return
        with closing(get_connection(self.db_path)) as conn:
            with conn:
                conn.executemany(
                    "insert or replace into research_score_cache (url, topic, score, comment) values (?, ?, ?, ?)",
                    rows,
                )

    def score_resources(self, resources: list[dict], topic: str = "") -> list[dict]:
        """为资源列表打分并生成点评。

        Args:
            resources: 资源列表，每项需包含 title 和 summary 字段
            topic: 搜索主题，用于判断相关性（如"强化学习"、"Agent"）

        Raises:
            AIApiError: Claude API 调用失败

        Returns:
            评分后的资源列表，每项新增 score 和 comment 字段
            只返回 score >= min_score 的资源
        """
        if not resources:
            return []

        # 查缓存：已有评分的直接复用（空 url 的资源不参与缓存）
        urls = [r.get("url", "") for r in resources if r.get("url")]
        cached = self._get_cached_scores(urls, topic)
        cache_hits = len(cached)
        if cache_hits:
            logger.info("评分缓存命中 %d/%d 条", cache_hits, len(resources))

        # 分离：需要调 Claude 的 vs 缓存命中的（无 url 的资源也归入 to_score）
        to_score = [r for r in resources if not cached.get(r.get("url", ""))]
        from_cache = [r for r in resources if cached.get(r.get("url", ""))]

        # 缓存命中的直接合并评分
        cached_results = []
        for r in from_cache:
            c = cached[r["url"]]
            if c["score"] >= self.min_score:
                resource = r.copy()
                resource["score"] = c["score"]
                resource["comment"] = c["comment"]
                cached_results.append(resource)

        if not to_score:
            return cached_results

        # 未命中的批量送 Claude 评分（_call_claude 内部会写缓存）
        scored_from_claude = self._call_claude(to_score, topic)

        return cached_results + scored_from_claude

    def _call_claude(self, resources: list[dict], topic: str) -> list[dict]:
        """调用 Claude 对资源列表评分，返回 score >= min_score 的结果。"""
        resources_text = "\n".join(
            f"{i+1}. Title: {r.get('title', '')}  Summary: {r.get('summary', '')[:150]}"
            for i, r in enumerate(resources)
        )

        topic_line = f"The user is searching for: {topic}\n\n" if topic else ""

        prompt = f"""You are a technical learning resource evaluator. Score each resource (1-10) and write a brief Chinese comment.

{topic_line}Scoring criteria:
- 9-10: Authoritative primary sources (top conference papers, official docs, classic tutorials), highly relevant to topic
- 7-8: High-quality resources (excellent open source projects, in-depth technical articles), relevant to topic
- 5-6: Average resources (general tutorials, blogs), somewhat related to topic
- 3-4: Low quality (outdated content, superficial introductions)
- 1-2: Not recommended (ads, irrelevant content)

Important: If a resource is not directly related to the topic "{topic}", score it 1-2 regardless of quality.

Resources:
{resources_text}

Requirements:
- Comment should be concise (10-20 Chinese characters), explain why it's worth learning
- Return strictly in JSON format, no other text

Format:
{{"results": [{{"id": 1, "score": 8, "comment": "PyTorch官方文档，权威全面"}}, ...]}}"""

        raw = ""
        try:
            from utils.claude import claude_call
            raw = claude_call(prompt, max_tokens=2048, model=self.model)

            # 提取 JSON
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                logger.warning("评分原始响应（未找到JSON）: %s", raw[:300])
                raise AIApiError("Claude 返回格式错误：未找到 JSON")

            data = json.loads(raw[start:end])
            results = data.get("results", [])

            logger.info("Claude 评分完成：%d 个资源", len(results))

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("评分解析失败，原始响应: %s", raw[:300])
            raise AIApiError(f"Claude 返回解析失败: {e}") from e
        except Exception as e:
            logger.warning("评分异常，原始响应: %s", raw[:300])
            raise AIApiError(f"评分过程出错: {e}") from e

        # 合并评分结果到原资源，先收集全部（含低分），再过滤
        all_scored = []
        for r in results:
            idx = r.get("id", 0) - 1
            if 0 <= idx < len(resources):
                score = int(r.get("score", 0))
                resource = resources[idx].copy()
                resource["score"] = score
                resource["comment"] = r.get("comment", "")
                all_scored.append(resource)

        # 写缓存（含低分，避免重复调用 Claude）
        self._save_scores_to_cache(all_scored, topic)

        scored_resources = [r for r in all_scored if r["score"] >= self.min_score]
        logger.info("过滤后保留 %d 个资源（>= %d 分）", len(scored_resources), self.min_score)
        return scored_resources
