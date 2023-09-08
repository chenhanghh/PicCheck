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


# 发送验证码
class SmsCodeView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        if not re.match(r"^1[3-9]\d{9}$", phonenumber):
            return JsonResponse({'code': 400, 'msg': '手机号码格式不正确'})
        else:
            # 生成短信验证码，随机n位数字, 以下列表生成式可以随机生成4位0-9的数字字符串
            sms_code = '%04d' % random.randint(0, 9999)
            # 保存短信验证码
            redis_conn.setex('sms_%s' % phonenumber, 3000, sms_code)
            # 发送手机验证码
            ccp = CCP()
            try:
                # ccp.send_template_sms(手机号,[验证码，过期时间],内容模板)
                res = ccp.send_template_sms(phonenumber, [sms_code, 5], "1")
                if res == 0:
                    return JsonResponse({'code': 200, "msg": "短信验证码发送成功！"})
                else:
                    return JsonResponse({'code': 400, "msg": "短信验证码发送失败！"})
            except Exception as e:
                logger.error(e)
                return JsonResponse({'code': 400, "msg": "短信验证码发送异常！"})


# 手机号+验证码注册
class RegisterView(View):
    def post(self, request):
        # 获取手机号码和输入的验证码
        phonenumber = request.POST.get('phonenumber')
        re_captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        if User.objects.filter(phonenumber=phonenumber):
            return JsonResponse({'code': 400, 'msg': '手机号已注册'})
        if int(re_captcha) != int(redis_sms):
            return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
        else:
            try:
                # 随机生成一个用户名
                user_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
                record = User.objects.create_user(phonenumber=phonenumber,
                                                  username=user_name
                                                  )
                return JsonResponse({'code': 200, "msg": "注册成功！"})
            except DatabaseError as e:
                logger.error(e)
                return JsonResponse({'code': 400, "msg": "注册失败"})


# 用户手机号验证
class VerifySmsCode(View):
    def post(self, request):
        # 获取手机号码和输入的验证码
        phonenumber = request.POST.get('phonenumber')
        re_captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        try:
            user = User.objects.get(phonenumber=phonenumber)
            if int(re_captcha) != int(redis_sms):
                return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
            else:
                return JsonResponse({'code': 200, "msg": "验证成功"})
        except User.DoesNotExist:
            return JsonResponse({'code': 400, "msg": "用户不存在"})


# 密码设置（包括修改密码、忘记密码）
class ResetPasswordView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        password = request.POST.get('password')
        try:
            user = User.objects.get(phonenumber=phonenumber)
            user.set_password(password)
            user.save()
            return JsonResponse({'code': 200, 'msg': '密码设置成功'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, "msg": "密码设置异常，请稍后再试！"})


# 手机号+密码登录，用户名与密码匹配返回token
class LoginPasswordView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        password = request.POST.get('password')
        try:
            user = User.objects.get(phonenumber=phonenumber)
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
        except User.DoesNotExist:
            return JsonResponse({'code': 400, "msg": "用户不存在"})


# 手机号+验证码登录
class LoginSmsView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        re_captcha = request.POST.get('captcha')
        redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        try:
            user = User.objects.get(phonenumber=phonenumber)
            if int(re_captcha) != int(redis_sms):
                return JsonResponse({'code': 400, "msg": "验证码失效或输入错误"})
            else:
                # 调用第三方的JWT_PAYLOAD_HANDLER和JWT_ENCODE_HANDLER
                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

                # 通过user解析出payload
                payload = jwt_payload_handler(user)
                # 通过payload生成token
                token = jwt_encode_handler(payload)
                return JsonResponse({'code': 200, 'msg': '用户登陆成功！', 'token': token})
        except User.DoesNotExist:
            return JsonResponse({'code': 400, "msg": "用户不存在"})


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


# 编辑用户信息
class ModifyUserInfoView(View):
    def post(self, request):
        phonenumber = request.POST.get('phonenumber')
        nickname = request.POST.get('nickname')
        gender = request.POST.get('gender')
        scope = request.POST.get('scope')
        user = User.objects.filter(phonenumber=phonenumber).first()
        if not user:
            return JsonResponse({'code': 400, 'msg': '该用户未注册'})
        else:
            user.nickname = nickname
            user.gender = gender
            user.scope = scope
            user.save()
            return JsonResponse({'code': 200, 'msg': '用户信息修改成功'})
