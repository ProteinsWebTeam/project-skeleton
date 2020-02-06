"""
Django settings for interpro project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import yaml
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    INTERPRO_CONFIG = yaml.safe_load(open("{}/config/interpro.yml".format(BASE_DIR)))
except FileNotFoundError:
    INTERPRO_CONFIG = {}
try:
    MYSQL_CONFIG = yaml.safe_load(open("{}/config/mysql.yml".format(BASE_DIR)))
except FileNotFoundError:
    MYSQL_CONFIG = {}
try:
    INTERPRO_CONFIG_LOCAL = yaml.safe_load(
        open("{}/config/interpro.local.yml".format(BASE_DIR))
    )
except FileNotFoundError:
    INTERPRO_CONFIG_LOCAL = {}

for key in INTERPRO_CONFIG_LOCAL:
    INTERPRO_CONFIG[key] = INTERPRO_CONFIG_LOCAL.get(key, None)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "#*-7w_j1le-j(_#=g4ii!knr&w5!9ocpw*#7hq9+_osc5@19vs"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = INTERPRO_CONFIG.get("debug", False)

MINOR_VERSION = INTERPRO_CONFIG.get("minor_version", 0)
HTTP_PROXY = INTERPRO_CONFIG.get("http_proxy", "")

ALLOWED_HOSTS = INTERPRO_CONFIG.get("allowed_host", [])

import django_redis.cache
import django_redis.client

# Application definition

INSTALLED_APPS = (
    #'django.contrib.admin',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # added
    "webfront",
    "release",
    # third-party added libraries
    "rest_framework",
)

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    #'django.middleware.cache.UpdateCacheMiddleware',
    #'django.middleware.common.CommonMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
)

if INTERPRO_CONFIG.get("django_cors", False):
    INSTALLED_APPS = INSTALLED_APPS + ("corsheaders",)
    MIDDLEWARE = ("corsheaders.middleware.CorsMiddleware",) + MIDDLEWARE
    CORS_ORIGIN_ALLOW_ALL = True
    CORS_ALLOW_CREDENTIALS = False


ROOT_URLCONF = "interpro.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "interpro.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": MYSQL_CONFIG.get("engine", "django.db.backends.sqlite3"),
        "NAME": MYSQL_CONFIG.get(
            "sid", os.path.join(BASE_DIR, "../database/db.sqlite3")
        ),
        "USER": MYSQL_CONFIG.get("user"),
        "PASSWORD": MYSQL_CONFIG.get("password"),
        "HOST": MYSQL_CONFIG.get("host"),
        "PORT": MYSQL_CONFIG.get("port"),
        "CONN_MAX_AGE": MYSQL_CONFIG.get("conn_max_age", 0),
        "TEST": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(os.path.dirname(__file__), "test.db"),
        },
    }
}

TESTING = sys.argv[1:2] == ["test"] or INTERPRO_CONFIG.get("use_test_db", True)
if TESTING:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "../database/db.sqlite3",
    }


SEARCHER_URL = INTERPRO_CONFIG.get(
    "searcher_path", "http://127.0.0.1:9200/interpro_sp/relationship"
)
SEARCHER_TEST_URL = INTERPRO_CONFIG.get(
    "searcher_test_path", "http://127.0.0.1:9200/interpro_sp/relationship"
)
if INTERPRO_CONFIG.get("use_test_db", True):
    SEARCHER_URL = SEARCHER_TEST_URL
TEST_RUNNER = "webfront.tests.managed_model_test_runner.UnManagedModelTestRunner"

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = INTERPRO_CONFIG.get("static_url", "/static_files/")
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "static_files"))


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
    "DEFAULT_PAGINATION_CLASS": "webfront.pagination.CustomPagination",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "interpro.renderers.TSVRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

HMMER_PATH = INTERPRO_CONFIG.get("hmmer_path", "/tmp/")
TMP_FOLDER = INTERPRO_CONFIG.get("tmp_path", "/tmp/")
DB_MEMBERS = INTERPRO_CONFIG.get("members", {})
ENTRY_SETS = INTERPRO_CONFIG.get("sets", {})
CROSS_REFERENCES = INTERPRO_CONFIG.get("cross_references", {})

ENABLE_CACHING = INTERPRO_CONFIG.get("enable_caching", False)
if ENABLE_CACHING:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": INTERPRO_CONFIG.get("redis", "redis://127.0.0.1:6379/1"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }

import logging

l = logging.getLogger("django.db.backends")
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())
if DEBUG and ("TRAVIS" not in os.environ):
    LOGGING = {
        "version": 1,
        "handlers": {
            "console": {"level": "DEBUG", "class": "logging.StreamHandler"},
            "file_sql": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": "../sql.log",
            },
            "file_elastic": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": "../elastic.log",
            },
            "file_request": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": "../requests.log",
            },
        },
        "loggers": {
            "django.db.backends": {"level": "DEBUG", "handlers": ["file_sql"]},
            "interpro.elastic": {"level": "DEBUG", "handlers": ["file_elastic"]},
            "interpro.request": {"level": "DEBUG", "handlers": ["file_request"]},
        },
    }

# Debug toolbar
# DEBUG_TOOLBAR_PATCH_SETTINGS = False
# DEBUG_TOOLBAR_CONFIG = {
#     # show the toolbar for all requests (in DEBUG mode)
#     'SHOW_TOOLBAR_CALLBACK': lambda request: True,
# }
# DEBUG_TOOLBAR_PANELS = [
#     'debug_toolbar.panels.versions.VersionsPanel',
#     'debug_toolbar.panels.timer.TimerPanel',
#     'debug_toolbar.panels.settings.SettingsPanel',
#     'debug_toolbar.panels.headers.HeadersPanel',
#     'debug_toolbar.panels.request.RequestPanel',
#     'debug_toolbar.panels.sql.SQLPanel',
#     'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#     'debug_toolbar.panels.templates.TemplatesPanel',
#     'debug_toolbar.panels.cache.CachePanel',
#     'debug_toolbar.panels.signals.SignalsPanel',
#     'debug_toolbar.panels.logging.LoggingPanel',
#     'debug_toolbar.panels.redirects.RedirectsPanel',
#     'debug_toolbar.panels.profiling.ProfilingPanel',
# ]
