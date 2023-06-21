import os
from pathlib import Path

DEBUG = os.getenv("VELICAN_DEBUG", "False").lower() in ("1", "true", "yes")

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
            'client_id': os.getenv('FACEBOOK_APP_ID', ""),
            'secret': os.getenv('FACEBOOK_APP_SECRET', ""),
        }
    }
}

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