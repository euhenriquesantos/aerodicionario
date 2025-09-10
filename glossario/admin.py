from django.contrib import admin
codex/enable-django-admin-in-urls.py
from .models import Termo


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
    list_display = ("termo",)


# Register your models here.
 main
