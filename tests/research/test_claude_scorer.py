from unittest.mock import patch, MagicMock
from research.claude_scorer import ClaudeScorer


def test_score_resources_calls_claude_api():
    """应调用 Claude API 进行评分"""
    scorer = ClaudeScorer(api_key="test-key")

    resources = [
        {"title": "Deep RL Survey", "summary": "A comprehensive survey"},
        {"title": "PyTorch Tutorial", "summary": "Getting started with PyTorch"},
    ]

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"results": [{"id": 1, "score": 8, "comment": "很好的综述"}, {"id": 2, "score": 7, "comment": "实用教程"}]}')]

    with patch('research.claude_scorer.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        results = scorer.score_resources(resources)

        assert len(results) == 2
        assert results[0]["score"] == 8
        assert results[0]["comment"] == "很好的综述"
        assert mock_client.messages.create.called


def test_score_resources_filters_low_scores():
    """应过滤低分资源"""
    scorer = ClaudeScorer(api_key="test-key", min_score=6)

    resources = [
        {"title": "Good paper", "summary": "High quality"},
        {"title": "Bad paper", "summary": "Low quality"},
    ]

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"results": [{"id": 1, "score": 8, "comment": "优秀"}, {"id": 2, "score": 3, "comment": "质量差"}]}')]

    with patch('research.claude_scorer.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        results = scorer.score_resources(resources)

        # 只返回 score >= 6 的
        assert len(results) == 1
        assert results[0]["score"] == 8


def test_score_resources_handles_api_error():
    """API 错误应抛出 AIApiError"""
    from utils.errors import AIApiError

    scorer = ClaudeScorer(api_key="test-key")

    with patch('research.claude_scorer.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_anthropic.return_value = mock_client

        try:
            scorer.score_resources([{"title": "test", "summary": "test"}])
            assert False, "应该抛出异常"
        except AIApiError:
            pass
