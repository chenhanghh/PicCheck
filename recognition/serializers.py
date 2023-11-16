from rest_framework import serializers

from .models import CrackDetection


class SaveGallerySerializer(serializers.ModelSerializer):
    # 自动将当前请求的用户关联到user字段
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CrackDetection
        fields = ('user', 'create_date')
