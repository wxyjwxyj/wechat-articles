# tests/research/test_github_search.py
from unittest.mock import patch, MagicMock
from research.github_search import GitHubSearcher


def test_search_repositories_builds_correct_url():
    """应构建正确的 GitHub Search API URL"""
    searcher = GitHubSearcher()

    with patch('research.github_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        searcher.search_repositories("reinforcement learning", max_results=5)

        call_args = mock_get.call_args
        assert "api.github.com/search/repositories" in call_args[0][0]
        params = call_args[1]['params']
        assert "reinforcement learning" in params['q']
        assert params['sort'] == 'stars'


def test_search_repositories_returns_repos():
    """应返回仓库列表"""
    searcher = GitHubSearcher()

    mock_json = {
        "items": [
            {
                "name": "stable-baselines3",
                "full_name": "DLR-RM/stable-baselines3",
                "html_url": "https://github.com/DLR-RM/stable-baselines3",
                "description": "PyTorch version of Stable Baselines",
                "stargazers_count": 5000,
                "language": "Python",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        ]
    }

    with patch('research.github_search.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = searcher.search_repositories("reinforcement learning")

        assert len(results) == 1
        assert results[0]["name"] == "stable-baselines3"
        assert results[0]["stars"] == 5000


def test_search_repositories_handles_api_error():
    """API 错误应抛出 CollectorError"""
    from utils.errors import CollectorError

    searcher = GitHubSearcher()

    with patch('research.github_search.requests.get') as mock_get:
        mock_get.side_effect = Exception("API rate limit")

        try:
            searcher.search_repositories("test")
            assert False, "应该抛出异常"
        except CollectorError:
            pass
