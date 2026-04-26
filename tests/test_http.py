"""utils/http.py 测试：retry_session 重试逻辑。"""
from unittest.mock import patch, MagicMock
import requests
from requests.adapters import HTTPAdapter

from utils.http import retry_session


def test_retry_session_returns_session():
    """返回的是 requests.Session 实例。"""
    s = retry_session()
    assert isinstance(s, requests.Session)


def test_retry_session_configures_adapter():
    """HTTP/HTTPS 都挂载了带重试的 adapter。"""
    s = retry_session(retries=5, backoff=2.0, backoff_max=60.0)
    for prefix in ("http://", "https://"):
        adapter = s.get_adapter(f"{prefix}example.com")
        assert isinstance(adapter, HTTPAdapter)
        assert adapter.max_retries.total == 5
        assert adapter.max_retries.backoff_factor == 2.0
        assert adapter.max_retries.backoff_max == 60.0


def test_retry_session_status_forcelist():
    """重试覆盖 429/5xx 状态码。"""
    s = retry_session()
    adapter = s.get_adapter("https://example.com")
    forcelist = adapter.max_retries.status_forcelist
    assert 429 in forcelist
    assert 500 in forcelist
    assert 502 in forcelist
    assert 503 in forcelist
    assert 504 in forcelist


def test_retry_session_allowed_methods():
    """只对 GET/POST 重试。"""
    s = retry_session()
    adapter = s.get_adapter("https://example.com")
    assert "GET" in adapter.max_retries.allowed_methods
    assert "POST" in adapter.max_retries.allowed_methods


def test_retry_session_pool_maxsize():
    """连接池大小可配置。"""
    s = retry_session(pool_maxsize=50)
    adapter = s.get_adapter("https://example.com")
    assert adapter._pool_maxsize == 50


def test_retry_session_default_values():
    """默认参数：3次重试，backoff=1.0，max=120。"""
    s = retry_session()
    adapter = s.get_adapter("https://example.com")
    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 1.0
    assert adapter.max_retries.backoff_max == 120.0
