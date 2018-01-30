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
    INTERPRO_CONFIG = yaml.safe_load(open('{}/config/interpro.yml'.format(BASE_DIR)))
except FileNotFoundError:
    INTERPRO_CONFIG = {}
try:
    ORACLE_CONFIG = yaml.safe_load(open('{}/config/oracle.yml'.format(BASE_DIR)))
except FileNotFoundError:
    ORACLE_CONFIG = None
try:
    MYSQL_CONFIG = yaml.safe_load(open('{}/config/mysql.yml'.format(BASE_DIR)))
except FileNotFoundError:
    MYSQL_CONFIG = {}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#*-7w_j1le-j(_#=g4ii!knr&w5!9ocpw*#7hq9+_osc5@19vs'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    #'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # added
    'webfront',
    'release',
    # third-party added libraries
    'rest_framework'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

if (INTERPRO_CONFIG.get('django_cors', False)):
    INSTALLED_APPS = (*INSTALLED_APPS, 'corsheaders')
    MIDDLEWARE_CLASSES = (
        'corsheaders.middleware.CorsMiddleware',
        *MIDDLEWARE_CLASSES
    )
    CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'interpro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'interpro.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': MYSQL_CONFIG.get('engine', 'django.db.backends.sqlite3'),
        'NAME': MYSQL_CONFIG.get(
            'sid',
            os.path.join(BASE_DIR, '../database/db.sqlite3')
        ),
        'USER': MYSQL_CONFIG.get('user'),
        'PASSWORD': MYSQL_CONFIG.get('password'),
        'HOST': MYSQL_CONFIG.get('host'),
        'PORT': MYSQL_CONFIG.get('port'),
        'TEST': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(__file__), 'test.db'),
        },
    },
}
if sys.argv[1:2] == ['test'] or INTERPRO_CONFIG.get('use_test_db', True):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '../database/db.sqlite3',
    }
if ORACLE_CONFIG is not None:
    DATABASES['interpro_ro'] = {
        # 'ENGINE': ORACLE_CONFIG.get('engine', 'django.db.backends.oracle'),
        'USER': ORACLE_CONFIG.get('user', 'USER'),
        'PASSWORD': ORACLE_CONFIG.get('password'),
    }
    if ORACLE_CONFIG.get('sid', None) is not None:
        DATABASES['interpro_ro']['NAME'] = ORACLE_CONFIG.get('sid')
        DATABASES['interpro_ro']['HOST'] = ORACLE_CONFIG.get('host', 'localhost')
        DATABASES['interpro_ro']['PORT'] = ORACLE_CONFIG.get('port', 1540)
    elif ORACLE_CONFIG.get('name', None) is not None:
        DATABASES['interpro_ro']['NAME'] = "{}:{}/{}".format(
            ORACLE_CONFIG.get('host', 'localhost'),
            ORACLE_CONFIG.get('port', 1540),
            ORACLE_CONFIG.get('name')
        )
    else:
        del DATABASES['interpro_ro']


SEARCHER_URL = INTERPRO_CONFIG.get('searcher_path', 'http://127.0.0.1:9200/interpro_sp/relationship')
SEARCHER_TEST_URL = INTERPRO_CONFIG.get('searcher_test_path', 'http://127.0.0.1:9200/interpro_sp/relationship')
if INTERPRO_CONFIG.get('use_test_db', True):
    SEARCHER_URL = SEARCHER_TEST_URL
TEST_RUNNER = 'webfront.tests.managed_model_test_runner.UnManagedModelTestRunner'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/interpro/static_files/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'static_files'))


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'webfront.pagination.CustomPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'interpro.renderers.TSVRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

HMMER_PATH = INTERPRO_CONFIG.get('hmmer_path', '/tmp/')
TMP_FOLDER = INTERPRO_CONFIG.get('tmp_path', '/tmp/')
DB_MEMBERS = INTERPRO_CONFIG.get('members', {})
ENTRY_SETS = INTERPRO_CONFIG.get('sets', {})
CROSS_REFERENCES = INTERPRO_CONFIG.get('cross_references', {})

import logging
l = logging.getLogger('django.db.backends')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())
if DEBUG and ("TRAVIS" not in os.environ):
    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        # 'loggers': {
        #     'django.db.backends': {
        #         'level': 'DEBUG',
        #         'handlers': ['console'],
        #     },
        # },
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
