from django.urls import path

from . import views

app_name = "glossario"

urlpatterns = [
    path("termos/", views.lista_termos, name="lista_termos"),
    path("termos/<slug:slug>/", views.detalhes_termo, name="detalhes_termo"),
    path("api/termos/", views.TermoListAPI.as_view(), name="api_lista_termos"),
    path("api/termos/<slug:slug>/", views.TermoDetailAPI.as_view(), name="api_detalhes_termo"),
]
