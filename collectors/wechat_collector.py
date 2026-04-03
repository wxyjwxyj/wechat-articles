import json
from datetime import datetime

import requests


class WechatCollector:
    def __init__(self, cdp_proxy: str, token: str, target_id: str = ""):
        self.cdp_proxy = cdp_proxy
        self.token = token
        self.target_id = target_id

    def fetch_articles(self, account_name: str, fakeid: str, count: int = 20) -> list[dict]:
        target_id = self.target_id or self._find_target_id()
        if not target_id:
            return []

        js_code = f'''
        (() => {{
            const xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&search_field=null&begin=0&count={count}&query=&fakeid={fakeid}&type=101_1&free_publish_type=1&sub_action=list_ex&token={self.token}&lang=zh_CN&f=json&ajax=1', false);
            xhr.send();
            return JSON.parse(xhr.responseText);
        }})()
        '''
        resp = requests.post(f"{self.cdp_proxy}/eval?target={target_id}", data=js_code)
        raw_data = resp.json().get("value", {})
        return self._parse_articles(raw_data)

    def _find_target_id(self) -> str:
        resp = requests.get(f"{self.cdp_proxy}/targets")
        for target in resp.json():
            if "mp.weixin.qq.com" in target.get("url", ""):
                return target["targetId"]
        return ""

    def _parse_articles(self, raw_data: dict) -> list[dict]:
        if not raw_data or raw_data.get("base_resp", {}).get("ret") != 0:
            return []
        publish_page = raw_data.get("publish_page", "{}")
        if isinstance(publish_page, str):
            publish_page = json.loads(publish_page)
        today = datetime.now().date()
        articles = []
        for item in publish_page.get("publish_list", []):
            publish_info = item.get("publish_info", "{}")
            if isinstance(publish_info, str):
                publish_info = json.loads(publish_info)
            for msg in publish_info.get("appmsgex", []):
                pub_time = datetime.fromtimestamp(msg["update_time"])
                if pub_time.date() == today:
                    articles.append(
                        {
                            "title": msg["title"],
                            "link": msg["link"],
                            "digest": msg.get("digest", ""),
                            "time": pub_time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
        return articles
