"""
Django settings for velican2 project.

Generated by 'django-admin startproject' using Django 4.1.7.
"""
import os
from pathlib import Path
from django.urls import reverse_lazy

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("VELICAN_SECRET", 'verysecret')

DEBUG = os.getenv("VELICAN_DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [os.getenv("VELICAN_HOST", "localhost"), ]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # put velican before other apps to have template resolution priority
    'velican2.core',
    'velican2.payment',
    'velican2.engines.pelican',
    'velican2.deployers.aws',
    'velican2.deployers.caddy',
    'velican2.exporters.git',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.instagram',
    'allauth.socialaccount.providers.twitter_oauth2',
    'allauth.socialaccount.providers.linkedin_oauth2',

    'martor',
    # 'markdownx',
    'django_extensions',
    'debug_toolbar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'velican2.core.context_processors.user_has_site',
            ],
        },
    },
]

WSGI_APPLICATION = 'velican2.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'runtime' / 'sqlite3.db',
    }
}

ROOT_URLCONF = 'velican2.urls'

MEDIA_ROOT = BASE_DIR / 'runtime' / 'media'
STATIC_ROOT = BASE_DIR / 'runtime' / 'static'

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    # 'social_core.backends.twitter.TwitterOAuth',
    'django.contrib.auth.backends.ModelBackend',
]

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = reverse_lazy('core:start')
LOGIN_REDIRECT_URL = reverse_lazy("core:sites")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = 'media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
]

# Choices are: "semantic", "bootstrap"
MARTOR_THEME = 'semantic'
MARTOR_UPLOAD_URL = ''  # will POST to the current view
MARTOR_ALTERNATIVE_CSS_FILE_THEME = "core/martor/css/martor.min.css"

from .local_settings import *