import warnings
from typing import Dict
from django.conf import settings
import requests

import logging

logger = logging.getLogger('django')


# 自定义异常类
class CrackDetectionRpcCallE(Exception):
    _code: int
    _content: str

    def __init__(self, code, content):
        self._code = code
        self._content = content
        super().__init__()

    def __str__(self):
        return f"{{ \r\n\tcode={self._code},\r\n\tcontent={self._content}\r\n}}"


# 调用裂缝检测算法并返回结果
def crack_detection(img_bytes) -> Dict:
    """
    裂缝检测得RPC(http) 调用
    Args:
        img_bytes: 文件内容,二进制对象

    Returns:

    """
    crack_detect_url = settings.ALGORITHM_URL
    if crack_detect_url is None:
        warnings.warn("裂缝检测RPC 配置未完成")
        return []

    response = requests.post(crack_detect_url,
                             data=img_bytes, timeout=(3, 8))
    if response.status_code == 200:
        # 处理正确
        return response.json()
    raise CrackDetectionRpcCallE(code=response.status_code,
                                 content=response.content)
