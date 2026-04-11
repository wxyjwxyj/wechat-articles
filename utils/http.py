"""带自动重试的 HTTP 工具。"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def retry_session(retries: int = 3, backoff: float = 1.0) -> requests.Session:
    """返回一个带指数退避重试的 requests Session。"""
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s
