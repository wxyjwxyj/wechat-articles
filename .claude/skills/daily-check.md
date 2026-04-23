---
name: daily-check
description: 查看今日采集状态：各数据源条数、bundle 是否生成、最近日志错误。用户说"今天跑了吗"、"采集情况"、"日报状态"时触发。
tools: Bash, Read
---

查看今日（$ARGUMENTS 或今天）的采集状态，输出简洁报告。

## 执行步骤

1. 获取今天日期
2. 查询 content.db 各数据源今日条数
3. 检查 bundle_today.json 是否存在及条数
4. 扫描今日日志的 ERROR/WARNING

```bash
cd $CLAUDE_PROJECT_DIR

TODAY=$(date +%Y-%m-%d)

# 各数据源条数
echo "=== 今日采集（$TODAY）==="
python3 -c "
import sqlite3, json
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8))
conn = sqlite3.connect('content.db')
rows = conn.execute('''
    SELECT s.name, s.type, COUNT(i.id) as cnt
    FROM items i JOIN sources s ON i.source_id = s.id
    WHERE date(i.published_at, \"+8 hours\") = ? OR date(i.created_at) = ?
    GROUP BY s.name ORDER BY cnt DESC
''', ('$TODAY', '$TODAY')).fetchall()
for name, typ, cnt in rows:
    print(f'  {name}({typ}): {cnt}条')
total = sum(r[2] for r in rows)
print(f'  合计: {total}条')
conn.close()
"

# bundle 状态
echo ""
echo "=== Bundle ==="
if [ -f bundle_today.json ]; then
    python3 -c "
import json
d = json.load(open('bundle_today.json'))
items = d.get('items_flat', d.get('items', []))
print(f'  ✅ 已生成：{len(items)}条，{len(d.get(\"topics\",[]))}个话题')
print(f'  日期：{d.get(\"bundle_date\",\"未知\")}')
"
else
    echo "  ❌ 未生成"
fi

# 今日日志错误
echo ""
echo "=== 今日异常 ==="
LOG_FILE=".claude/logs/$TODAY.log"
if [ -f "$LOG_FILE" ]; then
    grep -E "ERROR|⚠|❌|失败|超时|限流" "$LOG_FILE" | grep -v "httpx\|anthropic._base" | tail -10 || echo "  无异常"
else
    echo "  日志文件不存在"
fi
```

## 输出格式

简洁三段式：数据源条数 → Bundle 状态 → 今日异常。不要啰嗦，直接给数字。
