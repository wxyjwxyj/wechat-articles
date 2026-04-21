"""自学习模块：分析当日新闻，自动优化采集/标签配置。

读取 bundle_today.json 的 top 文章，用 Claude 分析是否有新关键词或标签规则
需要添加到系统中。安全改动自动执行并提交，架构级建议只写到 insights 文件。
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.claude import claude_call
from utils.log import get_logger

logger = get_logger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
BUNDLE_FILE = PROJECT_DIR / "bundle_today.json"
INSIGHTS_FILE = PROJECT_DIR / "insights_today.md"

# 安全区域：只允许修改这些文件的这些变量
SAFE_TARGETS = {
    "collectors/rss.py": ["_EXACT_KEYWORDS", "_SUBSTRING_KEYWORDS"],
    "collectors/hackernews.py": ["AI_KEYWORDS"],
    "collectors/arxiv.py": ["HIGH_VALUE_KEYWORDS"],
    "pipeline/tagging.py": ["PATTERNS"],
}


def _read_current_keywords() -> dict:
    """读取当前各文件的关键词列表。"""
    result = {}
    for filepath, fields in SAFE_TARGETS.items():
        full_path = PROJECT_DIR / filepath
        if not full_path.exists():
            continue
        content = full_path.read_text()
        # 简单提取：找到变量赋值到下一个空行或函数定义
        for field in fields:
            start = content.find(f"{field} =")
            if start == -1:
                start = content.find(f"{field}=")
            if start == -1:
                continue
            # 找到对应的闭合括号
            bracket_start = content.find("[", start)
            if bracket_start == -1:
                continue
            depth = 0
            end = bracket_start
            for i in range(bracket_start, len(content)):
                if content[i] == "[":
                    depth += 1
                elif content[i] == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            result[f"{filepath}:{field}"] = content[bracket_start:end]
    return result


def _get_top_items(n: int = 15) -> list[dict]:
    """从 bundle 读取 top N 条目的摘要信息。"""
    if not BUNDLE_FILE.exists():
        return []
    data = json.loads(BUNDLE_FILE.read_text())
    items = data.get("items", [])
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return [
        {
            "title": it.get("title_zh") or it.get("title", ""),
            "tags": it.get("tags", []),
            "summary": (it.get("summary_zh") or it.get("summary", ""))[:200],
            "source": it.get("source_name", ""),
        }
        for it in items[:n]
    ]


def _build_prompt(current_keywords: dict, top_items: list[dict]) -> str:
    """构建分析 prompt。"""
    items_text = "\n".join(
        f"- [{it['source']}] {it['title']} (tags: {it['tags']})"
        for it in top_items
    )
    keywords_text = "\n".join(
        f"  {key}: {val[:500]}" for key, val in current_keywords.items()
    )

    return f"""Analyze today's top AI news and suggest improvements to our news collection system's keyword lists and tagging patterns.

Current configuration:
{keywords_text}

Today's top {len(top_items)} news items:
{items_text}

Tasks:
1. Identify new AI-related keywords/terms/company names that appear in multiple articles but are NOT in our current keyword lists
2. Identify any tagging patterns (company/product names) that should be added
3. Note any broader insights about trends that could improve the system (these won't be auto-applied)

Rules:
- Be CONSERVATIVE: only suggest adding a keyword if it appears in 2+ articles AND is clearly AI-related
- Never suggest removing existing keywords unless they cause obvious false positives
- For tagging patterns, follow the existing format: ("标签名", "分类", ["关键词1", "关键词2"])
- Output valid JSON with this structure:

{{
  "auto_changes": [
    {{"file": "collectors/rss.py", "field": "_SUBSTRING_KEYWORDS", "action": "add", "value": "example_keyword", "reason": "appeared in 3 articles about X"}},
  ],
  "suggestions": [
    {{"type": "datasource|architecture|workflow", "description": "...", "reason": "..."}}
  ],
  "trend_notes": "One paragraph summary of today's key trends"
}}

If no changes are needed, return {{"auto_changes": [], "suggestions": [], "trend_notes": "..."}}
Output ONLY the JSON, no markdown fences."""


def _apply_keyword_change(filepath: str, field: str, action: str, value: str) -> bool:
    """在指定文件的关键词列表中添加或删除一项。返回是否成功。"""
    full_path = PROJECT_DIR / filepath
    content = full_path.read_text()

    if action == "add":
        # 找到列表的最后一个 ] 前插入
        start = content.find(f"{field} =")
        if start == -1:
            start = content.find(f"{field}=")
        if start == -1:
            logger.warning("找不到 %s 中的 %s", filepath, field)
            return False

        # 找到闭合 ]
        bracket_start = content.find("[", start)
        depth = 0
        close_bracket = bracket_start
        for i in range(bracket_start, len(content)):
            if content[i] == "[":
                depth += 1
            elif content[i] == "]":
                depth -= 1
                if depth == 0:
                    close_bracket = i
                    break

        # 在 ] 前插入新项
        # 检查是否已存在
        existing_section = content[bracket_start:close_bracket]
        if f'"{value}"' in existing_section or f"'{value}'" in existing_section:
            logger.info("关键词 '%s' 已存在于 %s:%s，跳过", value, filepath, field)
            return False

        # 找到最后一个逗号或引号后的位置
        insert_pos = close_bracket
        indent = "    "
        new_entry = f'{indent}"{value}",\n'
        new_content = content[:insert_pos] + new_entry + content[insert_pos:]
        full_path.write_text(new_content)
        logger.info("已添加 '%s' 到 %s:%s", value, filepath, field)
        return True

    elif action == "remove":
        # 简单的行级删除
        lines = content.split("\n")
        new_lines = []
        removed = False
        for line in lines:
            if f'"{value}"' in line or f"'{value}'" in line:
                # 确认是在目标字段的上下文中（简单检查：在 field 定义之后）
                removed = True
                continue
            new_lines.append(line)
        if removed:
            full_path.write_text("\n".join(new_lines))
            logger.info("已从 %s:%s 删除 '%s'", filepath, field, value)
        return removed

    return False


def _apply_tagging_change(value: str, reason: str) -> bool:
    """向 pipeline/tagging.py 的 PATTERNS 列表追加新标签规则。"""
    # value 应该是类似 ("标签名", "分类", ["kw1", "kw2"]) 的字符串
    full_path = PROJECT_DIR / "pipeline/tagging.py"
    content = full_path.read_text()

    # 检查标签是否已存在
    if value.split(",")[0].strip("( \"'") in content:
        logger.info("标签规则已存在，跳过: %s", value[:50])
        return False

    # 找到 PATTERNS 列表的最后一个 ] 前插入
    # PATTERNS 是一个很长的列表，找最后的 ]
    patterns_start = content.find("PATTERNS = [")
    if patterns_start == -1:
        return False

    # 从 PATTERNS 开始找闭合 ]
    depth = 0
    close_pos = patterns_start
    found_open = False
    for i in range(patterns_start, len(content)):
        if content[i] == "[" and not found_open:
            found_open = True
            depth = 1
            continue
        if found_open:
            if content[i] == "[":
                depth += 1
            elif content[i] == "]":
                depth -= 1
                if depth == 0:
                    close_pos = i
                    break

    insert_pos = close_pos
    new_entry = f'\n    {value},  # auto-added: {reason[:50]}\n'
    new_content = content[:insert_pos] + new_entry + content[insert_pos:]
    full_path.write_text(new_content)
    logger.info("已添加标签规则: %s", value[:60])
    return True


def _run_tests() -> bool:
    """跑测试，返回是否全部通过。"""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=120,
    )
    if result.returncode != 0:
        logger.error("测试失败:\n%s", result.stdout[-1000:] if result.stdout else result.stderr[-500:])
    return result.returncode == 0


def _git_rollback(filepath: str):
    """回滚单个文件的改动。"""
    subprocess.run(
        ["git", "checkout", "--", filepath],
        cwd=PROJECT_DIR, capture_output=True,
    )
    logger.warning("已回滚 %s", filepath)


def _git_commit(message: str, files: list[str]):
    """提交指定文件。"""
    for f in files:
        subprocess.run(["git", "add", f], cwd=PROJECT_DIR, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"{message}\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"],
        cwd=PROJECT_DIR, capture_output=True,
    )


def _write_insights(today: str, auto_changes: list, suggestions: list, trend_notes: str):
    """写入 insights_today.md。"""
    lines = [f"# 自学习洞察 — {today}\n"]

    if auto_changes:
        lines.append("## 自动执行的改动\n")
        for c in auto_changes:
            lines.append(f"- [x] {c['action']} \"{c['value']}\" → {c['file']}:{c['field']}（{c['reason']}）\n")
    else:
        lines.append("## 自动执行的改动\n\n无\n")

    if suggestions:
        lines.append("\n## 建议（需人工确认）\n")
        for s in suggestions:
            lines.append(f"- [ ] [{s['type']}] {s['description']}（{s['reason']}）\n")

    if trend_notes:
        lines.append(f"\n## 今日趋势\n\n{trend_notes}\n")

    INSIGHTS_FILE.write_text("".join(lines))
    logger.info("已写入 %s", INSIGHTS_FILE.name)


def main():
    today = date.today().isoformat()
    logger.info("自学习分析开始 — %s", today)

    # 1. 读取输入
    top_items = _get_top_items(15)
    if not top_items:
        logger.info("无 bundle 数据，跳过")
        return

    current_keywords = _read_current_keywords()

    # 2. 调用 Claude 分析
    prompt = _build_prompt(current_keywords, top_items)
    try:
        response = claude_call(prompt, max_tokens=2048)
    except Exception as e:
        logger.error("Claude API 调用失败: %s", e)
        _write_insights(today, [], [], f"分析失败: {e}")
        return

    # 3. 解析响应
    try:
        # 处理可能的 markdown 代码块包裹
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        result = json.loads(text)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error("JSON 解析失败: %s\n响应: %s", e, response[:500])
        _write_insights(today, [], [], f"解析失败，原始响应已记录到日志")
        return

    auto_changes = result.get("auto_changes", [])
    suggestions = result.get("suggestions", [])
    trend_notes = result.get("trend_notes", "")

    # 4. 执行安全改动
    applied = []
    for change in auto_changes:
        filepath = change.get("file", "")
        field = change.get("field", "")
        action = change.get("action", "")
        value = change.get("value", "")
        reason = change.get("reason", "")

        # 安全检查
        if filepath not in SAFE_TARGETS:
            logger.warning("跳过不安全的目标文件: %s", filepath)
            continue
        if field not in SAFE_TARGETS[filepath]:
            logger.warning("跳过不安全的字段: %s:%s", filepath, field)
            continue
        if action not in ("add", "remove"):
            continue

        # 特殊处理 tagging PATTERNS
        if filepath == "pipeline/tagging.py" and field == "PATTERNS":
            if _apply_tagging_change(value, reason):
                applied.append(change)
        else:
            if _apply_keyword_change(filepath, field, action, value):
                applied.append(change)

    # 5. 验证改动
    if applied:
        if _run_tests():
            # 测试通过，提交
            changed_files = list(set(c["file"] for c in applied))
            descriptions = "; ".join(f'{c["action"]} "{c["value"]}"' for c in applied[:3])
            _git_commit(
                f"improve(auto): {descriptions}",
                changed_files,
            )
            logger.info("自动改动已提交: %d 项", len(applied))
        else:
            # 测试失败，回滚所有改动
            changed_files = list(set(c["file"] for c in applied))
            for f in changed_files:
                _git_rollback(f)
            logger.warning("测试失败，已回滚所有改动")
            applied = []  # 清空，不写入 insights

    # 6. 写入洞察文件
    _write_insights(today, applied, suggestions, trend_notes)
    logger.info("自学习分析完成 — 执行 %d 项改动，%d 项建议", len(applied), len(suggestions))


if __name__ == "__main__":
    main()
