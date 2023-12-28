from rest_framework import serializers
from common.models import User, Project, FolderinProject, FileinProject, ProjectUser
from datetime import datetime


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
        exclude = ['invitation_code']


class UserinProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'position', 'gender', 'avatar')


class ProjectUserSerializer(serializers.ModelSerializer):
    user = UserinProjectSerializer()

    class Meta:
        model = ProjectUser
        fields = ('user', 'user_level')


class ProjectDetailSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['users']


# 文件上传
class FileAddSerializer(serializers.ModelSerializer):
    # 自动将当前请求的用户关联到user字段
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FileinProject
        exclude = ('title', 'file_size', 'type')


# 批量删除文件
class FileDelSerializer(serializers.Serializer):
    file_ids = serializers.ListField(child=serializers.IntegerField())


# 获取文件信息
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileinProject
        fields = ('id', 'title', 'file_size', 'file')


# 文件重命名
class FileRenameSerializer(serializers.Serializer):
    new_title = serializers.CharField(max_length=500)


# 文件夹重命名
class FolderRenameSerializer(serializers.Serializer):
    new_title = serializers.CharField(max_length=500)


# 创建时间格式修改
class CustomDateTimeField(serializers.Field):
    def to_representation(self, value):
        # 如果value已经是datetime对象
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        # 如果value是字符串
        elif isinstance(value, str):
            parsed_date = datetime.fromisoformat(value)
            return parsed_date.strftime('%Y-%m-%d %H:%M')
        # 其他情况
        else:
            return value  # 或者根据需要处理


# 文件夹信息
class FolderInfoSerializer(serializers.ModelSerializer):
    create_date = CustomDateTimeField()

    class Meta:
        model = FolderinProject
        fields = ('id', 'title', 'create_date', 'type')


# 文件信息
class FileInfoSerializer(serializers.ModelSerializer):
    create_date = CustomDateTimeField()

    class Meta:
        model = FileinProject
        fields = ('id', 'title', 'file_size', 'create_date', 'user', 'type')


# 项目重命名
class ProjectRenameSerializer(serializers.Serializer):
    new_name = serializers.CharField(max_length=500)
