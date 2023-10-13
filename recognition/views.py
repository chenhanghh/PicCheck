from django.http import HttpResponse
import json

from django_redis import get_redis_connection
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from recognition.models import CrackDetection
from recognition.serializers import SaveDetectionSerializer
from recognition import utils as dis_utils

from recognition.tasks import crack_detection

import logging

logger = logging.getLogger(__name__)

# 链接redis数据库
redis_conn = get_redis_connection("default")


class ImagePreview(APIView):
    """
    配置图片预览接口
    """

    def get_image(self, *args, **kwargs):
        raise Exception()

    def get(self, request, *args, **kwargs):
        img = self.get_image(*args, **kwargs)
        if img is not None:
            return dis_utils.make_image_response(img)
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)


class CrackDetectionShow(ImagePreview):
    """
    裂缝检测图片显示
    """
    def get_image(self, *args, **kwargs):
        # 获取上传的图片对象
        image = self.request.FILES.get('image')

        with image.open() as storage_f:
            img_bytes = storage_f.read()
            results = crack_detection(img_bytes)
            box_s = dict(results)

            img = dis_utils.convert_opened_file_to_image(
                image.open()
            )
            handler = dis_utils.CrackDetectionDispose(img,
                                                      box_s)
            img_new = handler.draw()

            cache_key = 'image_cache:%s' % image.name
            # 将数据转化为 JSON 格式并存储在 Redis 中，设置过期时间
            cache_data = {
                'box_s': box_s,
            }
            redis_conn.setex(cache_key, 3600, json.dumps(cache_data))  # 设置缓存过期时间为1小时
        return img_new


class GetBoxSAPIView(APIView):
    """
    裂缝检测结果说明
    """
    def get(self, request):
        # 从请求中获取image对象或文件
        image = request.FILES.get('image')
        # 生成缓存键，使用image的唯一标识作为键
        cache_key = 'image_cache:%s' % image.name

        # 从缓存中获取box_s数据
        box_s_data = redis_conn.get(cache_key)
        data = json.loads(box_s_data)

        if box_s_data is not None:
            result_data = data['box_s']['result']
            result_name = data['box_s']['names']
            result = {}
            for n in range(len(result_data)):
                result[n+1] = result_name[str(result_data[n][5])]

            # 如果缓存中存在数据，将其解析为Python对象
            return Response({'result': result}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Data not found in cache.'}, status=status.HTTP_404_NOT_FOUND)


class SaveDetectionAPI(generics.CreateAPIView):
    """
    保存原始图像、检测说明
    """
    permission_classes = [IsAuthenticated]  # 控制访问权限
    queryset = CrackDetection.objects.all()
    serializer_class = SaveDetectionSerializer

    def perform_create(self, serializer):
        # 获取上传的文件对象
        image = self.request.FILES.get('image')

        # 设置文件名称和大小到 validated_data 中
        serializer.validated_data['image_name'] = image.name
        serializer.validated_data['image_size'] = image.size

        # 从 Redis 缓存中获取 box_s 和 img_new 数据
        cache_key = 'image_cache:%s' % image.name
        cached_data = redis_conn.get(cache_key)
        data = json.loads(cached_data)

        if data is None:
            raise serializers.ValidationError({'error': 'Data not found in cache.'})

        box_s = data['box_s']

        # 设置box_s到 validated_date 中
        serializer.validated_data['box_s'] = box_s

        # 关联上传的文件与当前登录用户
        serializer.validated_data['user'] = self.request.user

        # 调用父类的 perform_create 方法保存文件
        super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            response_data = response.data
            return Response({'message': 'Detection saved successfully', 'data': response_data},
                            status=status.HTTP_201_CREATED)
        return response
