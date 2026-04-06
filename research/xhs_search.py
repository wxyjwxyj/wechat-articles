"""小红书笔记搜索，通过 xhs-cli 调用（需提前 xhs login）。"""
import subprocess
import json
import yaml
from utils.log import get_logger

logger = get_logger(__name__)


class XhsSearcher:
    """小红书笔记搜索器。"""

    def search_notes(self, topic: str, max_results: int = 10) -> list[dict]:
        """按关键词搜索小红书笔记。

        Args:
            topic: 搜索主题
            max_results: 最多返回条数

        Returns:
            笔记列表，每项包含 title, url, author, cover, liked_count,
            collected_count, comment_count, type
        """
        try:
            result = subprocess.run(
                ["xhs", "search", topic],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except FileNotFoundError:
            logger.warning("xhs-cli 未安装，跳过小红书搜索")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("小红书搜索超时")
            return []

        if result.returncode != 0:
            logger.warning("小红书搜索失败: %s", result.stdout[:200])
            return []

        try:
            data = yaml.safe_load(result.stdout)
        except Exception as e:
            logger.warning("小红书搜索结果解析失败: %s", e)
            return []

        if not data.get("ok"):
            err = data.get("error", {})
            logger.warning("小红书搜索返回错误: %s", err.get("message", ""))
            return []

        items = data.get("data", {}).get("items", [])
        notes = []
        for item in items[:max_results]:
            card = item.get("note_card", {})
            note_id = item.get("id", "")
            xsec_token = item.get("xsec_token", "")
            user = card.get("user", {})
            interact = card.get("interact_info", {})
            cover = card.get("cover", {})

            # 构造可访问的 URL（需带 xsec_token）
            url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_search"

            notes.append({
                "title": card.get("display_title", ""),
                "url": url,
                "author": user.get("nickname", user.get("nick_name", "")),
                "cover": cover.get("url_pre", cover.get("url_default", "")),
                "type": card.get("type", "normal"),  # video / normal
                "liked_count": interact.get("liked_count", "0"),
                "collected_count": interact.get("collected_count", "0"),
                "comment_count": interact.get("comment_count", "0"),
            })

        logger.info("小红书搜索 '%s'：找到 %d 条", topic, len(notes))
        return notes
