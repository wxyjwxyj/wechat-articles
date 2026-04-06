from unittest.mock import patch, MagicMock
from research.web_search import WebSearcher


def test_search_articles_tries_google_first():
    """应优先尝试 Google Search"""
    searcher = WebSearcher(google_api_key="test-google", google_cx="test-cx")

    with patch('research.web_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        searcher.search_articles("强化学习")

        # 验证调用的是 Google API
        call_args = mock_get.call_args
        assert "googleapis.com" in call_args[0][0]


def test_search_articles_fallback_to_bing():
    """Google 失败时应降级到 Bing"""
    searcher = WebSearcher(
        google_api_key="test-google",
        google_cx="test-cx",
        bing_api_key="test-bing"
    )

    with patch('research.web_search.requests.get') as mock_get:
        # Google 失败
        def side_effect(url, *args, **kwargs):
            if "googleapis.com" in url:
                raise Exception("Google API error")
            # Bing 成功
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"webPages": {"value": []}}
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        mock_get.side_effect = side_effect

        results = searcher.search_articles("test")

        # 应该调用了两次（Google 失败 + Bing 成功）
        assert mock_get.call_count == 2


def test_search_articles_returns_google_results():
    """应返回 Google 搜索结果"""
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

    with patch('research.web_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = searcher.search_articles("强化学习")

        assert len(results) == 1
        assert results[0]["title"] == "强化学习入门教程"


def test_search_articles_returns_bing_results():
    """应返回 Bing 搜索结果"""
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

    with patch('research.web_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = searcher.search_articles("强化学习")

        assert len(results) == 1
        assert results[0]["title"] == "强化学习入门教程"


def test_search_articles_handles_no_api_key():
    """未配置 API key 应抛出异常"""
    from utils.errors import CollectorError

    searcher = WebSearcher()

    try:
        searcher.search_articles("test")
        assert False, "应该抛出异常"
    except CollectorError as e:
        assert "API key" in str(e)


def test_search_articles_prefers_chinese_content():
    """应优先返回中文内容"""
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

    with patch('research.web_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = searcher.search_articles("强化学习")

        # 中文内容应该排在前面
        assert "中文" in results[0]["snippet"]
