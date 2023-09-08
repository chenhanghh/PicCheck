from django.urls import path

from users import views
from users.views import SmsCodeView, LoginPasswordView, \
    RegisterView, UserInfoView, ResetPasswordView, \
    ModifyUserInfoView, VerifySmsCode, LoginSmsView

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 短信验证码发送
    path('api/sms/', SmsCodeView.as_view()),

    # 手机号+验证码注册
    path('api/register/', RegisterView.as_view()),

    # 用户手机号验证
    path('api/smsverify/', VerifySmsCode.as_view()),

    # 密码设置
    path('api/resetpassword/', ResetPasswordView.as_view()),

    # 登录
    path('api/login/pasword/', LoginPasswordView.as_view()),  # 手机号+密码登录
    path('api/login/sms/', LoginSmsView.as_view()),  # 手机号+验证码登录

    # 获取用户信息
    path('api/userinfo/', UserInfoView.as_view()),

    # 编辑用户信息
    path('api/userinfo/edit/', ModifyUserInfoView.as_view()),

]

