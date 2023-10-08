from django.urls import path

from users import views
from users.views import SmsCodeView

from users.views import ResetPasswordAPI, LoginPwdAPI, LoginSmsAPI, UserInfoAPI, EditUserInfoAPI, UserRegistrationAPI, \
    VerifySmsCodeAPI

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 短信验证码发送
    path('api/sms/', SmsCodeView.as_view()),

    # 手机号+验证码注册
    path('api/register/', UserRegistrationAPI.as_view()),

    # 用户手机号验证
    path('api/sms_verify/', VerifySmsCodeAPI.as_view()),

    # 密码设置
    path('api/reset-password/', ResetPasswordAPI.as_view()),

    # 登录
    path('login/password/', LoginPwdAPI.as_view()),  # 手机号+密码登录
    path('login/sms/', LoginSmsAPI.as_view()),  # 手机号+验证码登录

    # 获取用户信息
    path('api/user-info/', UserInfoAPI.as_view()),

    # 编辑用户信息
    path('api/edit-userinfo/', EditUserInfoAPI.as_view()),

]

