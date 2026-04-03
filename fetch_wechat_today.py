#!/usr/bin/env python3
"""获取微信公众号今天的文章 - 使用已打开的浏览器标签页"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

from collectors.wechat_collector import WechatCollector
from pipeline.normalize import normalize_wechat_article
from storage.db import init_db
from storage.repository import SourceRepository, ItemRepository


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

    # 初始化数据库和仓库
    db_path = Path("content.db")
    init_db(db_path)
    source_repo = SourceRepository(db_path)
    item_repo = ItemRepository(db_path)

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
            # 确保 source 存在，用于 normalize
            source_repo.upsert_source({
                "type": "wechat",
                "name": account,
                "external_id": fakeid,
                "status": "active",
                "config": {}
            })

            # 获取刚刚插入或更新的 source id
            sources = source_repo.list_sources()
            source = next((s for s in sources if s["name"] == account), None)

            if not source:
                print(f"  警告: 无法获取 {account} 的 source 记录")
                continue

            normalized_articles = []
            print(f"  找到 {len(articles)} 篇")
            for art in articles:
                print(f"    {art['time']} - {art['title'][:50]}")
                # 规范化文章
                item = normalize_wechat_article(source, art)
                normalized_articles.append(item)
                # 保存到数据库
                item_repo.upsert_item(item)

            all_results[account] = normalized_articles
        else:
            print(f"  今天暂无文章")

    # 保存结果
    if all_results:
        output_file = f"wechat_today_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已规范化并保存到数据库")
        print(f"✓ 规范化后的结果已保存到: {output_file}")
    else:
        print("\n今天所有公众号都没有新文章")
