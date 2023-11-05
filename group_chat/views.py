from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Group, GroupMember
from common.models import User
from .serializers import GroupSerializer
import random
from django.core.files.base import ContentFile


class AddGroupAPI(generics.CreateAPIView):
    """
    创建群组
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # 解析请求数据，将 QueryDict 转换为可变字典
        group_data = request.data
        member_data = group_data.pop('members', [])

        # 获取当前登录用户
        current_user = self.request.user

        # 生成唯一的群组号
        group_data['group_number'] = self.generate_unique_group_number()

        # 将群组头像设置为默认图像
        group_data['avatar'] = self.default_group_avatar()

        # 创建群组
        group_serializer = self.get_serializer(data=group_data)
        if group_serializer.is_valid():
            group = group_serializer.save()

            # 创建群主
            GroupMember.objects.create(
                group=group,
                user=current_user,
                member_level='owner'
            )

            # 添加其他多名用户为普通群成员
            # member_data = request.data.get('members', [])
            for member_id in member_data:
                try:
                    member_id = int(member_id)
                    member = User.objects.get(id=member_id)
                    GroupMember.objects.create(
                        group=group,
                        user=member,
                        member_level='member'  # 设置为普通群成员
                    )
                except User.DoesNotExist:
                    pass

            return Response({'status': 201, 'data': group_serializer.data, 'member_data': member_data}, status=status.HTTP_201_CREATED)
        return Response({'status': 400, 'error': group_serializer.errors}, status=400)

    def generate_unique_group_number(self):
        # 生成随机的六位数字
        while True:
            group_number = str(random.randint(100000, 999999))
            if not Group.objects.filter(group_number=group_number).exists():
                return group_number

    def default_group_avatar(self):
        # 定义静态文件中默认头像图像的路径
        default_avatar_path = 'media/avatar/group_avatar.jpg'

        # 获取默认头像文件的内容
        with open(default_avatar_path, "rb") as avatar_file:

            avatar_content = avatar_file.read()

            # 将默认头像保存为群组头像
            default_avatar = ContentFile(avatar_content)
            default_avatar.name = 'group_avatar.jpg'
            return default_avatar
