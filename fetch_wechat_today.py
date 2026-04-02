#!/usr/bin/env python3
"""获取微信公众号今天的文章 - 使用已打开的浏览器标签页"""
import requests
import json
import sys
import os
from datetime import datetime

# 加载配置
def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        print("✗ 错误: 找不到 config.json")
        print("  请复制 config.example.json 为 config.json 并填写配置")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
ACCOUNTS = config['accounts']
TOKEN = config['token']
TARGET_ID = config.get('target_id', '')  # 可选，如果为空则自动查找
CDP_PROXY = config.get('cdp_proxy', 'http://localhost:3456')

def fetch_articles(account_name, fakeid, count=20):
    """获取文章"""
    # 如果没有指定 target_id，自动查找
    target_id = TARGET_ID
    if not target_id:
        resp = requests.get(f"{CDP_PROXY}/targets")
        targets = resp.json()
        for target in targets:
            if 'mp.weixin.qq.com' in target.get('url', ''):
                target_id = target['targetId']
                break

        if not target_id:
            print(f"  {account_name}: 未找到微信公众平台标签页")
            return []

    # 使用 XMLHttpRequest 同步请求
    js_code = f'''
    (() => {{
        const xhr = new XMLHttpRequest();
        xhr.open('GET', 'https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&search_field=null&begin=0&count={count}&query=&fakeid={fakeid}&type=101_1&free_publish_type=1&sub_action=list_ex&token={TOKEN}&lang=zh_CN&f=json&ajax=1', false);
        xhr.send();
        return JSON.parse(xhr.responseText);
    }})()
    '''

    resp = requests.post(f"{CDP_PROXY}/eval?target={target_id}", data=js_code)
    raw_data = resp.json().get('value', {})

    return parse_articles(account_name, raw_data)

def parse_articles(account_name, raw_data):
    """解析文章数据，只返回今天的"""
    if not raw_data or 'base_resp' not in raw_data:
        print(f"  {account_name}: API 返回数据异常")
        return []

    if raw_data.get('base_resp', {}).get('ret') != 0:
        print(f"  {account_name}: API 返回错误")
        return []

    publish_page_str = raw_data.get('publish_page', '{}')
    if isinstance(publish_page_str, str):
        publish_page = json.loads(publish_page_str)
    else:
        publish_page = publish_page_str

    articles = []
    today = datetime.now().date()

    for item in publish_page.get('publish_list', []):
        publish_info_str = item.get('publish_info', '{}')
        if isinstance(publish_info_str, str):
            publish_info = json.loads(publish_info_str)
        else:
            publish_info = publish_info_str

        for msg in publish_info.get('appmsgex', []):
            pub_time = datetime.fromtimestamp(msg['update_time'])

            # 只保留今天的文章
            if pub_time.date() == today:
                articles.append({
                    'title': msg['title'],
                    'link': msg['link'],
                    'digest': msg['digest'],
                    'time': pub_time.strftime('%Y-%m-%d %H:%M:%S')
                })

    return articles

if __name__ == "__main__":
    all_results = {}

    for account, fakeid in ACCOUNTS.items():
        print(f"\n获取 {account} 今天的文章...")
        articles = fetch_articles(account, fakeid)

        if articles:
            all_results[account] = articles
            print(f"  找到 {len(articles)} 篇")
            for art in articles:
                print(f"    {art['time']} - {art['title'][:50]}")
        else:
            print(f"  今天暂无文章")

    # 保存结果
    if all_results:
        output_file = f"wechat_today_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到: {output_file}")
    else:
        print("\n今天所有公众号都没有新文章")
