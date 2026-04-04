"""通过 CDP Proxy 操作微信公众号草稿箱（创建/查看/删除草稿）。

复用 WechatCollector 的 CDP 连接方式：浏览器登录态 + 同步 XHR。
"""
import json
from urllib.parse import urlparse, parse_qs

import requests


class MpPublisher:
    """微信公众号草稿箱操作器。"""

    def __init__(self, cdp_proxy: str = "http://localhost:3456"):
        self.cdp_proxy = cdp_proxy
        self.token = ""
        self.target_id = ""

    # ──────────────────────────────────────────────
    # 连接管理（与 WechatCollector 相同逻辑）
    # ──────────────────────────────────────────────

    def _resolve_session(self) -> bool:
        """从浏览器标签页中自动探测 target_id 和 token。"""
        try:
            resp = requests.get(f"{self.cdp_proxy}/targets", timeout=10)
            resp.raise_for_status()
            targets = resp.json()
        except (requests.RequestException, ValueError) as e:
            print(f"错误: 获取 targets 失败 - {e}")
            return False

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
                best_target = t.get("targetId", "")
                best_token = token_val
                break
            if best_target is None:
                best_target = t.get("targetId", "")

        if not best_target:
            print("错误: 未找到微信公众平台标签页")
            return False
        if not best_token:
            print("错误: 无法从浏览器 URL 获取 token，请确保已登录公众号后台")
            return False

        self.target_id = best_target
        self.token = best_token
        return True

    def _ensure_session(self) -> bool:
        """确保已连接，如未连接则自动探测。"""
        if self.target_id and self.token:
            return True
        return self._resolve_session()

    def _eval_js(self, js_code: str) -> dict:
        """通过 CDP Proxy 在浏览器中执行 JS 代码。"""
        resp = requests.post(
            f"{self.cdp_proxy}/eval?target={self.target_id}",
            data=js_code,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("value", {})

    # ──────────────────────────────────────────────
    # 草稿箱操作
    # ──────────────────────────────────────────────

    def create_draft(
        self,
        title: str,
        content_html: str,
        digest: str = "",
        author: str = "AI日报",
        cover_fileid: str = "",
        cover_cdn_url: str = "",
    ) -> dict:
        """创建一条公众号草稿。

        Args:
            title: 文章标题
            content_html: 正文 HTML
            digest: 摘要（不填则微信自动截取）
            author: 作者名
            cover_fileid: 封面图素材 ID（由 upload_cover 返回）
            cover_cdn_url: 封面图 CDN URL（由 upload_cover 返回）

        Returns:
            {"success": True/False, "app_msg_id": int, "raw": dict}
        """
        if not self._ensure_session():
            return {"success": False, "error": "无法连接公众号后台"}

        # 转义 JS 字符串中的特殊字符
        title_escaped = self._escape_js(title)
        content_escaped = self._escape_js(content_html)
        digest_escaped = self._escape_js(digest)
        author_escaped = self._escape_js(author)

        # 封面图字段
        fileid_val = cover_fileid or "0"
        cdn_url_val = self._escape_js(cover_cdn_url) if cover_cdn_url else ""
        show_cover = "1" if cover_fileid else "0"

        js_code = f'''(() => {{
  var xhr = new XMLHttpRequest();
  var url = "https://mp.weixin.qq.com/cgi-bin/operate_appmsg?t=ajax-response&sub=create&type=77&token={self.token}&lang=zh_CN";

  var formData = new FormData();
  formData.append("token", "{self.token}");
  formData.append("lang", "zh_CN");
  formData.append("f", "json");
  formData.append("ajax", "1");
  formData.append("AppMsgId", "");
  formData.append("count", "1");
  formData.append("title0", "{title_escaped}");
  formData.append("content0", "{content_escaped}");
  formData.append("digest0", "{digest_escaped}");
  formData.append("author0", "{author_escaped}");
  formData.append("fileid0", "{fileid_val}");
  formData.append("cdn_url0", "{cdn_url_val}");
  formData.append("show_cover_pic0", "{show_cover}");
  formData.append("need_open_comment0", "0");
  formData.append("only_fans_can_comment0", "0");
  formData.append("isneedsave", "0");

  xhr.open("POST", url, false);
  xhr.send(formData);

  try {{
    return JSON.parse(xhr.responseText);
  }} catch(e) {{
    return {{error: xhr.responseText.substring(0, 500), status: xhr.status}};
  }}
}})()'''

        try:
            result = self._eval_js(js_code)
        except Exception as e:
            return {"success": False, "error": f"CDP 请求失败: {e}"}

        ret = result.get("ret", result.get("base_resp", {}).get("ret", -1))
        if str(ret) == "0":
            return {
                "success": True,
                "app_msg_id": result.get("appMsgId"),
                "raw": result,
            }
        else:
            return {
                "success": False,
                "error": f"创建草稿失败 (ret={ret})",
                "raw": result,
            }

    def list_drafts(self, count: int = 10) -> list[dict]:
        """获取草稿箱列表。

        Returns:
            草稿列表，每项包含 app_id, title, digest, create_time 等
        """
        if not self._ensure_session():
            return []

        js_code = f'''(() => {{
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "https://mp.weixin.qq.com/cgi-bin/appmsg?begin=0&count={count}&type=77&action=list_card&token={self.token}&lang=zh_CN&f=json&ajax=1", false);
  xhr.send();
  return JSON.parse(xhr.responseText);
}})()'''

        try:
            result = self._eval_js(js_code)
        except Exception:
            return []

        items = result.get("app_msg_info", {}).get("item", [])
        return items

    def delete_draft(self, app_msg_id: int) -> bool:
        """删除指定草稿。"""
        if not self._ensure_session():
            return False

        js_code = f'''(() => {{
  var xhr = new XMLHttpRequest();
  var url = "https://mp.weixin.qq.com/cgi-bin/operate_appmsg?sub=del&t=ajax-response&token={self.token}&lang=zh_CN";
  var formData = new FormData();
  formData.append("AppMsgId", "{app_msg_id}");
  formData.append("token", "{self.token}");
  formData.append("lang", "zh_CN");
  formData.append("f", "json");
  formData.append("ajax", "1");

  xhr.open("POST", url, false);
  xhr.send(formData);
  return JSON.parse(xhr.responseText);
}})()'''

        try:
            result = self._eval_js(js_code)
            ret = str(result.get("ret", result.get("base_resp", {}).get("ret", -1)))
            return ret == "0"
        except Exception:
            return False

    def has_today_draft(self, today_date: str) -> bool:
        """检查草稿箱中是否已有今日稿件（按标题中的日期判断）。"""
        drafts = self.list_drafts()
        for draft in drafts:
            title = draft.get("title", "")
            if today_date in title:
                return True
        return False

    # ──────────────────────────────────────────────
    # 封面图
    # ──────────────────────────────────────────────

    def _get_upload_ticket(self) -> dict:
        """从编辑器页面提取上传所需的 ticket 信息。"""
        js_code = f'''(() => {{
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&token={self.token}&lang=zh_CN", false);
  xhr.send();
  var text = xhr.responseText;
  var ticketMatch = text.match(/ticket\\s*[:=]\\s*"([^"]+)"/);
  var userNameMatch = text.match(/user_name\\s*[:=]\\s*"([^"]+)"/);
  var timeMatch = text.match(/svr_time\\s*[:=]\\s*"?(\\d+)"?/);
  return {{
    ticket: ticketMatch ? ticketMatch[1] : null,
    user_name: userNameMatch ? userNameMatch[1] : null,
    svr_time: timeMatch ? timeMatch[1] : null
  }};
}})()'''
        return self._eval_js(js_code)

    def upload_cover(self, image_path: str) -> dict:
        """上传封面图到公众号素材库。

        Args:
            image_path: 本地图片文件路径

        Returns:
            {"success": True, "fileid": str, "cdn_url": str} 或 {"success": False, ...}
        """
        import base64

        if not self._ensure_session():
            return {"success": False, "error": "无法连接公众号后台"}

        # 读取图片并转 base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("ascii")

        # 获取上传凭证
        ticket_info = self._get_upload_ticket()
        ticket = ticket_info.get("ticket", "")
        user_name = ticket_info.get("user_name", "")
        svr_time = ticket_info.get("svr_time", "")

        if not ticket:
            return {"success": False, "error": "无法获取上传凭证 ticket"}

        # 通过浏览器上传
        js_code = f'''(() => {{
  var b64 = "{img_b64}";
  var byteChars = atob(b64);
  var byteNumbers = new Array(byteChars.length);
  for (var i = 0; i < byteChars.length; i++) {{
    byteNumbers[i] = byteChars.charCodeAt(i);
  }}
  var byteArray = new Uint8Array(byteNumbers);
  var blob = new Blob([byteArray], {{type: "image/png"}});

  var formData = new FormData();
  formData.append("file", blob, "cover.png");

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "https://mp.weixin.qq.com/cgi-bin/filetransfer?action=upload_material&f=json&scene=1&writetype=doublewrite&groupid=1&ticket_id={user_name}&ticket={ticket}&svr_time={svr_time}&token={self.token}&lang=zh_CN&seq=1", false);
  xhr.send(formData);

  try {{
    return JSON.parse(xhr.responseText);
  }} catch(e) {{
    return {{error: xhr.responseText.substring(0, 500), status: xhr.status}};
  }}
}})()'''

        try:
            result = self._eval_js(js_code)
        except Exception as e:
            return {"success": False, "error": f"上传失败: {e}"}

        ret = result.get("base_resp", {}).get("ret", -1)
        if ret == 0:
            return {
                "success": True,
                "fileid": str(result.get("content", "")),
                "cdn_url": result.get("cdn_url", ""),
            }
        else:
            return {"success": False, "error": f"上传失败 (ret={ret})", "raw": result}

    @staticmethod
    def generate_cover(
        bundle_date: str,
        count: int,
        output_path: str,
    ) -> str:
        """生成公众号封面图（900x383，深蓝底 + 红色点缀）。

        Returns:
            输出文件路径
        """
        from PIL import Image, ImageDraw, ImageFont
        import os

        width, height = 900, 383
        img = Image.new("RGB", (width, height), "#1a1a2e")
        draw = ImageDraw.Draw(img)

        # 底部装饰条
        draw.rectangle([(0, height - 6), (width, height)], fill="#c0392b")

        # 加载系统中文字体
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
        ]
        font_large = font_small = font_tag = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font_large = ImageFont.truetype(fp, 42)
                    font_small = ImageFont.truetype(fp, 20)
                    font_tag = ImageFont.truetype(fp, 16)
                    break
                except Exception:
                    continue

        if not font_large:
            font_large = ImageFont.load_default()
            font_small = font_large
            font_tag = font_large

        # 绘制内容
        draw.text((width // 2, 80), "DAILY AI BRIEFING", fill="#c0392b",
                  font=font_small, anchor="mm")
        draw.text((width // 2, 170), "今日 AI 资讯速览", fill="#ffffff",
                  font=font_large, anchor="mm")
        draw.text((width // 2, 240),
                  f"{bundle_date} · 精选 {count} 条 · 编辑点评版",
                  fill="#888888", font=font_small, anchor="mm")
        # 分隔线
        draw.line([(width // 2 - 30, 290), (width // 2 + 30, 290)],
                  fill="#c0392b", width=2)
        draw.text((width // 2, 330), "自动采集 · Claude 编辑点评 · 每日更新",
                  fill="#555555", font=font_tag, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    # ──────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────

    @staticmethod
    def _escape_js(text: str) -> str:
        """转义字符串，使其可以安全嵌入 JS 双引号字符串中。"""
        return (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
