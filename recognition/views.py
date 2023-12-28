import json
from django_redis import get_redis_connection
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from PicCheck import settings
from recognition.models import CrackDetection, FileinUser
from recognition.serializers import SaveGallerySerializer
from recognition import utils as dis_utils
import base64
from io import BytesIO
from PIL import Image
import os
import datetime
import time

from django.shortcuts import render

from xhtml2pdf import pisa

from django.core.files.base import ContentFile

import logging

from recognition.tasks import crack_detection

logger = logging.getLogger(__name__)

# 链接redis数据库
redis_conn = get_redis_connection("default")


class CrackDetectionShow(APIView):
    """
    裂缝检测图片显示
    """
    def post(self, *args, **kwargs):
        image = self.request.FILES.get('image')
        with image.open() as storage_f:
            img_bytes = storage_f.read()
            # results = crack_detection(img_bytes)
            # box_s = dict(results)
            # 上面代码涉及算法的调用，不要删除
            box_s = dict({'result': [[445, 273, 489, 424, 0.5890567302703857, 3], [207, 1, 309, 500, 0.7012394070625305, 0]], 'names': {'0': '裂缝', '1': '空洞、气孔', '2': '拼缝漏浆、底部漏浆', '3': '蜂窝、麻面'}})

            img = dis_utils.convert_opened_file_to_image(image.open())
            handler = dis_utils.CrackDetectionDispose(img, box_s)
            img_new = handler.draw()
            img_new_base64 = self.make_image_response(img_new)
            print(img_new_base64, type(img_new_base64))  # str

            cache_key = f'image_cache:{image.name}'
            # 将数据转化为 JSON 格式并存储在 Redis 中，设置过期时间
            cache_data = {'box_s': box_s, 'img_new_base64': img_new_base64}
            # cache_data = {'box_s': box_s}
            redis_conn.setex(cache_key, 3600000, json.dumps(cache_data))  # 设置缓存过期时间为1小时
        return dis_utils.make_image_response(img_new)

    def make_image_response(self, image: Image):
        result_content: BytesIO = BytesIO()
        image.save(result_content, "png")
        result_content = result_content.getvalue()
        base64_img = base64.b64encode(result_content).decode('utf-8')
        return base64_img


class GetBoxSAPIView(APIView):
    """
    裂缝检测结果说明
    """
    def get(self, request):
        # 从请求中获取image名字
        image_name = request.GET.get('image_name')
        # 生成缓存键，使用image的唯一标识作为键
        cache_key = 'image_cache:%s' % image_name

        # 从缓存中获取box_s数据
        box_s_data = redis_conn.get(cache_key)

        if box_s_data is not None:
            data = json.loads(box_s_data)
            print(data)
            result_data = data['box_s']['result']
            result_name = data['box_s']['names']
            result = {}
            for n in range(len(result_data)):
                result[n + 1] = result_name[str(result_data[n][5])]

            # 如果缓存中存在数据，将其解析为Python对象
            return Response({'status': 200, 'result': result}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 404, 'error': 'Data not found in cache.'}, status=status.HTTP_404_NOT_FOUND)


class SaveGalleryAPI(generics.CreateAPIView):
    """
    保存识别图像到图库中
    """
    permission_classes = [IsAuthenticated]  # 控制访问权限
    queryset = CrackDetection.objects.all()
    serializer_class = SaveGallerySerializer

    def perform_create(self, serializer):
        # 从请求中获取image_name
        image_name = self.request.data.get('image_name')
        print(image_name)

        # 从 Redis 缓存中获取 box_s 和 img_new 数据
        # 生成缓存键，使用image的唯一标识作为键
        cache_key = 'image_cache:%s' % image_name
        cached_data = redis_conn.get(cache_key)
        data = json.loads(cached_data)

        if data is None:
            raise serializers.ValidationError({'error': 'Data not found in cache.'})

        # 从缓存中获取新图片的base64字符串
        img_new_base64 = data['img_new_base64']
        # 解码base64字符串
        data_dict = base64.b64decode(img_new_base64)
        # 将图像数据转换为PIL图像对象
        img_new = Image.open(BytesIO(data_dict))

        # 获取当前时间戳并将其转换为字符串
        timestamp = str(int(time.time()))
        # 生成一个唯一的文件名
        file_name = timestamp + '_' + image_name
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        file_path = os.path.join('uploads/', 'users/', date_str + '/' + file_name)
        folder_path = os.path.join(settings.MEDIA_ROOT, 'uploads/', 'users/', date_str).replace('\\', "/")
        # 如果文件夹不存在，创建
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        img_new.save(os.path.join(folder_path, file_name))

        # 计算文件大小（以字节为单位）
        img_new_size = os.path.getsize(os.path.join(folder_path, file_name))

        # 设置文件名、文件路径和文件大小到 validated_data 中
        serializer.validated_data['img_new_name'] = image_name
        serializer.validated_data['img_new'] = file_path
        serializer.validated_data['img_new_size'] = img_new_size

        # 关联上传的文件与当前登录用户
        serializer.validated_data['user'] = self.request.user

        # 调用父类的 perform_create 方法保存文件
        super().perform_create(serializer)

        response_data = {
            'img_new_name': serializer.validated_data['img_new_name'],
            'img_new': serializer.validated_data['img_new'],
            'img_new_size': serializer.validated_data['img_new_size'],
        }

        return Response({'status': 201, 'data': response_data}, status=status.HTTP_201_CREATED)


def font_patch():
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from xhtml2pdf.default import DEFAULT_FONT
    # 注册自定义字体
    font_path = f"{settings.BASE_DIR}/NotoSansSC-VariableFont_wght.ttf"
    pdfmetrics.registerFont(TTFont('NotoSansSC-VariableFont_wght', font_path))
    DEFAULT_FONT['helvetica'] = 'NotoSansSC-VariableFont_wght'


class GeneratePDFAPI(APIView):
    """
    上传pdf文件到个人文件中
    """
    def post(self, request, *args, **kwargs):
        # 获取HTML富文本内容
        html_content = self.request.data.get('html_content')
        print(html_content)
        # 从请求中获取image_name
        image_name = self.request.data.get('image_name')
        print(image_name)

        # 从 Redis 缓存中获取 box_s 和 img_new 数据
        # 生成缓存键，使用image的唯一标识作为键
        cache_key = 'image_cache:%s' % image_name
        cached_data = redis_conn.get(cache_key)
        data = json.loads(cached_data)
        date_str = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")

        if data is None:
            raise serializers.ValidationError({'error': 'Data not found in cache.'})

        # 从缓存中获取新图片的base64字符串
        img_new_base64 = data['img_new_base64']
        # 解码base64字符串
        data_dict = base64.b64decode(img_new_base64)
        # 将图像数据转换为PIL图像对象
        img_new = Image.open(BytesIO(data_dict))
        img_new_buffer = BytesIO()
        img_new.save(img_new_buffer, "JPEG")
        img_new_data = img_new_buffer.getvalue()

        image_data = base64.b64encode(img_new_data).decode()

        result_data = data['box_s']['result']
        result_name = data['box_s']['names']
        result = {}
        for n in range(len(result_data)):
            result[n + 1] = result_name[str(result_data[n][5])]
        result_list = list(result.items())
        print(result_list, type)

        # 渲染HTML模板
        image_no_extension, extension = os.path.splitext(image_name)
        html_template = os.path.join(settings.BASE_DIR, 'templates', 'pdf_template.html')
        context = {
            'image_name': image_no_extension,
            'date_time': date_str,
            'image_data': image_data,
            'result_list': result_list,
            'frontend_html_content': html_content,
        }
        rendered_html = render(request, html_template, context)

        # 创建PDF文档
        pdf_buffer = BytesIO()
        # 生成PDF
        # font_patch()
        pdf = pisa.CreatePDF(BytesIO(rendered_html.content), pdf_buffer)

        # 保存 PDF 到数据库
        if not pdf.err:
            pdf_buffer.seek(0)
            pdf_file = FileinUser(
                file_name=image_no_extension+".pdf",
                file=ContentFile(pdf_buffer.read(), name=image_no_extension+".pdf")
            )
            pdf_file.save()
            return Response({'status': 201, 'message': 'PDF generated and saved successfully', 'file': '/media/' + pdf_file.file.name}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 500, 'error': 'PDF generation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
