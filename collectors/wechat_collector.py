import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests


class WechatCollector:
    def __init__(self, cdp_proxy: str, token: str = "", target_id: str = ""):
        self.cdp_proxy = cdp_proxy
        self.token = token
        self.target_id = target_id

    def _resolve_session(self) -> bool:
        """自动从浏览器标签页中探测 target_id 和 token，优先使用公众平台主页。"""
        try:
            resp = requests.get(f"{self.cdp_proxy}/targets", timeout=10)
            resp.raise_for_status()
            targets = resp.json()
        except (requests.RequestException, ValueError) as e:
            print(f"错误: 获取 targets 失败 - {e}")
            return False

        # 优先匹配公众平台管理页（含 token 参数），其次匹配任意微信域名
        best_target = None
        best_token = ""
        for t in targets:
            url = t.get("url", "")
            if "mp.weixin.qq.com" not in url:
                continue
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            token_val = qs.get("token", [""])[0]
            if token_val:
                # 含 token 的管理页，优先级最高
                best_target = t.get("targetId", "")
                best_token = token_val
                break
            if best_target is None:
                best_target = t.get("targetId", "")

        if not best_target:
            print("错误: 未找到微信公众平台标签页，请先在浏览器中打开 mp.weixin.qq.com 并登录")
            return False

        if not self.target_id:
            self.target_id = best_target
        if not self.token:
            self.token = best_token

        if not self.token:
            print("错误: 无法从浏览器 URL 获取 token，请确保在微信公众平台管理页（含 token 参数）已登录")
            return False

        return True

    def fetch_articles(self, account_name: str, fakeid: str, count: int = 20) -> list[dict]:
        # 首次调用时探测 session（后续复用已探测到的值）
        if not self.target_id or not self.token:
            if not self._resolve_session():
                print(f"[{account_name}] 错误: 无法获取 target_id / token")
                return []

        js_code = f'''
        (() => {{
            const xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&search_field=null&begin=0&count={count}&query=&fakeid={fakeid}&type=101_1&free_publish_type=1&sub_action=list_ex&token={self.token}&lang=zh_CN&f=json&ajax=1', false);
            xhr.send();
            return JSON.parse(xhr.responseText);
        }})()
        '''
        try:
            resp = requests.post(f"{self.cdp_proxy}/eval?target={self.target_id}", data=js_code, timeout=10)
            resp.raise_for_status()
            raw_data = resp.json().get("value", {})
        except requests.RequestException as e:
            print(f"[{account_name}] 错误: CDP 请求失败 - {e}")
            return []
        except ValueError as e:
            print(f"[{account_name}] 错误: JSON 解析失败 - {e}")
            return []

        return self._parse_articles(raw_data)

    def _parse_articles(self, raw_data: dict) -> list[dict]:
        if not raw_data or raw_data.get("base_resp", {}).get("ret") != 0:
            return []
        publish_page = raw_data.get("publish_page", "{}")
        if isinstance(publish_page, str):
            try:
                publish_page = json.loads(publish_page)
            except json.JSONDecodeError:
                publish_page = {}
                
        today = datetime.now().date()
        articles = []
        for item in publish_page.get("publish_list", []):
            publish_info = item.get("publish_info", "{}")
            if isinstance(publish_info, str):
                try:
                    publish_info = json.loads(publish_info)
                except json.JSONDecodeError:
                    publish_info = {}
                    
            for msg in publish_info.get("appmsgex", []):
                update_time = msg.get("update_time")
                if not update_time:
                    continue
                pub_time = datetime.fromtimestamp(update_time)
                if pub_time.date() == today:
                    articles.append(
                        {
                            "title": msg.get("title", ""),
                            "link": msg.get("link", ""),
                            "digest": msg.get("digest", ""),
                            "time": pub_time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
        return articles
