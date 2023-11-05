from django.urls import path

from .views import AddGroupAPI

# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 创建群组
    path('api/addgroup/', AddGroupAPI.as_view()),

]

