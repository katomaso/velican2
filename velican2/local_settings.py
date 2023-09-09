import os
from pathlib import Path

DEBUG = os.getenv("VELICAN_DEBUG", "True").lower() in ("1", "true", "yes")

ROOT_DIR = Path(__file__).resolve().parent.parent

HTML_SOURCE = Path(os.getenv("HTML_SOURCE", ROOT_DIR / "runtime/source"))
HTML_OUTPUT = Path(os.getenv("HTML_OUTPUT", ROOT_DIR / "runtime/www"))
APP_DIR = Path(os.getenv("APP_DIR", os.getcwd()))

PELICAN_DEFAULT_SETTINGS = {
    'PAGE_PATHS': ["pages", ],
    'ARTICLE_PATHS': ["content", ],
    'STATIC_PATHS': ['images', ],
    'STATIC_CREATE_LINKS': True,  #  create (sym)links to static files instead of copying them
    'STATIC_CHECK_IF_MODIFIED': True,
    'DELETE_OUTPUT_DIRECTORY': False,
    'CACHE_CONTENT': True, # cache generated files
    'LOAD_CONTENT_CACHE': True,
}

# django-allauth specific settings
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'js_sdk',
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': os.getenv('FACEBOOK_CLIENT_ID', "928951921500929"),
            'secret': os.getenv('FACEBOOK_CLIENT_SECRET', "87710ede48d8c5a75388034fb0834f79"),
        }
    },
    'twitter_oauth2': {
        'APP': {
            # app_id: 27563999
            'client_id': os.getenv('TWITTER_CLIENT_ID', "YkM3bTZ0WVNGOHdWdno2SDFZQV86MTpjaQ"),
            'secret': os.getenv('TWITTER_CLIENT_SECRET', "OpOw6i3W89q9oVfz9V0qLDWkUkPdt2hxmiIwghWNP3D7zv66nn"),
        },
        'SCOPE': ('tweet.write', 'tweet.read', 'users.read')
    }
}

SOCIAL_AUTH_TWITTER_OAUTH2_KEY = 'YkM3bTZ0WVNGOHdWdno2SDFZQV86MTpjaQ'
SOCIAL_AUTH_TWITTER_OAUTH2_SECRET = 'OpOw6i3W89q9oVfz9V0qLDWkUkPdt2hxmiIwghWNP3D7zv66nn'

# set to None or an empty string to disable caddy deployment
CADDY_URL = os.getenv("CADDY_URL", "http://localhost:2019")

AWS_KEY=os.getenv("AWS_KEY", "")
AWS_SECRET=os.getenv("AWS_SECRET", "")

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'cs-cz'
TIME_ZONE = 'Europe/Prague'
USE_I18N = True
USE_TZ = True
SITE_ID = 1
DOMAIN = "localhost"

MB = 1024*1024
MAX_IMAGE_UPLOAD_SIZE = 2.5*MB
MAX_IMAGE_SIZE = (1280, 720)
MAX_IMAGE_SIZE_MOBILE = (340, 720)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    '': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': False,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'velican2': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'pelican': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = []

EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
# EMAIL_HOST_USER
# EMAIL_HOST_PASSWORD

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TEMPLATE_CONTEXT': True,
}