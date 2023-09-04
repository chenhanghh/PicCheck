from django.urls import path

from users import views
from users.views import RegisterUsnameView, RegisterCaptchaView, RegisterBindMobileView, LoginUsernameView, \
    RegisterMobileView, RegisterMobilePwdView, UserInfoView, LoginCaptchaView, LoginMobileCaptView, ResetPasswordView, \
    UpdatePwdCaptchaView, UpdatePwdView, ModifyUserInfoView

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 手机号+密码注册
    path('api/register/username/', RegisterUsnameView.as_view()),
    path('api/register/captcha/', RegisterCaptchaView.as_view()),
    path('api/register/username/bind_mobile/', RegisterBindMobileView.as_view()),

    # 手机号+验证码注册
    path('api/register/mobile/', RegisterMobileView.as_view()),
    path('api/register/mobile/set_password/', RegisterMobilePwdView.as_view()),

    # 登录
    path('api/login/username/', LoginUsernameView.as_view()),
    path('api/login/mobile/send_captcha/', LoginCaptchaView.as_view()),
    path('api/login/mobile/captcha/', LoginMobileCaptView.as_view()),

    # 获取用户信息
    path('api/userinfo/', UserInfoView.as_view()),

    # 修改密码
    path('api/resetpassword/', ResetPasswordView.as_view()),

    # 忘记密码
    path('api/updatepassword/captcha/', UpdatePwdCaptchaView.as_view()),
    path('api/updatepassword/', UpdatePwdView.as_view()),

    # 编辑用户信息
    path('api/userinfo/edit/', ModifyUserInfoView.as_view()),

]

