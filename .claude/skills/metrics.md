---
name: metrics
description: 查看采集指标趋势：各数据源历史条数、成功率、异常记录。用户说"最近采集情况"、"历史趋势"、"成功率"时触发。
tools: Bash, Read
---

读取 `.claude/metrics.csv`，展示最近的采集趋势。

```bash
cd $CLAUDE_PROJECT_DIR

python3 -c "
import csv, os

f = '.claude/metrics.csv'
if not os.path.exists(f):
    print('暂无指标数据，等 daily_run.sh 跑一次后再查')
    exit()

rows = list(csv.DictReader(open(f)))
if not rows:
    print('暂无数据')
    exit()

# 最近 14 条
recent = rows[-14:]
print(f'=== 采集指标趋势（最近 {len(recent)} 次）===')
print(f'{\"日期\":<12}{\"时间\":<8}{\"总计\":<6}{\"微信\":<6}{\"HN\":<5}{\"ArXiv\":<7}{\"GH\":<5}{\"RSS\":<5}{\"状态\"}')
print('-' * 65)
for r in recent:
    status = \"✅\" if r.get('status') == 'ok' else \"⚠\"
    print(f\"{r['date']:<12}{r['time']:<8}{r['total']:<6}{r['wechat']:<6}{r['hackernews']:<5}{r['arxiv']:<7}{r['github']:<5}{r['rss']:<5}{status}\")

print()

# 统计
ok_cnt = sum(1 for r in recent if r.get('status') == 'ok')
print(f'成功率：{ok_cnt}/{len(recent)} ({ok_cnt*100//len(recent)}%)')

# 异常记录
errors = [(r['date'], r['time'], r['errors']) for r in recent if r.get('errors','none') != 'none']
if errors:
    print()
    print('--- 异常记录 ---')
    for date, time, err in errors:
        print(f'  {date} {time}: {err}')
"
```
