"""统一 Claude API 调用入口。

fallback 链：haiku → sonnet → opus，日常任务用最便宜的，失败逐级升级。
所有模块通过 claude_call() / claude_stream() / get_client() 调用，
不要直接创建 anthropic.Anthropic client。
"""
import logging
import time
import anthropic

from utils.config import get_claude_config

logger = logging.getLogger(__name__)

# fallback 顺序：快→强
MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
]


def get_client() -> anthropic.Anthropic:
    """返回配置好的 Anthropic client，供需要复用 client 的场景使用。"""
    api_key, base_url = get_claude_config()
    return anthropic.Anthropic(api_key=api_key, base_url=base_url)


def claude_call(
    prompt: str,
    *,
    max_tokens: int = 1024,
    model: str | None = None,
) -> str:
    """发送单轮对话，返回文本响应。

    Args:
        prompt: 用户消息内容
        max_tokens: 最大输出 token 数
        model: 指定模型则直接用，不走 fallback

    Returns:
        模型返回的文本，所有模型都失败时抛出最后一个异常
    """
    client = get_client()
    models = [model] if model else MODELS

    last_err = None
    for m in models:
        for attempt in range(3):
            try:
                msg = client.messages.create(
                    model=m,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                if m != models[0]:
                    logger.info("claude_call: fallback 到 %s 成功", m)
                return msg.content[0].text
            except anthropic.RateLimitError:
                if attempt < 2:
                    wait = 2 ** (attempt + 1)
                    logger.warning("claude_call: %s 限流，%ds 后重试", m, wait)
                    time.sleep(wait)
                    continue
                logger.warning("claude_call: %s 限流 3 次，尝试下一个模型", m)
                last_err = anthropic.RateLimitError("rate limit exceeded")
                break
            except Exception as e:
                logger.warning("claude_call: %s 失败（%s），尝试下一个模型", m, e)
                last_err = e
                break

    raise last_err


def claude_stream(
    prompt: str,
    *,
    max_tokens: int = 8192,
    model: str = "claude-opus-4-6",
):
    """流式输出，返回 context manager，用法：

    with claude_stream(prompt) as stream:
        for text in stream.text_stream:
            ...
    """
    client = get_client()
    return client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
