from django.db import models


class Termo(models.Model):
    titulo = models.CharField("Sigla ou palavra", max_length=255)
    slug = models.SlugField(unique=True)
    decod_en = models.CharField(
        "Decodificação em inglês", max_length=255, blank=True
    )
    decod_pt = models.CharField(
        "Decodificação em português", max_length=255, blank=True
    )
    explicacao = models.TextField(blank=True)
    fotos = models.JSONField(blank=True, default=list)
    videos = models.JSONField(blank=True, default=list)
    links = models.JSONField(blank=True, default=list)

    class Meta:
        ordering = ["titulo"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.titulo
