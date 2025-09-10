"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
codex/create-glossary-views-and-routes
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/

codex/enable-django-admin-in-urls.py
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/

https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
 main
 main
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
