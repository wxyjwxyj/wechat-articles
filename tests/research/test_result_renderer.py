# tests/research/test_result_renderer.py
from research.result_renderer import render_results_html


def test_render_results_html_contains_all_sections():
    """生成的 HTML 应包含所有分类"""
    results = {
        "papers": [
            {"title": "Paper 1", "url": "http://test.com", "score": 8, "comment": "好论文"}
        ],
        "repositories": [
            {"full_name": "user/repo", "url": "http://github.com", "score": 9, "comment": "优秀项目"}
        ],
        "discussions": [
            {"title": "Discussion 1", "hn_url": "http://hn.com", "score": 7, "comment": "有价值"}
        ],
        "docs": [
            {"name": "PyTorch", "url": "http://pytorch.org", "score": 9, "comment": "官方文档"}
        ],
    }

    html = render_results_html("强化学习", results)

    assert "强化学习" in html
    assert "Paper 1" in html
    assert "user/repo" in html
    assert "Discussion 1" in html
    assert "PyTorch" in html
    assert "好论文" in html


def test_render_results_html_handles_empty_results():
    """空结果应显示提示信息"""
    results = {
        "papers": [],
        "repositories": [],
        "discussions": [],
        "docs": [],
    }

    html = render_results_html("不存在的主题", results)

    assert "不存在的主题" in html
    assert "未找到" in html or "没有" in html


def test_render_results_html_shows_scores():
    """应显示评分"""
    results = {
        "papers": [
            {"title": "Test", "url": "http://test.com", "score": 8, "comment": "好"}
        ],
        "repositories": [],
        "discussions": [],
        "docs": [],
    }

    html = render_results_html("test", results)

    assert "8" in html or "8分" in html
