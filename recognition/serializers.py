from rest_framework import serializers

from .models import CrackDetection


class CrackDetectionSerializer(serializers.ModelSerializer):
    """
    裂缝识别序列化结果
    """

    class Meta:
        model = CrackDetection
        fields = [
            "id",
            "box_s",
        ]


class SaveDetectionSerializer(serializers.ModelSerializer):
    # 自动将当前请求的用户关联到user字段
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CrackDetection
        exclude = ('image_name', 'image_size', 'box_s')
