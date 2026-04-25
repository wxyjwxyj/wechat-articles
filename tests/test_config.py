"""utils/config.py 测试：环境变量优先、config.json 降级、缺失文件兜底。"""
import json
from unittest.mock import patch

from utils.config import get_claude_config


def test_get_claude_config_env_takes_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env.example.com")

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"claude_api_key": "file-key", "claude_base_url": "https://file.example.com"}))

    with patch("utils.config.CONFIG_PATH", cfg_file):
        api_key, base_url = get_claude_config()

    assert api_key == "env-key"
    assert base_url == "https://env.example.com"


def test_get_claude_config_falls_back_to_file(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"claude_api_key": "file-key", "claude_base_url": "https://file.example.com"}))

    with patch("utils.config.CONFIG_PATH", cfg_file):
        api_key, base_url = get_claude_config()

    assert api_key == "file-key"
    assert base_url == "https://file.example.com"


def test_get_claude_config_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

    with patch("utils.config.CONFIG_PATH", tmp_path / "nonexistent.json"):
        api_key, base_url = get_claude_config()

    assert api_key == ""
    assert base_url == "https://api.anthropic.com"
