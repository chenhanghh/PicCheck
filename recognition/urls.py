from django.urls import path

from recognition.tasks import crack_detection
from recognition.views import CrackDetectionAPI, CrackDetectionRestfulAPI, CrackDetectionShow

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 裂缝检测
    path("api/crack_detection/", CrackDetectionAPI.as_view(), name="crack_detection"),
    path("crack_detection/<int:photo>/", CrackDetectionRestfulAPI.as_view({"get": "retrieve"}), name="crack_detection"),
    path("crack_show/<int:row_id>/", CrackDetectionShow.as_view(), name="crack_show"),

]
