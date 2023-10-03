from django.db import transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from common.models import FileinUser
from recognition.models import CrackDetection
from recognition.serializers import CrackDetectionSerializer
from recognition import utils as dis_utils

from recognition.tasks import crack_detection

import logging

logger = logging.getLogger(__name__)


class CrackDetectionAPI(APIView):
    """
    上传图片的裂缝检测接口
    """

    def post(self, request):
        file_id = request.data.get("file_id")
        user_id = request.data.get("user_id")

        try:
            with transaction.atomic():
                file_row = FileinUser.objects.get(id=file_id)
                with file_row.file.open() as storage_f:
                    img_bytes = storage_f.read()
                    results = crack_detection(img_bytes)
                    results_instance = CrackDetection.objects.update_or_create(
                        defaults=dict(box_s=results),
                        photo_id=file_id, user_id=user_id,
                    )
                    logger.info("update or create result:%s", results_instance)

                    return Response(
                        {"message": "Crack detection completed successfully"},
                        status=status.HTTP_200_OK
                    )
        except FileinUser.DoesNotExist:
            return Response(
                {"message": f"FileinUser with id {file_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error("Error during crack detection: %s", str(e))
            return Response(
                {"message": "An error occurred during crack detection"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


class CrackDetectionRestfulAPI(ModelViewSet):
    """
    裂缝识别结果信息
    """
    lookup_field = "photo"
    queryset = CrackDetection.objects.all()
    serializer_class = CrackDetectionSerializer


class CrackDetectionShow(ImagePreview):
    """
    预览裂缝识别
    """
    permission_classes = []  # 代表不需要任何特性的权限或认证

    def get_image(self, *args, **kwargs):
        row_id = kwargs.get("row_id")
        if not row_id:
            return None

        crack_detection: CrackDetection = CrackDetection.objects.get(id=row_id)
        img = dis_utils.convert_opened_file_to_image(
            crack_detection.photo.file.open()
        )
        handler = dis_utils.CrackDetectionDispose(img,
                                                  crack_detection.box_s)
        img_new = handler.draw()
        return img_new

