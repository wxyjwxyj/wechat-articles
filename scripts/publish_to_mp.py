"""将公众号稿件提交到微信公众号草稿箱（含自动生成封面图）。

用法：
  python scripts/publish_to_mp.py                  # 正常提交
  python scripts/publish_to_mp.py --dry-run         # 只预览不提交
  python scripts/publish_to_mp.py path/to/preview.json  # 指定稿件文件

读取 mp_article_preview.json，自动生成封面图并上传，
通过 CDP Proxy 调用公众号后台接口创建带封面的草稿。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from publishers.mp_publisher import MpPublisher

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_PREVIEW = PROJECT_DIR / "mp_article_preview.json"
CONFIG_PATH = PROJECT_DIR / "config.json"
COVER_PATH = PROJECT_DIR / "cover_today.png"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def main() -> None:
    # 解析参数
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    preview_path = Path(args[0]) if args else DEFAULT_PREVIEW

    if not preview_path.exists():
        print(f"⚠ 稿件文件不存在：{preview_path}")
        return

    # 读取稿件
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    title = preview.get("title", "")
    body_html = preview.get("body_html", "")
    bundle_date = preview.get("bundle_date", "")

    if not title or not body_html:
        print("⚠ 稿件内容为空，跳过")
        return

    # 生成摘要（取 commentary 的第一条，或用默认）
    commentary = preview.get("commentary", [])
    digest = commentary[0] if commentary else f"AI 资讯精选 · {bundle_date}"
    # 微信摘要最多 120 字
    if len(digest) > 120:
        digest = digest[:117] + "..."

    # 文章条数
    count = len(commentary) if commentary else 8

    print(f"📝 稿件信息：")
    print(f"   标题：{title}")
    print(f"   摘要：{digest}")
    print(f"   正文长度：{len(body_html)} 字符")
    print(f"   日期：{bundle_date}")
    print()

    if dry_run:
        print("🔍 [Dry Run] 仅预览，不提交到草稿箱")
        return

    # 连接公众号后台
    config = load_config()
    cdp_proxy = config.get("cdp_proxy", "http://localhost:3456")
    publisher = MpPublisher(cdp_proxy=cdp_proxy)

    # 检查是否已有同日草稿
    if bundle_date and publisher.has_today_draft(bundle_date):
        print(f"⚠ 草稿箱中已存在包含 {bundle_date} 的草稿，跳过创建")
        print("   如需重新创建，请先在公众号后台删除旧草稿")
        return

    # 生成封面图
    print("🎨 生成封面图...")
    try:
        MpPublisher.generate_cover(
            bundle_date=bundle_date,
            count=count,
            output_path=str(COVER_PATH),
        )
        print(f"   ✓ 封面图 → {COVER_PATH}")
    except Exception as e:
        print(f"   ⚠ 封面图生成失败（{e}），将创建无封面草稿")

    # 上传封面图
    cover_fileid = ""
    cover_cdn_url = ""
    if COVER_PATH.exists():
        print("📤 上传封面图...")
        upload_result = publisher.upload_cover(str(COVER_PATH))
        if upload_result["success"]:
            cover_fileid = upload_result["fileid"]
            cover_cdn_url = upload_result["cdn_url"]
            print(f"   ✓ fileid={cover_fileid}")
        else:
            print(f"   ⚠ 上传失败（{upload_result.get('error')}），将创建无封面草稿")

    # 创建草稿
    print("📤 正在提交到草稿箱...")
    result = publisher.create_draft(
        title=title,
        content_html=body_html,
        digest=digest,
        author="AI日报",
        cover_fileid=cover_fileid,
        cover_cdn_url=cover_cdn_url,
    )

    if result["success"]:
        app_msg_id = result["app_msg_id"]
        print(f"✅ 草稿创建成功！")
        print(f"   AppMsgId: {app_msg_id}")
        if cover_fileid:
            print(f"   封面图: ✓")
        print(f"   👉 请到公众号后台草稿箱确认并发布：")
        print(f"   https://mp.weixin.qq.com/cgi-bin/appmsg?begin=0&count=10&type=77&action=list_card&token={publisher.token}&lang=zh_CN")
    else:
        print(f"❌ 草稿创建失败：{result.get('error', '未知错误')}")
        if "raw" in result:
            print(f"   原始返回：{json.dumps(result['raw'], ensure_ascii=False)[:300]}")


if __name__ == "__main__":
    main()
