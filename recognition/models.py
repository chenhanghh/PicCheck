from django.db import models
from common.models import User, FileinUser

# Create your models here.


class CrackDetection(models.Model):
    photo = models.ForeignKey(FileinUser, verbose_name='照片', null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.CASCADE)
    box_s = models.JSONField(verbose_name="目标检测结果", null=True, blank=True)

    class Meta:
        verbose_name = "缺陷检测"
        verbose_name_plural = verbose_name
