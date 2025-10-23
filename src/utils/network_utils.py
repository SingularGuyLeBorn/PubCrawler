# FILE: src/utils/network_utils.py

import requests
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 获取一个简单的日志记录器，或者你可以从主配置中传递一个
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_session_with_retries(
    retries=5,
    backoff_factor=1,
    status_forcelist=(500, 502, 503, 504),
    session=None,
):
    """
    创建一个带有重试机制的 requests Session 对象。
    这对于处理临时的网络错误或服务器不稳定非常有效。
    """
    session = session or requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def robust_get(url: str, timeout: int = 30, retries: int = 5, backoff_factor: float = 1.0):
    """
    一个健壮的 GET 请求函数，集成了重试和更长的超时。
    :param url: 要请求的 URL
    :param timeout: 单次请求的超时时间（秒）
    :param retries: 最大重试次数
    :param backoff_factor: 重试的退避因子 (e.g., 1s, 2s, 4s...)
    :return: requests.Response 对象或 None
    """
    session = get_session_with_retries(retries=retries, backoff_factor=backoff_factor)
    try:
        response = session.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()  # 如果状态码是 4xx 或 5xx，则抛出异常
        return response
    except requests.exceptions.RequestException as e:
        # 使用 logger.error 而不是 print，以便记录到日志文件
        logger.error(f"    [✖ NETWORK ERROR] 请求失败，已达到最大重试次数 for URL: {url}. Error: {e}")
        return None