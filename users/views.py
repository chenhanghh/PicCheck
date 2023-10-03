import random
import string

from django.contrib.auth import authenticate
from django.db import DatabaseError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from common.models import User
import re
from django.contrib.auth.hashers import check_password

from .serializers import ResetPasswordSerializer, LoginSmsSerializer, UserSerializer, UserEditSerializer, \
    LoginPwdSerializer
from utils.yuntongxun.sms import CCP
import logging

from django_redis import get_redis_connection

from rest_framework_jwt.settings import api_settings
from jwt import ExpiredSignatureError

# 注册视图
from django.views import View

logger = logging.getLogger(__name__)

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
        # redis_sms = redis_conn.get("sms_%s" % phonenumber)  # 从redis中获取数据
        redis_sms = 1782
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


# 密码设置
class ResetPasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data.get('new_password')
            user.set_password(new_password)
            user.save()
            return Response({'message': '密码修改成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 手机号+密码登录
class LoginPwdAPI(APIView):
    def post(self, request):
        serializer = LoginPwdSerializer(data=request.data)
        if serializer.is_valid():
            phonenumber = serializer.validated_data["phonenumber"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(phonenumber=phonenumber)
                if user.is_active == 0:
                    return Response({'error': 'This user is not active.'}, status=status.HTTP_400_BAD_REQUEST)
                if not check_password(password, user.password):
                    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({'access_token': access_token}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 手机号+验证码登录
class LoginSmsAPI(APIView):
    def post(self, request):
        serializer = LoginSmsSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_code = serializer.validated_data['verification_code']

            # 从Redis中获取验证码
            # cached_code = redis_conn.get("sms_%s" % phone_number)
            cached_code = 1782

            if int(cached_code) and int(cached_code) == int(verification_code):
                try:
                    user = User.objects.get(phonenumber=phone_number)
                except User.DoesNotExist:
                    return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({'access_token': access_token}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 获取用户信息
class UserInfoAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


# 编辑用户信息
class EditUserInfoAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user_profile = request.user

        serializer = UserEditSerializer(user_profile, data=request.data, partial=True)  # 允许部分更新

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
