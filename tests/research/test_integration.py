"""端到端集成测试（需要真实 API key，标记为 slow）"""
import os
import pytest
from research.topic_searcher import TopicSearcher


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="需要 ANTHROPIC_API_KEY 环境变量"
)
@pytest.mark.slow
def test_full_search_workflow():
    """完整搜索流程测试"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    searcher = TopicSearcher(
        api_key=api_key,
        max_papers=3,
        max_repos=3,
        max_discussions=3,
        max_docs=3,
    )

    results = searcher.search_topic("reinforcement learning")

    # 验证返回结构
    assert "papers" in results
    assert "repositories" in results
    assert "discussions" in results
    assert "docs" in results

    # 至少应该有一些结果
    total = (len(results["papers"]) + len(results["repositories"]) +
             len(results["discussions"]) + len(results["docs"]))
    assert total > 0, "应该至少返回一些结果"

    # 验证评分字段存在
    for category in ["papers", "repositories", "discussions", "docs"]:
        for item in results[category]:
            assert "score" in item
            assert "comment" in item
            assert 1 <= item["score"] <= 10
