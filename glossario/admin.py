from django.contrib import admin
 codex/create-glossary-views-and-routes

=======
codex/enable-django-admin-in-urls.py
 main
from .models import Termo


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
 codex/create-glossary-views-and-routes
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ["titulo"]

    list_display = ("termo",)


# Register your models here.
 main
 main
