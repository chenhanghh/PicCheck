import random
import string

from rest_framework import serializers
from common.models import User


# 注册
class UserRegisterSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    captcha = serializers.CharField()

    def validate(self, data):
        phonenumber = data.get('phonenumber')
        captcha = data.get('captcha')

        # 验证码验证逻辑  (之后开通短信服务再进行更改)
        redis_sms = 1782

        # 检查验证码是否有效，如果无效，引发ValidationError
        if int(captcha) != int(redis_sms):
            raise serializers.ValidationError("验证码无效")

        return data

    # 创建用户
    def create(self, validated_data):
        phonenumber = validated_data['phonenumber']
        # 随机生成一个用户名
        username = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        user = User.objects.create_user(phonenumber=phonenumber, username=username)
        return user


# 用户手机号验证
class VerifySmsCodeSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    captcha = serializers.CharField()

    def validate(self, data):
        phonenumber = data.get('phonenumber')
        captcha = data.get('captcha')

        # 验证码验证逻辑  (之后开通短信服务再进行更改)
        redis_sms = 1782

        # 检查验证码是否有效，如果无效，引发ValidationError
        if int(captcha) != int(redis_sms):
            raise serializers.ValidationError("验证码无效")

        return data


# 密码设置
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)


# 手机号+密码登录
class LoginPwdSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    password = serializers.CharField()


# 手机号+验证码登录
class LoginSmsSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    captcha = serializers.CharField()


# 获取用户信息
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'phonenumber', 'gender', 'position', 'scope', 'avatar')


# 编辑用户信息
class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'gender', 'position', 'scope']
