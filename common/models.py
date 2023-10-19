# 定义数据库表 项目所需要的公共表
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    gender_ = (
        ('male', '男'),
        ('female', '女'),
    )

    nickname = models.CharField(max_length=128, verbose_name='昵称')
    phonenumber = models.CharField(max_length=32, verbose_name='电话号码', unique=True)
    position = models.CharField(max_length=128, verbose_name='职位', )
    gender = models.CharField(max_length=32, verbose_name='性别', choices=gender_, default='男')
    scope = models.CharField(max_length=256, verbose_name='地区', )
    avatar = models.ImageField(upload_to='uploads/avatar/%Y%m%d/', null=True, blank=True)

    # 创建超级管理员必须输入的字段
    REQUIRED_FIELDS = ['phonenumber']

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Project(models.Model):
    name = models.CharField(max_length=50, verbose_name='项目名称')
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建日期')
    # 项目中包含的用户，和User表是多对多的关系
    users = models.ManyToManyField(User, verbose_name='项目包含用户', through='ProjectUser')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProjectUser(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)


class FolderinProject(models.Model):
    title = models.CharField(max_length=50, verbose_name='文件夹名')
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建日期')
    project = models.ForeignKey(Project, verbose_name='所属项目', on_delete=models.CASCADE)
    # 形成递归结构，允许在文件夹内创建子文件夹
    parent_folder = models.ForeignKey('self', verbose_name='父文件夹', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '项目文件夹'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class FileinProject(models.Model):
    user = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.CASCADE)
    folder = models.ForeignKey(FolderinProject, verbose_name='所属文件夹', on_delete=models.CASCADE,
                               null=True, blank=True)
    project = models.ForeignKey(Project, verbose_name='所属项目', on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/projects/%Y%m%d/', verbose_name='文件', null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    file_name = models.CharField(max_length=50, verbose_name='文件名')
    file_size = models.PositiveIntegerField()  # 文件大小

    class Meta:
        verbose_name = '项目文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file_name
