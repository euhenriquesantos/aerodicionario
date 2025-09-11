"""URL configuration for the aerodicionario project."""

from django.contrib import admin
from django.urls import include, path
from glossario import views as gviews
from django.contrib.sitemaps.views import sitemap
from glossario.sitemaps import TermoSitemap, StaticSitemap
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Override login/logout to add messages
    path("accounts/login/", gviews.login_view, name="login"),
    path("accounts/logout/", gviews.logout_view, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": {"termos": TermoSitemap, "static": StaticSitemap}}, name="sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("", include("glossario.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
