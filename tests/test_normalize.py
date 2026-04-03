from pipeline.normalize import normalize_wechat_article


def test_normalize_wechat_article_maps_fields():
    raw_article = {
        "title": "封不住！Claude Code爆改Python版",
        "link": "https://mp.weixin.qq.com/s/example",
        "digest": "韩国女友神助攻",
        "time": "2026-04-03 09:30:05",
    }

    source = {"id": 1, "name": "量子位", "type": "wechat"}

    item = normalize_wechat_article(source, raw_article)

    assert item["source_id"] == 1
    assert item["source_type"] == "wechat"
    assert item["title"] == "封不住！Claude Code爆改Python版"
    assert item["url"] == "https://mp.weixin.qq.com/s/example"
    assert item["summary"] == "韩国女友神助攻"
    assert item["published_at"] == "2026-04-03T09:30:05"
    assert item["status"] == "raw"
