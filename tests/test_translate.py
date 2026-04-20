# tests/test_translate.py
"""_translate_overseas_items 翻译逻辑测试。"""
from unittest.mock import patch, MagicMock
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# scripts/ 不是 package，用 importlib 加载
_spec = importlib.util.spec_from_file_location(
    "build_bundle", Path(__file__).parent.parent / "scripts" / "build_bundle.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_translate_overseas_items = _mod._translate_overseas_items


def _make_item(source_type="hackernews", language="en", title_zh="", **kwargs):
    """构造测试用 item。"""
    item = {
        "id": 1,
        "source_type": source_type,
        "language": language,
        "title": "Test Title",
        "summary": "Test summary",
        "title_zh": title_zh,
        "summary_zh": "",
    }
    item.update(kwargs)
    return item


def test_skips_wechat_items():
    """微信条目不翻译"""
    item = _make_item(source_type="wechat", language="zh")
    repo = MagicMock()

    with patch("utils.claude.claude_call") as mock_call:
        _translate_overseas_items([item], repo)
        mock_call.assert_not_called()


def test_skips_already_translated():
    """已有 title_zh 的条目不重复翻译"""
    item = _make_item(title_zh="已翻译标题")
    repo = MagicMock()

    with patch("utils.claude.claude_call") as mock_call:
        _translate_overseas_items([item], repo)
        mock_call.assert_not_called()


def test_translates_and_writes_back():
    """正常翻译并回写 DB"""
    item = _make_item()
    repo = MagicMock()

    mock_response = '{"title_zh": "测试标题", "summary_zh": "测试摘要"}'

    with patch("utils.claude.claude_call", return_value=mock_response):
        _translate_overseas_items([item], repo)

    assert item["title_zh"] == "测试标题"
    assert item["summary_zh"] == "测试摘要"
    repo.update_item_translations.assert_called_once_with(1, "测试标题", "测试摘要")


def test_fallback_to_original_title_when_empty():
    """Claude 返回空 title_zh 时兜底用原标题"""
    item = _make_item(title="Original Title")
    repo = MagicMock()

    mock_response = '{"title_zh": "", "summary_zh": "摘要"}'

    with patch("utils.claude.claude_call", return_value=mock_response):
        _translate_overseas_items([item], repo)

    assert item["title_zh"] == "Original Title"


def test_handles_api_failure_gracefully():
    """API 失败不崩溃，item 保持原状"""
    item = _make_item()
    repo = MagicMock()

    with patch("utils.claude.claude_call", side_effect=Exception("API error")):
        _translate_overseas_items([item], repo)

    assert item["title_zh"] == ""
    repo.update_item_translations.assert_not_called()


def test_skips_db_write_when_no_id():
    """item 没有 id 时跳过回写"""
    item = _make_item()
    del item["id"]
    repo = MagicMock()

    mock_response = '{"title_zh": "标题", "summary_zh": "摘要"}'

    with patch("utils.claude.claude_call", return_value=mock_response):
        _translate_overseas_items([item], repo)

    assert item["title_zh"] == "标题"
    repo.update_item_translations.assert_not_called()
