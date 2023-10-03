from rest_framework import serializers
from common.models import User


# 密码设置
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)


# 手机号+密码登录
class LoginPwdSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    password = serializers.CharField()


# 手机号+验证码登录
class LoginSmsSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    verification_code = serializers.CharField()


# 获取用户信息
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'phonenumber', 'gender', 'position', 'scope')


# 编辑用户信息
class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'gender', 'position', 'scope']
