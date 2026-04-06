# tests/research/test_topic_searcher.py
from unittest.mock import patch, MagicMock
from research.topic_searcher import TopicSearcher


def test_search_topic_calls_all_sources():
    """应调用所有数据源"""
    searcher = TopicSearcher(api_key="test-key")

    with patch('research.topic_searcher.ArxivCollector') as mock_arxiv, \
         patch('research.topic_searcher.GitHubSearcher') as mock_github, \
         patch('research.topic_searcher.HNSearcher') as mock_hn, \
         patch('research.topic_searcher.search_docs') as mock_docs, \
         patch('research.topic_searcher.ClaudeScorer') as mock_scorer:

        mock_arxiv_inst = MagicMock()
        mock_arxiv_inst.search_by_keyword.return_value = []
        mock_arxiv.return_value = mock_arxiv_inst

        mock_github_inst = MagicMock()
        mock_github_inst.search_repositories.return_value = []
        mock_github.return_value = mock_github_inst

        mock_hn_inst = MagicMock()
        mock_hn_inst.search_stories.return_value = []
        mock_hn.return_value = mock_hn_inst

        mock_docs.return_value = [{"name": "PyTorch", "url": "test"}]

        mock_scorer_inst = MagicMock()
        mock_scorer_inst.score_resources.return_value = []
        mock_scorer.return_value = mock_scorer_inst

        results = searcher.search_topic("reinforcement learning")

        # 验证所有数据源都被调用
        assert mock_arxiv_inst.search_by_keyword.called
        assert mock_github_inst.search_repositories.called
        assert mock_hn_inst.search_stories.called
        assert mock_docs.called


def test_search_topic_returns_categorized_results():
    """应返回按类型分类的结果"""
    searcher = TopicSearcher(api_key="test-key")

    with patch('research.topic_searcher.ArxivCollector') as mock_arxiv, \
         patch('research.topic_searcher.GitHubSearcher') as mock_github, \
         patch('research.topic_searcher.HNSearcher') as mock_hn, \
         patch('research.topic_searcher.search_docs') as mock_docs, \
         patch('research.topic_searcher.ClaudeScorer') as mock_scorer:

        mock_arxiv_inst = MagicMock()
        mock_arxiv_inst.search_by_keyword.return_value = [{"title": "Paper", "summary": "test"}]
        mock_arxiv.return_value = mock_arxiv_inst

        mock_github_inst = MagicMock()
        mock_github_inst.search_repositories.return_value = [{"name": "Repo", "description": "test"}]
        mock_github.return_value = mock_github_inst

        mock_hn_inst = MagicMock()
        mock_hn_inst.search_stories.return_value = [{"title": "Story", "url": "test"}]
        mock_hn.return_value = mock_hn_inst

        mock_docs.return_value = [{"name": "Doc", "url": "test"}]

        mock_scorer_inst = MagicMock()
        mock_scorer_inst.score_resources.side_effect = lambda x: [
            {**item, "score": 8, "comment": "好"} for item in x
        ]
        mock_scorer.return_value = mock_scorer_inst

        results = searcher.search_topic("test")

        assert "papers" in results
        assert "repositories" in results
        assert "discussions" in results
        assert "docs" in results


def test_search_topic_handles_partial_failure():
    """单个数据源失败不应影响其他数据源"""
    searcher = TopicSearcher(api_key="test-key")

    with patch('research.topic_searcher.ArxivCollector') as mock_arxiv, \
         patch('research.topic_searcher.GitHubSearcher') as mock_github, \
         patch('research.topic_searcher.HNSearcher') as mock_hn, \
         patch('research.topic_searcher.search_docs') as mock_docs, \
         patch('research.topic_searcher.ClaudeScorer') as mock_scorer:

        # ArXiv 失败
        mock_arxiv_inst = MagicMock()
        mock_arxiv_inst.search_by_keyword.side_effect = Exception("API error")
        mock_arxiv.return_value = mock_arxiv_inst

        # 其他成功
        mock_github_inst = MagicMock()
        mock_github_inst.search_repositories.return_value = [{"name": "Repo", "description": "test"}]
        mock_github.return_value = mock_github_inst

        mock_hn_inst = MagicMock()
        mock_hn_inst.search_stories.return_value = []
        mock_hn.return_value = mock_hn_inst

        mock_docs.return_value = []

        mock_scorer_inst = MagicMock()
        mock_scorer_inst.score_resources.return_value = [{"name": "Repo", "score": 8, "comment": "好"}]
        mock_scorer.return_value = mock_scorer_inst

        results = searcher.search_topic("test")

        # ArXiv 失败，但其他数据源正常
        assert results["papers"] == []
        assert len(results["repositories"]) > 0
