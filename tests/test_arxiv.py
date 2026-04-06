from unittest.mock import patch, MagicMock
from collectors.arxiv import ArxivCollector


def test_search_by_keyword_builds_correct_query():
    """关键词搜索应构建正确的查询字符串"""
    collector = ArxivCollector()

    with patch('collectors.arxiv.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector.search_by_keyword("reinforcement learning", max_results=5)

        # 验证调用参数
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert 'reinforcement learning' in params['search_query']
        assert params['max_results'] == 5


def test_search_by_keyword_returns_papers():
    """关键词搜索应返回论文列表"""
    collector = ArxivCollector()

    mock_xml = '''<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <entry>
            <id>http://arxiv.org/abs/2401.12345</id>
            <title>Deep Reinforcement Learning Survey</title>
            <summary>A comprehensive survey of deep RL methods.</summary>
            <published>2024-01-15T00:00:00Z</published>
            <author><name>John Doe</name></author>
        </entry>
    </feed>'''

    with patch('collectors.arxiv.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_xml
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = collector.search_by_keyword("reinforcement learning")

        assert len(results) == 1
        assert "reinforcement" in results[0]["title"].lower()
