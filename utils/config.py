"""统一配置读取：敏感字段优先从环境变量获取，降级读 config.json。"""
import json
import os
import logging
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

logger = logging.getLogger(__name__)


def _load_config_file() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("config.json 不存在，请复制 config.example.json 并填写")
        return {}
    except json.JSONDecodeError as e:
        logger.error("config.json 格式错误: %s", e)
        return {}


def load_project_config() -> dict:
    """加载并校验项目配置，缺少必要字段时记录警告。"""
    cfg = _load_config_file()
    if not cfg.get("cdp_proxy"):
        logger.warning("config.json 缺少 cdp_proxy，将使用默认值 http://localhost:3456")
        cfg.setdefault("cdp_proxy", "http://localhost:3456")
    return cfg


def get_claude_config() -> tuple[str, str]:
    """返回 (api_key, base_url)，环境变量优先。"""
    cfg = _load_config_file()
    api_key = os.getenv("ANTHROPIC_API_KEY") or cfg.get("claude_api_key", "")
    base_url = os.getenv("ANTHROPIC_BASE_URL") or cfg.get("claude_base_url", "https://api.anthropic.com")
    return api_key, base_url
