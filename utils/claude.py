"""统一 Claude API 调用入口。

模型、API Key、Base URL 均从 .env / config.json 读取，换代理只改配置不改代码。
所有模块通过 claude_call() / claude_stream() / get_client() 调用，
不要直接创建 anthropic.Anthropic client。
"""
import logging
import time
import anthropic
from anthropic.types import TextBlock

from utils.config import get_claude_config

logger = logging.getLogger(__name__)


def get_client() -> anthropic.Anthropic:
    """返回配置好的 Anthropic client，供需要复用 client 的场景使用。"""
    api_key, base_url, _ = get_claude_config()
    return anthropic.Anthropic(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    """返回当前配置的模型名。"""
    _, _, model = get_claude_config()
    return model


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
    m = model or _get_model()

    last_err = None
    for attempt in range(3):
        try:
            msg = client.messages.create(
                model=m,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            # 跳过 ThinkingBlock，取第一个 TextBlock
            for block in msg.content:
                if isinstance(block, TextBlock):
                    return block.text
            # 兜底：直接拼所有块的文本
            return "".join(getattr(b, "text", "") for b in msg.content)
        except anthropic.RateLimitError as e:
            if attempt < 2:
                wait = 2 ** (attempt + 1)
                logger.warning("claude_call: %s 限流，%ds 后重试", m, wait)
                time.sleep(wait)
                continue
            logger.warning("claude_call: %s 限流 3 次，放弃", m)
            last_err = e
            break
        except Exception as e:
            logger.warning("claude_call: %s 失败（%s）", m, e)
            last_err = e
            break

    raise last_err


def claude_stream(
    prompt: str,
    *,
    max_tokens: int = 8192,
    model: str | None = None,
):
    """流式输出，返回 context manager，用法：

    with claude_stream(prompt) as stream:
        for text in stream.text_stream:
            ...
    """
    client = get_client()
    return client.messages.stream(
        model=model or _get_model(),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
