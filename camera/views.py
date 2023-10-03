from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from common.models import FileinUser
from .serializers import ImageSerializer
from rest_framework.response import Response


# 图片上传
class ImageUploadAPI(generics.CreateAPIView):
    queryset = FileinUser.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]  # 控制访问权限

    def perform_create(self, serializer):

        # 获取上传的文件对象
        uploaded_file = self.request.FILES.get('file')

        # 设置文件名称和大小到 validated_data 中
        serializer.validated_data['file_name'] = uploaded_file.name
        serializer.validated_data['file_size'] = uploaded_file.size

        # 关联上传的文件与当前登录用户
        serializer.validated_data['user'] = self.request.user

        # 调用父类的 perform_create 方法保存文件
        super().perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
