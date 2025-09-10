from django.contrib import admin
from .models import Termo


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
    list_display = ("termo",)
