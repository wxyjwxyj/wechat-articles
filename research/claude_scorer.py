"""Claude 评分器，为学习资料打分并生成点评。"""
import json
import anthropic
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
    ):
        """
        Args:
            api_key: Anthropic API key
            base_url: API base URL
            model: 使用的模型
            min_score: 最低分数阈值（低于此分数的资源会被过滤）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.min_score = min_score

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

        # 构建批量评分 prompt
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
            client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            message = client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()

            # 提取 JSON
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                logger.warning("评分原始响应（未找到JSON）: %s", raw[:300])
                raise AIApiError("Claude 返回格式错误：未找到 JSON")

            data = json.loads(raw[start:end])
            results = data.get("results", [])

            logger.info("Claude 评分完成：%d 个资源", len(results))

        except anthropic.APIError as e:
            raise AIApiError(f"Claude API 调用失败: {e}") from e
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("评分解析失败，原始响应: %s", raw[:300])
            raise AIApiError(f"Claude 返回解析失败: {e}") from e
        except Exception as e:
            logger.warning("评分异常，原始响应: %s", raw[:300])
            raise AIApiError(f"评分过程出错: {e}") from e

        # 合并评分结果到原资源
        scored_resources = []
        for r in results:
            idx = r.get("id", 0) - 1
            if 0 <= idx < len(resources):
                score = int(r.get("score", 0))
                if score >= self.min_score:
                    resource = resources[idx].copy()
                    resource["score"] = score
                    resource["comment"] = r.get("comment", "")
                    scored_resources.append(resource)

        logger.info("过滤后保留 %d 个资源（>= %d 分）", len(scored_resources), self.min_score)
        return scored_resources
