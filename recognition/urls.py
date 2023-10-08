from django.urls import path

from recognition.views import CrackDetectionShow, GetBoxSAPIView, SaveDetectionAPI

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 裂缝检测 图片未上传
    path("api/crackdetection/", CrackDetectionShow.as_view(), name="crackdetection"),
    path("api/getbox/", GetBoxSAPIView.as_view(), name="getbox"),
    path("api/savedetection/", SaveDetectionAPI.as_view(), name="savedetection"),

]
