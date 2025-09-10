from django.db import models

codex/add-termo-class-to-glossario-model

class Termo(models.Model):
    """Representa um termo do glossário."""

    titulo = models.CharField(max_length=200)
    definicao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple human-readable repr
        return self.titulo
=======
# Create your models here.
main
