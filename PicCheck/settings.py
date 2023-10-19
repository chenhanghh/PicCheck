"""
Django settings for PicCheck project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

import datetime

from PicCheck import postgresql_cfg

import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-zh9__!nm0s$wjflpr&w-di6i!wq4sdze#s5=)37_*m$wka2$*9"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*', ]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 跨域资源共享
    'corsheaders',

    # jwt
    'rest_framework',
    'rest_framework_jwt',  # 提供JWT身份验证功能

    "common.apps.CommonConfig",
    "users.apps.UsersConfig",
    "projects.apps.ProjectsConfig",
    "recognition.apps.RecognitionConfig",

]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_ALLOW_REFRESH': True,  # 允许刷新令牌
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),  # 刷新令牌的过期时间
}

# 设置JWT令牌的有效期，以秒为单位，默认为15分钟
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),  # 滑动令牌的刷新有效期
    'SLIDING_TOKEN_LIFETIME': datetime.timedelta(days=30),  # 滑动令牌的有效期
    'SLIDING_TOKEN_REFRESH_ON_LOGIN': True,  # 用户登录时是否刷新滑动令牌
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "PicCheck.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },

]

WSGI_APPLICATION = "PicCheck.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # 数据库引擎
        "NAME": postgresql_cfg.get_config("NAME"),  # 数据库名字
        "USER": postgresql_cfg.get_config("USER"),  # 数据库用户名
        "PASSWORD": postgresql_cfg.get_config("PASSWORD"),  # 数据库用户密码
        "HOST": postgresql_cfg.get_config("HOST"),  # 数据库主机
        "PORT": postgresql_cfg.get_config("PORT"),  # 数据库端口
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # redis缓存引擎
        'LOCATION': 'redis://127.0.0.1:6379/2',  # 指定redis所在的地址, 默认端口6379, 0代表数据库的索引
        'OPTIONS': {  # 指定需要使用redis的client类
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# 引用Django自带的User表，继承使用时需要设置
# 替换 系统的User 来使用自定义的User
AUTH_USER_MODEL = "common.User"

# 上传文件目录
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
# 设置文件访问的统一路由
MEDIA_URL = '/upload/'

# 配置日志
LOGGING_DIR = os.path.join(BASE_DIR, 'logs')  # 创建一个存储日志文件的目录
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {  # 格式化器
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {  # 记录不同级别日志的处理程序
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'error.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['file_debug', 'file_error', 'console'],
        'level': 'INFO',
    },
}

# 定义裂缝识别算法路径
ALGORITHM_URL = "https://wx.conre.com.cn/dev/yolov5-crack/predict"

CORS_ORIGIN_ALLOW_ALL = True  # 允许任何主机
CORS_ALLOW_CREDENTIALS = True  # 允许包含身份验证凭证的请求
