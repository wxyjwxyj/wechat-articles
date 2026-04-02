---
name: wechat-news
description: 获取微信公众号今日文章并生成 HTML 汇总页面
trigger: 当用户要求获取微信公众号文章、更新新闻汇总、或生成文章列表时使用
---

# 微信公众号文章获取与发布

自动获取指定微信公众号的今日文章，生成 HTML 汇总页面，并可选提交到 Git。

## 使用场景

- "获取今天的微信公众号文章"
- "更新新闻汇总"
- "生成文章列表"
- "拉取最新文章并发布"

## 执行流程

### 1. 检查前置条件

首先检查 CDP Proxy 和浏览器登录状态：

```bash
# 检查 CDP Proxy
curl -s http://localhost:3456/health

# 检查浏览器标签页
curl -s http://localhost:3456/targets | grep "mp.weixin.qq.com"
```

如果没有打开微信公众平台，则打开：

```bash
curl -s "http://localhost:3456/new?url=https://mp.weixin.qq.com/"
```

### 2. 获取今日文章

执行 `fetch_wechat_today.py` 脚本：

```bash
python fetch_wechat_today.py
```

这会生成 `wechat_today_YYYYMMDD.json` 文件。

### 3. 生成 HTML 页面

创建或更新 `generate_html.py` 脚本来生成 HTML：

```python
#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from collections import Counter

def generate_html(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计信息
    total_articles = sum(len(articles) for articles in data.values())
    total_accounts = len(data)
    
    # 提取热门主题（从标题中提取关键词）
    all_titles = []
    for articles in data.values():
        all_titles.extend([art['title'] for art in articles])
    
    # 简单的关键词提取（可以改进）
    keywords = []
    for title in all_titles:
        if 'Claude' in title or 'claude' in title:
            keywords.append('Claude')
        if 'AI' in title:
            keywords.append('AI')
        if 'OpenAI' in title:
            keywords.append('OpenAI')
        # 可以添加更多关键词
    
    keyword_counts = Counter(keywords).most_common(5)
    
    # 生成 HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>微信公众号文章汇总 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 10px; }}
        .summary {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 14px; }}
        .topics {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .topics-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 15px; }}
        .topic-tags {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .topic-tag {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 15px; border-radius: 20px; font-size: 14px; }}
        .account-section {{ margin-bottom: 40px; }}
        .account-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; }}
        .account-name {{ font-size: 20px; font-weight: bold; }}
        .account-count {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th {{ background: #f8f9fa; padding: 12px; text-align: left; font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6; }}
        td {{ padding: 12px; border-bottom: 1px solid #dee2e6; }}
        tr:hover {{ background: #f8f9fa; }}
        .title {{ font-weight: 500; }}
        .title a {{ color: #667eea; text-decoration: none; }}
        .title a:hover {{ text-decoration: underline; }}
        .digest {{ color: #666; font-size: 14px; }}
        .time {{ color: #999; font-size: 13px; white-space: nowrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 微信公众号文章汇总</h1>
        <div class="summary">获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 共 {total_articles} 篇文章 | 覆盖 {total_accounts} 个公众号</div>
'''
    
    # 热门主题
    if keyword_counts:
        html += '''        <div class="topics">
            <div class="topics-title">🔥 热门主题</div>
            <div class="topic-tags">
'''
        for keyword, count in keyword_counts:
            html += f'                <div class="topic-tag">{keyword} ({count})</div>\n'
        html += '''            </div>
        </div>
'''
    
    # 各公众号文章
    for account, articles in data.items():
        html += f'''
        <div class="account-section">
            <div class="account-header">
                <div class="account-name">{account}</div>
                <div class="account-count">共 {len(articles)} 篇文章</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50%">标题</th>
                        <th style="width: 35%">摘要</th>
                        <th style="width: 15%">发布时间</th>
                    </tr>
                </thead>
                <tbody>
'''
        for article in articles:
            html += f'''                    <tr>
                        <td class="title"><a href="{article['link']}" target="_blank">{article['title']}</a></td>
                        <td class="digest">{article['digest']}</td>
                        <td class="time">{article['time']}</td>
                    </tr>
'''
        html += '''                </tbody>
            </table>
        </div>
'''
    
    html += '''    </div>
</body>
</html>'''
    
    return html

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_html.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    html = generate_html(json_file)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✓ HTML 已生成: index.html")
```

执行：

```bash
python generate_html.py wechat_today_YYYYMMDD.json
```

### 4. 提交到 Git（可选）

如果用户要求提交，则执行：

```bash
# 查看状态
git status

# 添加文件
git add index.html wechat_today_*.json

# 提交
git commit -m "Update: $(date +%Y-%m-%d) articles"

# 推送（需要用户确认）
git push
```

## 注意事项

1. **CDP Proxy 必须运行**：确保 `http://localhost:3456` 可访问
2. **浏览器必须登录**：微信公众平台需要登录状态
3. **Token 可能过期**：如果失败，从浏览器 URL 更新 token
4. **只获取今天的文章**：如果今天没有新文章，会返回空列表
5. **Git 推送需要确认**：推送前询问用户

## 错误处理

- CDP Proxy 未运行 → 提示用户启动
- 浏览器未登录 → 提示用户登录微信公众平台
- Token 过期 → 提示用户更新 token
- 没有新文章 → 提示今天暂无更新

## 完整示例

```bash
# 一键执行完整流程
python fetch_wechat_today.py && \
python generate_html.py wechat_today_$(date +%Y%m%d).json && \
echo "✓ 完成！查看 index.html"
```
