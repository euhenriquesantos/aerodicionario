from django.contrib import admin

from .models import Termo


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ["titulo"]
    list_display = ("titulo",)
