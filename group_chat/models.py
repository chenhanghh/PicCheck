from django.utils import timezone
from django.db import models
from common.models import User


class Group(models.Model):
    """
    群组
    """
    name = models.CharField(max_length=50, verbose_name='群名称')
    group_number = models.CharField(max_length=20, unique=True, verbose_name='群号')
    description = models.CharField(max_length=100, verbose_name='群描述')
    avatar = models.ImageField(upload_to='uploads/group_avatars/%Y%m%d/', null=True, blank=True, verbose_name='群头像')
    announcement = models.TextField(null=True, blank=True, verbose_name='群公告')  # 不限制文本长度
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建日期')
    members = models.ManyToManyField(User, through='GroupMember', verbose_name='群组包含成员')


class GroupMember(models.Model):
    """
    群成员，同时定义不同的成员等级
    """
    MEMBER_CHOICES = (
        ('owner', '群主'),
        ('admin', '管理员'),
        ('member', '普通群成员'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 这里先为数据库用户，后等私聊添加联系人功能存在后，将用户限制在该用户添加的联系人范围？
    member_level = models.CharField(max_length=10, choices=MEMBER_CHOICES, verbose_name='群成员等级')


class Emoji(models.Model):
    name = models.CharField(max_length=50, verbose_name='emoji名称')
    image = models.ImageField(upload_to='uploads/chat_content/emoji_images/%Y%m%d/', verbose_name='emoji图像保存路径')


class GroupMessage(models.Model):
    """
    群聊天内容，包括文字、语音、表情包、图片、视频、文件和链接
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='群组id')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='聊天内容所属成员')
    message_type = models.CharField(max_length=20, verbose_name='聊天内容类型')  # 可以是文字、语音、表情包、图片、视频、文件、链接

    text_content = models.TextField(null=True, blank=True, verbose_name='文字消息内容')  # 不限制文本长度
    emojis_content = models.ManyToManyField(Emoji, blank=True, verbose_name='emoji消息内容')
    voice_content = models.FileField(upload_to='uploads/chat_content/voice_messages/%Y%m%d/', null=True, blank=True, verbose_name='语音消息内容')
    image_content = models.ImageField(upload_to='uploads/chat_content/images/%Y%m%d/', null=True, blank=True, verbose_name='图片消息内容')
    video_content = models.FileField(upload_to='uploads/chat_content/videos/%Y%m%d/', null=True, blank=True, verbose_name='视频消息内容')
    file_content = models.FileField(upload_to='uploads/chat_content/files/%Y%m%d/', null=True, blank=True, verbose_name='文件消息内容')
    link_content = models.URLField(null=True, blank=True, verbose_name='链接消息内容')

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')


class GroupEmoji(models.Model):
    group_message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE)
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE)
