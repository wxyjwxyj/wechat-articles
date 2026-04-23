---
name: news-quality
description: 分析今日新闻质量：数据源分布、标签覆盖率、话题多样性、重复情况。用户说"今天质量怎么样"、"内容质量"、"分析一下今天的新闻"时触发。
tools: Bash, Read
---

分析今日 bundle 的内容质量，输出简洁报告。

## 执行步骤

```bash
cd $CLAUDE_PROJECT_DIR

python3 -c "
import json
from collections import Counter

if not __import__('os').path.exists('bundle_today.json'):
    print('bundle_today.json 不存在，请先运行采集')
    exit()

d = json.load(open('bundle_today.json'))
items = d.get('items_flat', d.get('items', []))
topics = d.get('topics', [])

print(f'=== 今日新闻质量报告（{d.get(\"bundle_date\",\"未知\")}）===')
print(f'总条数：{len(items)}，话题数：{len(topics)}')
print()

# 数据源分布
print('--- 数据源分布 ---')
source_cnt = Counter(i.get('source_type','unknown') for i in items)
for src, cnt in source_cnt.most_common():
    pct = cnt * 100 // len(items)
    print(f'  {src}: {cnt}条 ({pct}%)')
print()

# 标签覆盖率
tagged = sum(1 for i in items if i.get('tags') and len(json.loads(i['tags']) if isinstance(i['tags'], str) else i['tags']) > 0)
untagged = len(items) - tagged
print(f'--- 标签覆盖率 ---')
print(f'  已打标签：{tagged}条 ({tagged*100//len(items)}%)')
if untagged > 0:
    print(f'  ⚠ 未打标签：{untagged}条')
print()

# 话题多样性
print('--- 话题分布（Top 10）---')
for t in topics[:10]:
    name = t.get('name', '')
    cnt = t.get('count', len(t.get('items', [])))
    print(f'  {name}: {cnt}条')
print()

# 单一话题占比过高检测
if topics:
    top_cnt = topics[0].get('count', len(topics[0].get('items', [])))
    if top_cnt > len(items) * 0.3:
        print(f'  ⚠ 话题「{topics[0].get(\"name\",\"\")}」占比过高：{top_cnt}条 ({top_cnt*100//len(items)}%)')
"
```

## 输出格式

四段式：总览 → 数据源分布 → 标签覆盖率 → 话题分布。发现异常用 ⚠ 标注。
