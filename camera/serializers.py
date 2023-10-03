from rest_framework import serializers
from common.models import User, FileinUser


# 图片上传
class ImageSerializer(serializers.ModelSerializer):
    # 自动将当前请求的用户关联到user字段
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FileinUser
        exclude = ('file_name', 'file_size')
