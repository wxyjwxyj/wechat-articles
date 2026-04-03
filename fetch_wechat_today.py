#!/usr/bin/env python3
"""获取微信公众号今天的文章 - 使用已打开的浏览器标签页"""
import json
import sys
import os
from datetime import datetime

from collectors.wechat_collector import WechatCollector
from pipeline.normalize import normalize_wechat_article


# 加载配置
def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        print("✗ 错误: 找不到 config.json")
        print("  请复制 config.example.json 为 config.json 并填写配置")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    config = load_config()
    ACCOUNTS = config['accounts']
    TOKEN = config['token']
    TARGET_ID = config.get('target_id', '')  # 可选，如果为空则自动查找
    CDP_PROXY = config.get('cdp_proxy', 'http://localhost:3456')

    collector = WechatCollector(
        cdp_proxy=CDP_PROXY,
        token=TOKEN,
        target_id=TARGET_ID
    )

    all_results = {}

    for account, fakeid in ACCOUNTS.items():
        print(f"\n获取 {account} 今天的文章...")
        articles = collector.fetch_articles(account, fakeid)

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
