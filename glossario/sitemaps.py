from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Termo


class TermoSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Termo.objects.all()

    def location(self, obj):
        return reverse("glossario:detalhes_termo", args=[obj.slug])


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["glossario:home", "glossario:lista_termos"]

    def location(self, item):
        return reverse(item)

