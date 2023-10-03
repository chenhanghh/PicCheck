from django.urls import path

from camera.views import ImageUploadAPI

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 上传图片
    path('api/upload/', ImageUploadAPI.as_view()),


]

