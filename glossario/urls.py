from django.urls import path

from . import views

app_name = "glossario"

urlpatterns = [
    path("", views.home, name="home"),
    path("dicionario/", views.lista_termos, name="lista_termos"),
    path("dicionario/<slug:slug>/", views.detalhes_termo, name="detalhes_termo"),
    path("sugerir/", views.sugerir, name="sugerir"),
    path("sugerir/<slug:slug>/", views.sugerir, name="sugerir_para_termo"),
    path("accounts/signup/", views.signup, name="signup"),
    path("conta/", views.perfil, name="perfil"),
    path("api/termos/", views.TermoListAPI.as_view(), name="api_lista_termos"),
    path("api/termos/<slug:slug>/", views.TermoDetailAPI.as_view(), name="api_detalhes_termo"),
    path("api/autocomplete/", views.AutocompleteAPI.as_view(), name="api_autocomplete"),
]
