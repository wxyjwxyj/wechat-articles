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
            f"{i+1}. 标题：{r.get('title', '')}  简介：{r.get('summary', '')[:150]}"
            for i, r in enumerate(resources)
        )

        topic_line = f"用户搜索的主题是：**{topic}**\n\n" if topic else ""

        prompt = f"""你是一个技术学习资源评估专家。请为以下每个资源打分（1-10分）并写一句中文点评。

{topic_line}评分标准：
- 9-10分：权威一手资料（顶会论文、官方文档、经典教程），且与主题高度相关
- 7-8分：高质量学习资源（优秀开源项目、深度技术文章），且与主题相关
- 5-6分：普通资源（一般质量的教程、博客），与主题有一定关联
- 3-4分：质量较低（过时内容、浅显介绍）
- 1-2分：不推荐（广告、无关内容）

⚠️ 重要：如果资源与搜索主题"{topic}"不直接相关，无论质量多高，都必须打 1-2 分。

资源列表：
{resources_text}

要求：
- 点评简洁（10-20字），说明为什么值得学习
- 严格按 JSON 格式返回，不要有任何其他文字

返回格式：
{{"results": [{{"id": 1, "score": 8, "comment": "PyTorch官方文档，权威全面"}}, ...]}}"""

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
                raise AIApiError("Claude 返回格式错误：未找到 JSON")

            data = json.loads(raw[start:end])
            results = data.get("results", [])

            logger.info("Claude 评分完成：%d 个资源", len(results))

        except anthropic.APIError as e:
            raise AIApiError(f"Claude API 调用失败: {e}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise AIApiError(f"Claude 返回解析失败: {e}") from e
        except Exception as e:
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
