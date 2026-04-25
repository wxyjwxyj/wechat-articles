"""项目统一异常层级。

设计原则：
- 所有自定义异常继承 News1Error
- 每种异常关联一个 exit code，供入口脚本 sys.exit() 使用
- 采集器、流水线、发布器分别使用各自的异常子类
- 保持向后兼容：现有 return [] 的地方改为 raise，调用方 catch 后决定是否降级

Exit Code 规划（0=成功，1=通用错误）：
  10  CDP Proxy 连接失败
  11  微信登录态过期 / token 缺失
  12  采集超时或网络错误
  13  AI API 调用失败（Claude / OpenAI）
  14  公众号草稿提交失败
  15  数据处理 / bundle 生成失败
"""


class News1Error(Exception):
    """项目基础异常，所有自定义异常的父类。"""
    exit_code: int = 1

    def __init__(self, message: str = "", *, exit_code: int | None = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


# ── 采集阶段 ──────────────────────────────────────


class CollectorError(News1Error):
    """采集器通用错误。"""
    exit_code = 12


class CDPConnectionError(CollectorError):
    """CDP Proxy 连接失败（未运行 / 不可达）。"""
    exit_code = 10


class LoginExpiredError(CollectorError):
    """微信公众平台登录态过期或 token 缺失。"""
    exit_code = 11


class FetchTimeoutError(CollectorError):
    """采集请求超时。"""
    exit_code = 12


# ── 流水线阶段 ────────────────────────────────────


class PipelineError(News1Error):
    """数据处理流水线错误（去重 / 打标签 / bundle）。"""
    exit_code = 15


class AIApiError(PipelineError):
    """Claude / OpenAI 等 AI API 调用失败。"""
    exit_code = 13


# ── 发布阶段 ──────────────────────────────────────


class PublishError(News1Error):
    """公众号草稿发布相关错误。"""
    exit_code = 14


# ── 辅助函数 ──────────────────────────────────────


# exit code → 中文描述，供 shell 脚本或日志使用
EXIT_CODE_MAP: dict[int, str] = {
    0:  "成功",
    1:  "未知错误",
    10: "CDP Proxy 未运行",
    11: "微信登录态过期",
    12: "采集超时/网络错误",
    13: "AI API 调用失败",
    14: "草稿提交失败",
    15: "数据处理失败",
}


def exit_code_desc(code: int) -> str:
    """根据 exit code 返回中文描述。"""
    return EXIT_CODE_MAP.get(code, f"未知错误 (code={code})")
