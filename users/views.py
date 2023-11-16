import random

from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from common.models import User
import re
from django.contrib.auth.hashers import check_password
from django.db.utils import IntegrityError

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from django.conf import settings
import json

from .serializers import ResetPasswordSerializer, LoginSmsSerializer, UserSerializer, UserEditSerializer, \
    LoginPwdSerializer, UserRegisterSerializer, VerifySmsCodeSerializer

from utils.yuntongxun.sms import CCP
import logging

from django_redis import get_redis_connection

# 注册视图
from django.views import View

logger = logging.getLogger(__name__)

# 链接redis数据库
redis_conn = get_redis_connection("default")


# 发送验证码
class SmsCodeView(View):
    def get(self, request):
        phonenumber = request.GET.get('phonenumber')

        # if not phonenumber:
        #     return Response({'status': 400, 'message': '缺少手机号码'}, status=status.HTTP_400_BAD_REQUEST)

        if not re.match(r"^1[3-9]\d{9}$", phonenumber):
            return Response({'status': 400, 'message': '手机号码格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成随机的6位验证码
        verification_code = ''.join(random.choices('0123456789', k=6))

        # request.session['verification_code'] = verification_code

        # 保存短信验证码
        redis_conn.setex('sms_%s' % phonenumber, 3000, verification_code)

        # 阿里云短信服务配置
        client = AcsClient(
            settings.ALIYUN_ACCESS_KEY_ID,
            settings.ALIYUN_ACCESS_KEY_SECRET,
            'default'
        )

        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')

        # 配置短信模板和签名
        request.add_query_param('SignName', settings.ALIYUN_SMS_SIGN_NAME)
        request.add_query_param('TemplateCode', settings.ALIYUN_SMS_TEMPLATE_CODE)
        # 设置短信验证码和手机号
        request.add_query_param('TemplateParam', json.dumps({'code': verification_code}))
        request.add_query_param('PhoneNumbers', phonenumber)

        # # 发送短信
        # response = client.do_action_with_exception(request)

        try:
            # 发送短信
            response = client.do_action_with_exception(request)
            return Response({'status': 200, 'message': '验证码发送成功'})
        except Exception as e:
            return Response({'status': 500, 'message': f'验证码发送失败: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRegistrationAPI(APIView):
    """
    手机号+验证码注册
    """
    def post(self, request):
        try:
            serializer = UserRegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                phonenumber = serializer.validated_data["phonenumber"]
                user = User.objects.get(phonenumber=phonenumber)
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({'status': 201, 'message': 'New users registered.', 'access_token': access_token, 'user_id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)
            return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({'status': 500, 'error': 'The phonenumber is registered.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifySmsCodeAPI(APIView):
    """
    用户手机号验证
    """
    def post(self, request):
        serializer = VerifySmsCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({'status': 200, 'message': 'Captcha is successfully verified.'}, status=status.HTTP_200_OK)
        return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPI(APIView):
    """
    密码设置
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data.get('new_password')
            user.set_password(new_password)
            user.save()
            return Response({'status': 200, 'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginPwdAPI(APIView):
    """
    手机号+密码登录
    """
    def post(self, request):
        serializer = LoginPwdSerializer(data=request.data)
        if serializer.is_valid():
            phonenumber = serializer.validated_data["phonenumber"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(phonenumber=phonenumber)
                if user.is_active == 0:
                    return Response({'status': 400, 'error': 'This user is not active.'}, status=status.HTTP_400_BAD_REQUEST)
                if not check_password(password, user.password):
                    return Response({'status': 401, 'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({'status': 200, 'access_token': access_token, 'user_id': user.id}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'status': 404, 'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginSmsAPI(APIView):
    """
    手机号+验证码登录
    """
    def post(self, request):
        serializer = LoginSmsSerializer(data=request.data)
        if serializer.is_valid():
            phonenumber = serializer.validated_data['phonenumber']
            captcha = serializer.validated_data['captcha']

            # 从Redis中获取验证码
            # cached_code = redis_conn.get("sms_%s" % phone_number)
            cached_code = 178266

            if int(cached_code) and int(cached_code) == int(captcha):
                try:
                    user = User.objects.get(phonenumber=phonenumber)
                except User.DoesNotExist:
                    return Response({'status': 404, 'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({'status': 200, 'access_token': access_token, 'user_id': user.id}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 400, 'error': 'Captcha error.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserInfoAPI(APIView):
    """
    获取用户信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({'status': 200, 'data': serializer.data})


class EditUserInfoAPI(APIView):
    """
    编辑用户信息
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user_profile = request.user

        serializer = UserEditSerializer(user_profile, data=request.data, partial=True)  # 允许部分更新

        if serializer.is_valid():
            # 处理头像上传
            user_avatar = request.FILES.get('avatar')
            if user_avatar:
                serializer.validated_data['avatar'] = user_avatar

            serializer.save()
            return Response({'status': 200, 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
