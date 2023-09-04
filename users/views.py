import random
import string

from django.db import DatabaseError
from django.http import JsonResponse
from common.models import User
import re
from django.contrib.auth.hashers import check_password

from utils.yuntongxun.sms import CCP
import logging

from django_redis import get_redis_connection

from rest_framework_jwt.settings import api_settings
from jwt import ExpiredSignatureError

# 注册视图
from django.views import View

logger = logging.getLogger('django')

# 链接redis数据库
redis_conn = get_redis_connection("default")

# redis_sms = redis_conn.get("sms_%s" % mobile)   #从redis中获取数据，或者删除数据等操作


# 用户名+密码注册 1.
class RegisterUsnameView(View):
    def post(self, request):
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 验证
        try:
            if User.objects.filter(username=username):
                return JsonResponse({'code': 400, 'msg': '用户已存在'})
            else:
                user = User.objects.create_user(username=username,
                                                password=password  # 密码进行加密处理
                                                )
                return JsonResponse({'code': 200, "msg": "注册成功！"})
        except DatabaseError as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '注册失败'})


# 手机号验证码发送
def captcha(phone_number):
    # 生成短信验证码，随机n位数字, 以下列表生成式可以随机生成4位0-9的数字字符串
    sms_code = '%04d' % random.randint(0, 9999)
    logger.info(sms_code)
    # 保存短信验证码
    redis_conn.setex('sms_%s' % phone_number, 3000, sms_code)
    # 发送手机验证码
    ccp = CCP()
    # ccp.send_template_sms(手机号,[验证码，过期时间],内容模板)
    res = ccp.send_template_sms(phone_number, [sms_code, 5], "1")
    return res


# 用户注册，发送验证码 2.
# 手机号注册，发送验证码 1.
class RegisterCaptchaView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        if not re.match(r"^1[3-9]\d{9}$", phonenumber):
            return JsonResponse({'code': 400, 'msg': '手机号码格式不正确'})
        elif User.objects.filter(phonenumber=phonenumber):
            return JsonResponse({'code': 400, 'msg': '手机号已注册'})
        else:
            res = captcha(phonenumber)
            if res == 0:
                return JsonResponse({'code': 200, "msg": "短信验证码发送成功！"})
            else:
                return JsonResponse({'code': 400, "msg": "短信验证码发送失败！"})


# 用户注册，绑定手机号 3.
class RegisterBindMobileView(View):
    def post(self, request):
        # 获取手机号码和输入的验证码
        username = request.POST.get('username')
        phone_number = request.POST.get('phonenumber')
        re_captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phone_number)  # 从redis中获取数据
        if int(re_captcha) != int(redis_sms):
            return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
        else:
            user = User.objects.get(username=username)
            user.phonenumber = phone_number
            user.save()
            return JsonResponse({'code': 200, "msg": "手机号绑定成功！"})


# 手机号 + 验证码注册 2.
class RegisterMobileView(View):
    def post(self, request):
        # 获取手机号码和输入的验证码
        phonenumber = request.POST.get('phonenumber')
        re_captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        if int(re_captcha) != int(redis_sms):
            return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
        else:
            # 随机生成一个账号
            user_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
            record = User.objects.create_user(phonenumber=phonenumber,
                                              username=user_name
                                              )
            return JsonResponse({'code': 200, "msg": "注册成功！", 'id': record.id})


# 手机+验证码注册 3.密码设置
class RegisterMobilePwdView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        password = request.POST.get('password')
        user = User.objects.get(phonenumber=phonenumber)
        user.set_password(password)
        user.save()
        return JsonResponse({'code': 200, 'msg': '密码添加成功'})


# 用户名+密码登录，用户名与密码匹配返回token
class LoginUsernameView(View):
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': '该用户未注册'})
        if user.is_active == 0:
            return JsonResponse({'code': 400, 'msg': '用户被禁用'})
        if not check_password(password, user.password):
            return JsonResponse({'code': 400, 'msg': '用户名或密码错误'})

        # 调用第三方的JWT_PAYLOAD_HANDLER和JWT_ENCODE_HANDLER
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 通过user解析出payload
        payload = jwt_payload_handler(user)
        # 通过payload生成token
        token = jwt_encode_handler(payload)
        return JsonResponse({'code': 200, 'msg': '用户登陆成功！', 'token': token})


# 手机号+验证码登录 1.验证码发送
class LoginCaptchaView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        if not re.match(r"^1[3-9]\d{9}$", phonenumber):
            return JsonResponse({'code': 400, 'msg': '手机号码格式不正确'})
        elif User.objects.filter(phonenumber=phonenumber):
            res = captcha(phonenumber)
            if res == 0:
                return JsonResponse({'code': 200, "msg": "短信验证码发送成功！"})
            else:
                return JsonResponse({'code': 400, "msg": "短信验证码发送失败！"})
        else:
            return JsonResponse({'code': 400, 'msg': '手机号不存在'})


# 手机号+验证码登录 2.验证验证码
class LoginMobileCaptView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        if int(captcha) != int(redis_sms):
            return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
        else:
            user = User.objects.get(phonenumber=phonenumber)

            # 调用第三方的JWT_PAYLOAD_HANDLER和JWT_ENCODE_HANDLER
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 通过user解析出payload
            payload = jwt_payload_handler(user)
            # 通过payload生成token
            token = jwt_encode_handler(payload)
            return JsonResponse({'code': 200, 'msg': '用户登陆成功！', 'token': token})


# 获取用户信息
class UserInfoView(View):
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION')
        except Exception:
            return JsonResponse({'code': 400, 'msg': '参数错误'})

        # 解析token
        jwt_decode_handler = api_settings.JWT_DECODE_HANDLER

        if token:
            try:
                username = jwt_decode_handler(token)["username"]
                nickname = User.objects.filter(username=username).values('nickname').first()
                phonenumber = User.objects.filter(username=username).values('phonenumber').first()
                gender = User.objects.filter(username=username).values('gender').first()
                position = User.objects.filter(username=username).values('position').first()
                project = User.objects.filter(username=username).values('project').first()
                scope = User.objects.filter(username=username).values('scope').first()
                return JsonResponse({'code': 200, 'msg': '用户信息获取成功！', 'username': username, 'nickname': nickname['nickname'],
                                     'phonenumber': phonenumber['phonenumber'], 'gender': gender['gender'],
                                     'position': position['position'], 'project': project['project'],
                                     'scope': scope['scope']})
            except ExpiredSignatureError:
                return JsonResponse({'code': 400, 'msg': 'token已过期'})
        else:
            return JsonResponse({'code': 400, 'msg': '无访问权限，请重新登录或稍后再试！'})


# 修改密码
class ResetPasswordView(View):
    def post(self, request):
        username = request.POST.get('username')
        oldpwd = request.POST.get('oldpwd')
        newpwd = request.POST.get('newpwd')
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': '该用户未注册'})
        if user.is_active == 0:
            return JsonResponse({'code': 400, 'msg': '用户被禁用'})
        if not check_password(oldpwd, user.password):
            return JsonResponse({'code': 400, 'msg': '用户名或密码错误'})
        else:
            user.set_password(newpwd)
            user.save()
            return JsonResponse({'code': 200, 'msg': '密码修改成功'})


# 忘记密码 1.输入手机号发送短信验证码 验证LoginCaptchaView()
# 手机号 + 验证码进行验证 2.验证
class UpdatePwdCaptchaView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        if int(captcha) != int(redis_sms):
            return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
        else:
            return JsonResponse({'code': 200, 'msg': '验证成功！'})


# 忘记密码 2.修改密码
class UpdatePwdView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        newpwd = request.POST.get('newpwd')
        user = User.objects.filter(phonenumber=phonenumber).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': '该用户未注册'})
        if user.is_active == 0:
            return JsonResponse({'code': 400, 'msg': '用户被禁用'})
        else:
            user.set_password(newpwd)
            user.save()
            return JsonResponse({'code': 200, 'msg': '密码修改成功'})


# 编辑用户信息
class ModifyUserInfoView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        username = request.POST.get('username')
        nickname = request.POST.get('nickname')
        gender = request.POST.get('gender')
        scope = request.POST.get('scope')
        user = User.objects.filter(phonenumber=phonenumber).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': '该用户未注册'})
        else:
            user.username = username
            user.nickname = nickname
            user.gender = gender
            user.scope = scope
            user.save()
            return JsonResponse({'code': 200, 'msg': '用户信息修改成功'})
