from django import forms
from django.contrib import admin

from .models import Termo


class TermoAdminForm(forms.ModelForm):
    fotos = forms.JSONField(required=False, widget=forms.Textarea, initial=list)
    videos = forms.JSONField(required=False, widget=forms.Textarea, initial=list)
    links = forms.JSONField(required=False, widget=forms.Textarea, initial=list)

    class Meta:
        model = Termo
        fields = "__all__"

    def clean_fotos(self):
        return self.cleaned_data.get("fotos") or []

    def clean_videos(self):
        return self.cleaned_data.get("videos") or []

    def clean_links(self):
        return self.cleaned_data.get("links") or []


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
    form = TermoAdminForm
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ["titulo", "decod_en", "decod_pt"]
    list_display = ("titulo", "decod_en", "decod_pt")


admin.site.site_header = "Aerodicionário Superadmin"
admin.site.site_title = "Aerodicionário Superadmin"
admin.site.index_title = "Gerenciamento do Aerodicionário"
