"""
WSGI config for cpexcel project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys
from socket import gethostname

from django.core.wsgi import get_wsgi_application

sys.path.append('C:/Python_too_development/isk_tools/config')
sys.path.append('C:/Python_too_development/isk_tools/common')

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
host_name = gethostname()
if host_name == 'YWEBSERV1':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.settings_product'
elif host_name == 'I7161DD6':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.settings_test'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.settings_develop'

application = get_wsgi_application()
