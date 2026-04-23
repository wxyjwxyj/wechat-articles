"""news1 MCP Server — 暴露 content.db 查询接口给 Claude。

工具：
- query_items_by_date: 查询指定日期的采集条数（按数据源分组）
- query_recent_trend: 查询最近 N 天各数据源条数趋势
- query_items: 按关键词搜索新闻条目
"""
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).parent.parent / "content.db"
CST = timezone(timedelta(hours=8))

mcp = FastMCP("news1")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def query_items_by_date(date: str = "") -> str:
    """查询指定日期（YYYY-MM-DD）各数据源采集条数。不传日期则查今天。"""
    if not date:
        date = datetime.now(CST).date().isoformat()
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT s.name, s.type, COUNT(i.id) as cnt
            FROM items i JOIN sources s ON i.source_id = s.id
            WHERE date(i.published_at, '+8 hours') = ? OR date(i.created_at) = ?
            GROUP BY s.name ORDER BY cnt DESC
        """, (date, date)).fetchall()
    if not rows:
        return f"{date} 暂无数据"
    lines = [f"=== {date} 采集情况 ==="]
    total = 0
    for r in rows:
        lines.append(f"  {r['name']}({r['type']}): {r['cnt']}条")
        total += r['cnt']
    lines.append(f"  合计: {total}条")
    return "\n".join(lines)


@mcp.tool()
def query_recent_trend(days: int = 7) -> str:
    """查询最近 N 天（默认7天）各数据源每天的采集条数趋势。"""
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT
                CASE
                    WHEN substr(i.published_at, 20, 6) = '+00:00'
                    THEN date(i.published_at, '+8 hours')
                    ELSE date(i.published_at)
                END as day,
                s.type,
                COUNT(i.id) as cnt
            FROM items i JOIN sources s ON i.source_id = s.id
            WHERE date(i.created_at) >= date('now', ?)
            GROUP BY day, s.type
            ORDER BY day DESC, cnt DESC
        """, (f"-{days} days",)).fetchall()

    if not rows:
        return f"最近 {days} 天暂无数据"

    # 按日期聚合
    from collections import defaultdict
    by_day = defaultdict(dict)
    for r in rows:
        by_day[r['day']][r['type']] = r['cnt']

    src_types = ['wechat', 'hackernews', 'arxiv', 'github_trending', 'rss']
    lines = [f"=== 最近 {days} 天趋势 ==="]
    lines.append(f"{'日期':<12} {'微信':>5} {'HN':>5} {'ArXiv':>7} {'GH':>5} {'RSS':>5} {'合计':>6}")
    lines.append("-" * 50)
    for day in sorted(by_day.keys(), reverse=True):
        d = by_day[day]
        total = sum(d.values())
        lines.append(
            f"{day:<12} {d.get('wechat',0):>5} {d.get('hackernews',0):>5} "
            f"{d.get('arxiv',0):>7} {d.get('github_trending',0):>5} "
            f"{d.get('rss',0):>5} {total:>6}"
        )
    return "\n".join(lines)


@mcp.tool()
def query_items(keyword: str, days: int = 3, limit: int = 10) -> str:
    """按关键词搜索最近 N 天的新闻条目（搜索标题和摘要）。"""
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT i.title, i.title_zh, i.url, s.name as source,
                   date(i.published_at, '+8 hours') as day
            FROM items i JOIN sources s ON i.source_id = s.id
            WHERE (i.title LIKE ? OR i.summary LIKE ? OR i.title_zh LIKE ?)
              AND date(i.created_at) >= date('now', ?)
            ORDER BY i.published_at DESC
            LIMIT ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%",
              f"-{days} days", limit)).fetchall()

    if not rows:
        return f"最近 {days} 天未找到包含「{keyword}」的新闻"

    lines = [f"=== 「{keyword}」相关新闻（最近{days}天，共{len(rows)}条）==="]
    for r in rows:
        title = r['title_zh'] or r['title']
        lines.append(f"\n[{r['day']}] {r['source']}")
        lines.append(f"  {title}")
        lines.append(f"  {r['url']}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
