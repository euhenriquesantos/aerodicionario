from django.db import models


class Termo(models.Model):
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["titulo"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.titulo
