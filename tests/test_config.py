"""utils/config.py 测试：环境变量 → cc-switch → config.json 优先级。"""
import json
from unittest.mock import patch

from utils.config import get_claude_config

MOCK_CC_EMPTY = patch("utils.config._load_cc_switch_config", return_value={})


def test_env_takes_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env.example.com")
    monkeypatch.setenv("ANTHROPIC_MODEL", "env-model")

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"claude_api_key": "file-key"}))

    with patch("utils.config.CONFIG_PATH", cfg_file), MOCK_CC_EMPTY:
        api_key, base_url, model = get_claude_config()

    assert api_key == "env-key"
    assert base_url == "https://env.example.com"
    assert model == "env-model"


def test_cc_switch_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    cc_data = {"api_key": "cc-key", "base_url": "https://cc.example.com", "model": "cc-model"}

    with patch("utils.config.CONFIG_PATH", tmp_path / "nonexistent.json"), \
         patch("utils.config._load_cc_switch_config", return_value=cc_data):
        api_key, base_url, model = get_claude_config()

    assert api_key == "cc-key"
    assert base_url == "https://cc.example.com"
    assert model == "cc-model"


def test_file_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"claude_api_key": "file-key", "claude_base_url": "https://file.example.com", "claude_model": "file-model"}))

    with patch("utils.config.CONFIG_PATH", cfg_file), MOCK_CC_EMPTY:
        api_key, base_url, model = get_claude_config()

    assert api_key == "file-key"
    assert base_url == "https://file.example.com"
    assert model == "file-model"


def test_all_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    with patch("utils.config.CONFIG_PATH", tmp_path / "nonexistent.json"), MOCK_CC_EMPTY:
        api_key, base_url, model = get_claude_config()

    assert api_key == ""
    assert base_url == ""
    assert model == ""
