"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
codex/enable-django-admin-in-urls.py
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/

https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
 main
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
