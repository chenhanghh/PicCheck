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
