from unittest.mock import patch, MagicMock
from research.web_search import WebSearcher


EXA_OUTPUT = """Title: AI Agent Tutorial
URL: https://example.com/agent
Published: 2025-01-01
Author: N/A
Highlights:
This is a tutorial about AI agents.

Title: 强化学习入门教程
URL: https://juejin.cn/post/123
Published: 2025-02-01
Author: N/A
Highlights:
这是一篇中文教程，介绍强化学习的基本概念。
"""


def _mock_exa_run(returncode=0, stdout=EXA_OUTPUT, stderr=""):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


def test_search_articles_tries_exa_first():
    """应优先尝试 Exa Search"""
    searcher = WebSearcher(google_api_key="test-google", google_cx="test-cx")

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run()) as mock_run:
        results = searcher.search_articles("AI agent")
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert "exa" in " ".join(cmd)
        assert len(results) == 2


def test_search_articles_fallback_to_google_when_exa_fails():
    """Exa 失败时应降级到 Google"""
    searcher = WebSearcher(google_api_key="test-google", google_cx="test-cx")

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run(returncode=1, stdout="")):
        with patch('research.web_search.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"items": []}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            searcher.search_articles("强化学习")
            call_args = mock_get.call_args
            assert "googleapis.com" in call_args[0][0]


def test_search_articles_returns_exa_results():
    """应正确解析并返回 Exa 搜索结果"""
    searcher = WebSearcher()

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run()):
        results = searcher.search_articles("AI agent")

    assert len(results) == 2
    assert results[0]["title"] == "AI Agent Tutorial"
    assert results[0]["url"] == "https://example.com/agent"
    assert "tutorial" in results[0]["snippet"].lower()


def test_search_articles_returns_google_results():
    """Exa 失败时应返回 Google 搜索结果"""
    searcher = WebSearcher(google_api_key="test-google", google_cx="test-cx")

    mock_json = {
        "items": [
            {
                "title": "强化学习入门教程",
                "link": "https://example.com/rl-tutorial",
                "snippet": "本文介绍强化学习的基本概念...",
            }
        ]
    }

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run(returncode=1, stdout="")):
        with patch('research.web_search.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_json
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            results = searcher.search_articles("强化学习")

    assert len(results) == 1
    assert results[0]["title"] == "强化学习入门教程"


def test_search_articles_returns_bing_results():
    """Exa 和 Google 都失败时应返回 Bing 搜索结果"""
    searcher = WebSearcher(bing_api_key="test-bing")

    mock_json = {
        "webPages": {
            "value": [
                {
                    "name": "强化学习入门教程",
                    "url": "https://example.com/rl-tutorial",
                    "snippet": "本文介绍强化学习的基本概念...",
                }
            ]
        }
    }

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run(returncode=1, stdout="")):
        with patch('research.web_search.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_json
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            results = searcher.search_articles("强化学习")

    assert len(results) == 1
    assert results[0]["title"] == "强化学习入门教程"


def test_search_articles_prefers_chinese_content_in_google_fallback():
    """Google 降级时应优先返回中文内容"""
    searcher = WebSearcher(google_api_key="test-google", google_cx="test-cx")

    mock_json = {
        "items": [
            {
                "title": "Reinforcement Learning Tutorial",
                "link": "https://example.com/en",
                "snippet": "This is an English tutorial...",
            },
            {
                "title": "强化学习教程",
                "link": "https://juejin.cn/post/123",
                "snippet": "这是一篇中文教程...",
            }
        ]
    }

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run(returncode=1, stdout="")):
        with patch('research.web_search.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_json
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            results = searcher.search_articles("强化学习")

    assert "中文" in results[0]["snippet"]


def test_search_articles_fallback_to_ddg_when_all_fail():
    """Exa/Google/Bing 都失败时降级到 DuckDuckGo，不抛异常"""
    searcher = WebSearcher()

    mock_ddgs = MagicMock()
    mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text = MagicMock(return_value=[])

    with patch('research.web_search.subprocess.run', return_value=_mock_exa_run(returncode=1, stdout="")):
        with patch('ddgs.DDGS', return_value=mock_ddgs):
            results = searcher.search_articles("test")

    assert isinstance(results, list)
