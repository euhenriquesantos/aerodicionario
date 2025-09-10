from django.db import models

 codex/create-glossary-views-and-routes

class Termo(models.Model):
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["titulo"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.titulo

 codex/enable-django-admin-in-urls.py

class Termo(models.Model):
    termo = models.CharField(max_length=100)
    definicao = models.TextField()

    def __str__(self):
        return self.termo

codex/add-termo-class-to-glossario-model

class Termo(models.Model):
    """Representa um termo do glossário."""

    titulo = models.CharField(max_length=200)
    definicao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple human-readable repr
        return self.titulo

# Create your models here.
main
main
 main
