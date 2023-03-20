from .settings_common import *
# 本番環境用設定ファイル

# 動作許可ホスト(セキュリティ用設定)
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'ywebserv1',
]

# Database設定
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'isk_tools_base',
        'USER': 'isk_tools_user',
        'PASSWORD': 'iskisk6117',
        # 'HOST': 'localhost\SQLEXPRESS',
        'HOST': 'ysqlserv4',  # 本番DB
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 13 for SQL Server',
        },
        'ATOMIC_REQUESTS': True
    },
    'fmsdb': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'fms',
        'USER': 'isk_tools_user',
        'PASSWORD': 'iskisk6117',
        # 'HOST': 'localhost\SQLEXPRESS',
        'HOST': 'ysqlserv4',  # 本番DB
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 13 for SQL Server',
        },
        'ATOMIC_REQUESTS': True
    },
    'GCdb': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'GC',
        'USER': 'GC_user_R',
        'PASSWORD': 'GC_user_R',
        # 'HOST': 'localhost\SQLEXPRESS',
        'HOST': 'Sqlserv2\\pubins',  # 本番DB
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 13 for SQL Server',
        },
        'ATOMIC_REQUESTS': True
    },
    'plantiav05': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'PLANTIA_PROD_DB',
        'USER': 'fujitsu',
        'PASSWORD': 'fujitsu00',
        # 'HOST': 'localhost\SQLEXPRESS',
        'HOST': 'YPLANTIAV05',  # 本番DB
        'PORT': '5432',
    },
    # 'plantiadb': {
    #     'ENGINE': 'django.db.backends.oracle',
    #     'NAME': 'PLANTIAU',
    #     'USER': 'PLANTIA44',
    #     'PASSWORD': 'PLANTIA44',
    #     'HOST': 'YPLANTIA',  # 本番DB
    #     'PORT': '1521',
    # },
    # 'cpexceldb': {
    #     'ENGINE': 'sql_server.pyodbc',
    #     'NAME': 'c_p_excel',
    #     'USER': 'isk_tools_user',
    #     'PASSWORD': 'iskisk6117',
    #     # 'HOST': 'localhost\SQLEXPRESS',
    #     # 'HOST': 'y0033out',
    #     'HOST': '172.16.48.23',
    #     'PORT': '',
    #     'OPTIONS': {
    #         'driver': 'ODBC Driver 13 for SQL Server',
    #     },
    #     'ATOMIC_REQUESTS': True
    # },
}

# ログ保存用設定
# LOG_ROOT = r'//Ydomnserv/common/部門間フォルダ/FacilityData/Production'
LOG_ROOT = 'D:\\python_tool_development/isk-tools'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_ROOT + "/logs/django_info.log",
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 1,
            "backupCount": 5,
        },
        "error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_ROOT + "/logs/django_error.log",
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 1,
            "backupCount": 5,
        },
    },
    "formatters": {
        "verbose": {
            "format": "\t".join(
                [
                    "[%(levelname)s]",
                    "%(asctime)s",
                    "%(name)s",
                    "%(message)s",
                ]
            )
        },
    },
    "loggers": {
        "info": {
            "handlers": ["info"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "error": {
            "handlers": ["error"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "ERROR"),
            "propagate": True,
        },
    },
}
