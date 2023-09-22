# 定义数据库表 项目所需要的公共表
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    gender_ = (
        ('male', '男'),
        ('female', '女'),
    )
    # 账号
    nickname = models.CharField(max_length=128)
    # 电话号码
    phonenumber = models.CharField(max_length=32, unique=True)
    # 职位
    position = models.CharField(max_length=128)
    # 性别
    gender = models.CharField(max_length=32, choices=gender_, default='男')
    # 地区
    scope = models.CharField(max_length=256)

    # 创建超级管理员必须输入的字段
    REQUIRED_FIELDS = ['phonenumber']

    def __str__(self):
        return self.username


class Project(models.Model):
    # 项目名称
    name = models.CharField(max_length=50)
    # 创建日期
    create_date = models.DateTimeField(default=timezone.now)
    # 项目中包含的用户，和User表是多对多的关系
    users = models.ManyToManyField(User, through='ProjectUser')

    userlist = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


class ProjectUser(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)


class Folder(models.Model):
    # 文件夹名
    title = models.CharField(max_length=50)
    # 创建日期
    create_date = models.DateTimeField(default=timezone.now)
    # 文件夹所属项目 一对多关系
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # 形成递归结构，允许在文件夹内创建子文件夹
    parent_folder = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class File(models.Model):
    # 文件名
    title = models.CharField(max_length=50)
    # 文件所属文件夹 一对多关系
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    # 文件
    file = models.FileField(upload_to='uploads/%Y%m%d/', null=True, blank=True)
    # 文件大小
    size = models.CharField(max_length=50)
    # 创建时间
    create_date = models.DateTimeField(default=timezone.now)
    # 文件所属用户 一对多关系
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    # 文件所属项目
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
