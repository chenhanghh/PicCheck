from unittest import skipIf

import os
from rest_framework.test import APITestCase
from .tasks import crack_detection

TEST_UPLOAD_IMAGE = os.path.join("media", "tests", "crack_1.jpg")

# Create your tests here.


# 测试裂缝检测
class TestCrackPredict(APITestCase):
    @skipIf(not os.path.exists(TEST_UPLOAD_IMAGE), "测试图片不存在,跳过测试")
    def test_rpc_call(self):
        """
        完成 开发环境RPC 调用
        Returns:

        """
        with open(TEST_UPLOAD_IMAGE, "rb") as local_opened_f:
            results = crack_detection(local_opened_f.read())
        print(f"裂缝识别结果:{results}")
