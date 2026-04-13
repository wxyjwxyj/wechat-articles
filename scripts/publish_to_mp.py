"""将公众号稿件提交到微信公众号草稿箱（含自动生成封面图）。

用法：
  python scripts/publish_to_mp.py                  # 正常提交
  python scripts/publish_to_mp.py --dry-run         # 只预览不提交
  python scripts/publish_to_mp.py --force           # 忽略已有草稿强制重建
  python scripts/publish_to_mp.py path/to/preview.json  # 指定稿件文件

读取 mp_article_preview.json，自动生成封面图并上传，
通过 CDP Proxy 调用公众号后台接口创建带封面的草稿。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from publishers.mp_publisher import MpPublisher
from utils.config import load_project_config
from utils.errors import News1Error, PublishError
from utils.log import get_logger

logger = get_logger(__name__)

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_PREVIEW = PROJECT_DIR / "mp_article_preview.json"
COVER_PATH = PROJECT_DIR / "cover_today.png"


def main() -> None:
    # 解析参数
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    preview_path = Path(args[0]) if args else DEFAULT_PREVIEW

    if not preview_path.exists():
        logger.warning("稿件文件不存在：%s", preview_path)
        return

    # 读取稿件
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    title = preview.get("title", "")
    body_html = preview.get("body_html", "")
    bundle_date = preview.get("bundle_date", "")

    if not title or not body_html:
        logger.warning("稿件内容为空，跳过")
        return

    # 生成摘要（取 commentary 的第一条，或用默认）
    commentary = preview.get("commentary", [])
    digest = commentary[0] if commentary else f"AI 资讯精选 · {bundle_date}"
    # 微信摘要最多 120 字
    if len(digest) > 120:
        digest = digest[:117] + "..."

    # 文章条数
    count = len(commentary) if commentary else 8

    logger.info("稿件信息：标题=%s, 摘要=%s, 正文长度=%d, 日期=%s",
                title, digest, len(body_html), bundle_date)

    if dry_run:
        logger.info("[Dry Run] 仅预览，不提交到草稿箱")
        return

    # 连接公众号后台
    config = load_project_config()
    cdp_proxy = config.get("cdp_proxy", "http://localhost:3456")
    publisher = MpPublisher(cdp_proxy=cdp_proxy)

    # 检查是否已有同日草稿
    if bundle_date and publisher.has_today_draft(bundle_date):
        if force:
            logger.info("--force 模式，忽略已有草稿，继续创建")
        else:
            logger.warning("草稿箱中已存在包含 %s 的草稿，跳过创建（如需重新创建请先删除旧草稿或加 --force）", bundle_date)
            return

    # 生成封面图
    logger.info("生成封面图...")
    try:
        MpPublisher.generate_cover(
            bundle_date=bundle_date,
            count=count,
            output_path=str(COVER_PATH),
        )
        logger.info("封面图 → %s", COVER_PATH)
    except Exception as e:
        logger.warning("封面图生成失败（%s），使用纯色兜底封面", e)
        try:
            from PIL import Image
            Image.new("RGB", (900, 383), "#1a1a2e").save(str(COVER_PATH), "PNG")
        except Exception:
            logger.warning("兜底封面也失败，将创建无封面草稿")

    # 上传封面图
    cover_fileid = ""
    cover_cdn_url = ""
    if COVER_PATH.exists():
        logger.info("上传封面图...")
        upload_result = publisher.upload_cover(str(COVER_PATH))
        if upload_result["success"]:
            cover_fileid = upload_result["fileid"]
            cover_cdn_url = upload_result["cdn_url"]
            logger.info("封面图上传成功 fileid=%s", cover_fileid)
        else:
            logger.warning("上传失败（%s），将创建无封面草稿", upload_result.get('error'))

    # 创建草稿
    logger.info("正在提交到草稿箱...")
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
        logger.info("草稿创建成功！AppMsgId=%s, 封面=%s", app_msg_id, "有" if cover_fileid else "无")
        logger.info("请到公众号后台草稿箱确认并发布：https://mp.weixin.qq.com/cgi-bin/appmsg?begin=0&count=10&type=77&action=list_card&token=%s&lang=zh_CN", publisher.token)
    else:
        error_msg = result.get('error', '未知错误')
        logger.error("草稿创建失败：%s", error_msg)
        if "raw" in result:
            logger.error("原始返回：%s", json.dumps(result['raw'], ensure_ascii=False)[:300])
        raise PublishError(f"草稿创建失败: {error_msg}")


if __name__ == "__main__":
    try:
        main()
    except News1Error as e:
        logger.error("发布失败: %s", e)
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error("未预期的错误: %s", e, exc_info=True)
        sys.exit(1)
