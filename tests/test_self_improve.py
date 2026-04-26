"""scripts/self_improve.py 测试：自学习模块核心逻辑。"""
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 把 scripts/ 加入 path，方便 import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from self_improve import (
    _read_current_keywords,
    _get_top_items,
    _build_prompt,
    _apply_keyword_change,
    _apply_tagging_change,
    _write_insights,
    SAFE_TARGETS,
)


# ── _get_top_items ──


def test_get_top_items_returns_sorted(bundle_tmp):
    """按 score 降序返回 top N 条目。"""
    items = [
        {"title": "A", "score": 5, "tags": [], "summary": "", "source_name": ""},
        {"title": "B", "score": 9, "tags": [], "summary": "", "source_name": ""},
        {"title": "C", "score": 7, "tags": [], "summary": "", "source_name": ""},
    ]
    bundle_tmp.write_text(json.dumps({"items": items}))
    result = _get_top_items(n=2)
    assert len(result) == 2
    assert result[0]["title"] == "B"
    assert result[1]["title"] == "C"


def test_get_top_items_empty_bundle(bundle_tmp):
    """空 bundle 返回空列表。"""
    bundle_tmp.write_text(json.dumps({"items": []}))
    assert _get_top_items() == []


def test_get_top_items_no_file(bundle_tmp):
    """文件不存在返回空列表。"""
    bundle_tmp.unlink(missing_ok=True)
    assert _get_top_items() == []


def test_get_top_items_uses_title_zh(bundle_tmp):
    """有 title_zh 时优先使用。"""
    items = [{"title": "EN", "title_zh": "中文", "score": 1, "tags": [], "summary": "", "source_name": ""}]
    bundle_tmp.write_text(json.dumps({"items": items}))
    result = _get_top_items()
    assert result[0]["title"] == "中文"


# ── _build_prompt ──


def test_build_prompt_includes_keywords():
    """prompt 包含当前关键词配置。"""
    keywords = {"collectors/rss.py:_EXACT_KEYWORDS": '["GPT", "Claude"]'}
    items = [{"title": "Test", "tags": ["AI公司"], "summary": "", "source": "量子位"}]
    prompt = _build_prompt(keywords, items)
    assert "GPT" in prompt
    assert "Claude" in prompt


def test_build_prompt_includes_items():
    """prompt 包含新闻条目信息。"""
    items = [{"title": "GPT-5 发布", "tags": ["AI公司"], "summary": "", "source": "量子位"}]
    prompt = _build_prompt({}, items)
    assert "GPT-5 发布" in prompt
    assert "量子位" in prompt


def test_build_prompt_output_format():
    """prompt 要求输出 JSON 格式。"""
    prompt = _build_prompt({}, [])
    assert "auto_changes" in prompt
    assert "suggestions" in prompt
    assert "trend_notes" in prompt


# ── _apply_keyword_change ──


def test_apply_keyword_add(tmp_path):
    """添加关键词到列表末尾。"""
    target = tmp_path / "collectors" / "rss.py"
    target.parent.mkdir(parents=True)
    target.write_text('_EXACT_KEYWORDS = [\n    "GPT",\n    "Claude",\n]\n')

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_keyword_change("collectors/rss.py", "_EXACT_KEYWORDS", "add", "Gemini")

    assert result is True
    content = target.read_text()
    assert '"Gemini"' in content


def test_apply_keyword_add_duplicate(tmp_path):
    """已存在的关键词不重复添加。"""
    target = tmp_path / "collectors" / "rss.py"
    target.parent.mkdir(parents=True)
    target.write_text('_EXACT_KEYWORDS = [\n    "GPT",\n]\n')

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_keyword_change("collectors/rss.py", "_EXACT_KEYWORDS", "add", "GPT")

    assert result is False


def test_apply_keyword_remove(tmp_path):
    """删除指定关键词。"""
    target = tmp_path / "collectors" / "rss.py"
    target.parent.mkdir(parents=True)
    target.write_text('_EXACT_KEYWORDS = [\n    "GPT",\n    "Claude",\n]\n')

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_keyword_change("collectors/rss.py", "_EXACT_KEYWORDS", "remove", "GPT")

    assert result is True
    content = target.read_text()
    assert '"GPT"' not in content
    assert '"Claude"' in content


def test_apply_keyword_field_not_found(tmp_path):
    """目标字段不存在时返回 False。"""
    target = tmp_path / "collectors" / "rss.py"
    target.parent.mkdir(parents=True)
    target.write_text("# no keywords here\n")

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_keyword_change("collectors/rss.py", "_EXACT_KEYWORDS", "add", "X")

    assert result is False


# ── _apply_tagging_change ──


def test_apply_tagging_change(tmp_path):
    """添加标签规则到 PATTERNS 列表。"""
    target = tmp_path / "pipeline" / "tagging.py"
    target.parent.mkdir(parents=True)
    target.write_text('PATTERNS = [\n    ("AI公司", "AI公司", ["OpenAI"]),\n]\n')

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_tagging_change('("新标签", "AI技术", ["关键词"])', "测试添加")

    assert result is True
    content = target.read_text()
    assert "新标签" in content


def test_apply_tagging_change_duplicate(tmp_path):
    """标签已存在时跳过。"""
    target = tmp_path / "pipeline" / "tagging.py"
    target.parent.mkdir(parents=True)
    target.write_text('PATTERNS = [\n    ("AI公司", "AI公司", ["OpenAI"]),\n]\n')

    with patch("self_improve.PROJECT_DIR", tmp_path):
        result = _apply_tagging_change('("AI公司", "AI公司", ["Google"])', "重复标签")

    assert result is False


# ── _write_insights ──


def test_write_insights_creates_file(tmp_path):
    """写入 insights 文件和归档。"""
    with patch("self_improve.INSIGHTS_FILE", tmp_path / "insights_today.md"), \
         patch("self_improve.PROJECT_DIR", tmp_path):
        _write_insights("2026-04-26", [], [], "今日趋势：AI 继续发展")

    assert (tmp_path / "insights_today.md").exists()
    assert (tmp_path / "insights" / "2026-04-26.md").exists()


def test_write_insights_includes_changes(tmp_path):
    """包含自动执行的改动。"""
    changes = [{"action": "add", "value": "Gemini", "file": "rss.py", "field": "KEYWORDS", "reason": "新关键词"}]
    with patch("self_improve.INSIGHTS_FILE", tmp_path / "insights_today.md"), \
         patch("self_improve.PROJECT_DIR", tmp_path):
        _write_insights("2026-04-26", changes, [], "")

    content = (tmp_path / "insights_today.md").read_text()
    assert "Gemini" in content
    assert "新关键词" in content


def test_write_insights_includes_suggestions(tmp_path):
    """包含建议。"""
    suggestions = [{"type": "architecture", "description": "添加新数据源", "reason": "覆盖面不足"}]
    with patch("self_improve.INSIGHTS_FILE", tmp_path / "insights_today.md"), \
         patch("self_improve.PROJECT_DIR", tmp_path):
        _write_insights("2026-04-26", [], suggestions, "")

    content = (tmp_path / "insights_today.md").read_text()
    assert "添加新数据源" in content


# ── SAFE_TARGETS ──


def test_safe_targets_covers_key_modules():
    """安全目标覆盖了关键的关键词/标签模块。"""
    assert "collectors/rss.py" in SAFE_TARGETS
    assert "collectors/hackernews.py" in SAFE_TARGETS
    assert "collectors/arxiv.py" in SAFE_TARGETS
    assert "pipeline/tagging.py" in SAFE_TARGETS


# ── fixture ──


@pytest.fixture
def bundle_tmp(tmp_path):
    """临时 bundle 文件。"""
    bundle = tmp_path / "bundle_today.json"
    with patch("self_improve.BUNDLE_FILE", bundle):
        yield bundle
