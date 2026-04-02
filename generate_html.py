#!/usr/bin/env python3
"""从 JSON 生成 HTML 汇总页面"""
import json
import sys
from datetime import datetime
from collections import Counter
import re

def extract_keywords(title):
    """从标题中提取关键词"""
    keywords = []

    # 定义关键词规则
    patterns = {
        'Claude Code': r'Claude\s*Code',
        'Claude': r'Claude',
        'OpenAI': r'OpenAI',
        'AI': r'\bAI\b',
        '大模型': r'大模型|LLM',
        '具身智能': r'具身智能',
        '融资': r'融资|投资',
        '开源': r'开源',
        '源码': r'源码|代码',
        'Agent': r'Agent|智能体',
    }

    for keyword, pattern in patterns.items():
        if re.search(pattern, title, re.IGNORECASE):
            keywords.append(keyword)

    return keywords

def generate_html(json_file):
    """生成 HTML 页面"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 统计信息
    total_articles = sum(len(articles) for articles in data.values())
    total_accounts = len(data)

    # 提取热门主题
    all_keywords = []
    for articles in data.values():
        for art in articles:
            all_keywords.extend(extract_keywords(art['title']))

    keyword_counts = Counter(all_keywords).most_common(8)

    # 生成 HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信公众号文章汇总 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; background: #f5f5f5; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 20px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 10px; font-size: 28px; }}
        .summary {{ text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }}
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
        td {{ padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top; }}
        tr:hover {{ background: #f8f9fa; }}
        .title {{ font-weight: 500; }}
        .title a {{ color: #667eea; text-decoration: none; }}
        .title a:hover {{ text-decoration: underline; color: #764ba2; }}
        .digest {{ color: #666; font-size: 14px; }}
        .time {{ color: #999; font-size: 13px; white-space: nowrap; }}
        @media (max-width: 768px) {{
            .container {{ margin: 10px; padding: 15px; }}
            h1 {{ font-size: 22px; }}
            table {{ font-size: 14px; }}
            th, td {{ padding: 8px; }}
        }}
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
        if not articles:
            continue

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
                        <td class="time">{article['time'].split()[1] if ' ' in article['time'] else article['time']}</td>
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
        print("示例: python generate_html.py wechat_today_20260402.json")
        sys.exit(1)

    json_file = sys.argv[1]

    try:
        html = generate_html(json_file)

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ HTML 已生成: index.html")
        print(f"  数据来源: {json_file}")
    except FileNotFoundError:
        print(f"✗ 错误: 找不到文件 {json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ 错误: {json_file} 不是有效的 JSON 文件")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)
