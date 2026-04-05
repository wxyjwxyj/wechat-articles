"""统一的 logging 配置。

使用方式：
    from utils.log import get_logger
    logger = get_logger(__name__)
    logger.info("✓ 采集完成")
    logger.warning("⚠ 未找到数据")
    logger.error("✗ 请求失败: %s", e)

日志格式：[时间] 级别 模块名 - 消息
launchd 场景下输出到 stdout/stderr，由 daily_run.sh 重定向到日志文件。
"""
import logging
import sys

# 全局只配置一次
_configured = False


def get_logger(name: str) -> logging.Logger:
    """获取带统一格式的 logger。"""
    global _configured
    if not _configured:
        _configure_root()
        _configured = True
    return logging.getLogger(name)


def _configure_root() -> None:
    """配置 root logger：统一格式，输出到 stderr。"""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # 避免重复添加 handler
    if not root.handlers:
        root.addHandler(handler)
