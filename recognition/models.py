from django.utils import timezone
from django.db import models
from common.models import User

# Create your models here.


class CrackDetection(models.Model):
    image = models.FileField(upload_to='uploads/users/%Y%m%d/', verbose_name='原图', null=True, blank=True)

    img_new = models.FileField(upload_to='uploads/users/%Y%m%d/', verbose_name='新图')
    img_new_name = models.CharField(max_length=50, verbose_name='新图片名')
    img_new_size = models.PositiveIntegerField()  # 新图片大小

    user = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.CASCADE)
    box_s = models.JSONField(verbose_name="目标检测结果", null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    notes = models.CharField(max_length=2000, verbose_name='标注', null=True, blank=True)

    class Meta:
        verbose_name = "缺陷检测"
        verbose_name_plural = verbose_name


class FileinUser(models.Model):
    file = models.FileField(upload_to='uploads/users/%Y%m%d/', verbose_name='个人文件')
    file_name = models.CharField(max_length=50, verbose_name='文件名称')
    create_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
