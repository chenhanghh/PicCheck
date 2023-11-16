from django.urls import path

from recognition.views import CrackDetectionShow, GetBoxSAPIView, SaveGalleryAPI, GeneratePDFAPI

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 裂缝检测 图片未上传
    path("api/crackdetection/", CrackDetectionShow.as_view()),
    path("api/getbox/", GetBoxSAPIView.as_view()),

    # 保存检测图片至图库
    path("api/save-gallery/", SaveGalleryAPI.as_view()),

    # 上传检测pdf文件至个人文件
    path("api/upload-user/", GeneratePDFAPI.as_view()),

]
