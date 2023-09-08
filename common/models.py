from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
# 定义数据库表 项目所需要的公共表


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
    # 所属项目
    project = models.CharField(max_length=256)

    # 创建超级管理员必须输入的字段
    REQUIRED_FIELDS = ['phonenumber']
