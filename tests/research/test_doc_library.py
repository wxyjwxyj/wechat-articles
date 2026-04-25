# tests/research/test_doc_library.py
from research.doc_library import search_docs, DOCS_LIBRARY


def test_docs_library_has_common_frameworks():
    """文档库应包含常见框架"""
    assert "pytorch" in DOCS_LIBRARY
    assert "tensorflow" in DOCS_LIBRARY
    assert "langchain" in DOCS_LIBRARY
    assert "huggingface" in DOCS_LIBRARY


def test_search_docs_exact_match():
    """精确匹配框架名"""
    results = search_docs("pytorch")
    assert len(results) > 0
    assert any("pytorch" in r["name"].lower() for r in results)


def test_search_docs_fuzzy_match():
    """模糊匹配标签"""
    results = search_docs("深度学习")
    assert len(results) > 0
    # 应该返回 PyTorch, TensorFlow 等


def test_search_docs_no_match():
    """无匹配时返回空列表"""
    results = search_docs("完全不存在的框架xyzabc")
    assert results == []


def test_search_docs_case_insensitive():
    """搜索不区分大小写"""
    results1 = search_docs("PyTorch")
    results2 = search_docs("pytorch")
    assert len(results1) == len(results2)
