from unittest.mock import patch, MagicMock
from research.hn_search import HNSearcher


def test_search_stories_builds_correct_url():
    """应构建正确的 HN Algolia API URL"""
    searcher = HNSearcher()

    with patch('research.hn_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"hits": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        searcher.search_stories("reinforcement learning", max_results=5)

        call_args = mock_get.call_args
        assert "hn.algolia.com/api/v1/search" in call_args[0][0]
        params = call_args[1]['params']
        assert params['query'] == "reinforcement learning"
        assert params['tags'] == "story"


def test_search_stories_returns_results():
    """应返回搜索结果列表"""
    searcher = HNSearcher()

    mock_json = {
        "hits": [
            {
                "objectID": "12345",
                "title": "Deep RL breakthrough",
                "url": "https://example.com/article",
                "points": 350,
                "num_comments": 120,
                "created_at": "2024-01-15T10:00:00Z",
                "author": "testuser",
            }
        ]
    }

    with patch('research.hn_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = searcher.search_stories("reinforcement learning")

        assert len(results) == 1
        assert results[0]["title"] == "Deep RL breakthrough"
        assert results[0]["score"] == 350


def test_search_stories_handles_api_error():
    """API 错误应抛出 CollectorError"""
    from utils.errors import CollectorError

    searcher = HNSearcher()

    with patch('research.hn_search.requests.get') as mock_get:
        mock_get.side_effect = Exception("Network error")

        try:
            searcher.search_stories("test")
            assert False, "应该抛出异常"
        except CollectorError:
            pass
