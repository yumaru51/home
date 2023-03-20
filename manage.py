#!/usr/bin/env python
import os
import sys
from socket import gethostname

if __name__ == '__main__':

    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    host_name = gethostname()
    if host_name == 'YWEBSERV1':
        print('本番環境起動')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.settings_product')
    elif host_name == 'I7161DD6':
        print('テスト環境起動')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.settings_test')
    else:
        print('開発環境起動')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.settings_develop')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
