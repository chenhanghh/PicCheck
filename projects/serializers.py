from rest_framework import serializers
from common.models import User, Project, FolderinProject, FileinProject


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderinProject
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


# 文件上传
class FileAddSerializer(serializers.ModelSerializer):
    # 自动将当前请求的用户关联到user字段
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FileinProject
        exclude = ('file_name', 'file_size')


# 批量删除文件
class FileDelSerializer(serializers.Serializer):
    file_ids = serializers.ListField(child=serializers.IntegerField())


# 获取文件信息
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileinProject
        fields = ('id', 'file_name', 'file_size', 'file')


# 文件夹重命名
class FolderRenameSerializer(serializers.Serializer):
    new_title = serializers.CharField(max_length=50)


# 文件夹信息
class FolderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderinProject
        fields = ('id', 'title', 'create_date')


# 文件信息
class FileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileinProject
        fields = ('id', 'file_name', 'file_size', 'create_date', 'user')


# 项目重命名
class ProjectRenameSerializer(serializers.Serializer):
    new_name = serializers.CharField(max_length=50)
