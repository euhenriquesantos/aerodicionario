from django.db import models

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
