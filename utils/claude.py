"""统一 Claude API 调用入口。

模型、API Key、Base URL 均从 .env / config.json 读取，换代理只改配置不改代码。
所有模块通过 claude_call() / claude_stream() / get_client() 调用，
不要直接创建 anthropic.Anthropic client。
"""
import json
import logging
import re
import time
import anthropic
from anthropic.types import TextBlock, ThinkingBlock

from utils.config import get_claude_config

logger = logging.getLogger(__name__)


def _strip_markdown_code_block(raw: str) -> str:
    """去除 markdown 代码块包裹（支持多个代码块，逐行过滤）。"""
    lines = raw.strip().splitlines()
    cleaned = [
        line for line in lines
        if not re.match(r'^\s*```(?:json)?\s*$', line)
    ]
    return "\n".join(cleaned)


def _find_last_json_object(text: str) -> tuple[int, int]:
    """在文本中找到最后一个完整的 JSON 对象的 (start, end) 位置。

    从后往前扫描，用括号深度匹配找到正确的 {…} 对。
    """
    end = text.rfind("}")
    if end == -1:
        return -1, -1
    depth = 0
    for i in range(end, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            depth -= 1
            if depth == 0:
                return i, end + 1
    return -1, -1


def extract_json(raw: str) -> dict:
    """从 Claude 响应中提取最后一个 JSON 对象，处理 markdown 代码块包裹。"""
    cleaned = _strip_markdown_code_block(raw)
    start, end = _find_last_json_object(cleaned)
    if start == -1:
        raise ValueError(f"无 JSON 对象: {raw[:100]}")
    return json.loads(cleaned[start:end])


def _find_last_json_array(text: str) -> tuple[int, int]:
    """在文本中找到最后一个完整的 JSON 数组的 (start, end) 位置。"""
    end = text.rfind("]")
    if end == -1:
        return -1, -1
    depth = 0
    for i in range(end, -1, -1):
        if text[i] == "]":
            depth += 1
        elif text[i] == "[":
            depth -= 1
            if depth == 0:
                return i, end + 1
    return -1, -1


def extract_json_array(raw: str) -> list:
    """从 Claude 响应中提取最后一个 JSON 数组，处理 markdown 代码块包裹。"""
    cleaned = _strip_markdown_code_block(raw)
    start, end = _find_last_json_array(cleaned)
    if start == -1:
        raise ValueError(f"无 JSON 数组: {raw[:100]}")
    return json.loads(cleaned[start:end])


def get_client() -> anthropic.Anthropic:
    """返回配置好的 Anthropic client，供需要复用 client 的场景使用。"""
    api_key, base_url, _ = get_claude_config()
    return anthropic.Anthropic(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    """返回当前配置的模型名，未配置则报错。"""
    _, _, model = get_claude_config()
    if not model:
        raise RuntimeError("未配置 ANTHROPIC_MODEL，请在 .env 中设置")
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
            # 取第一个 TextBlock
            for block in msg.content:
                if isinstance(block, TextBlock):
                    return block.text
            # 兜底：无 TextBlock 时尝试从 ThinkingBlock 提取
            for block in msg.content:
                if isinstance(block, ThinkingBlock) and block.thinking:
                    logger.debug("claude_call: 无 TextBlock，从 ThinkingBlock 提取")
                    return block.thinking
            return ""
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
