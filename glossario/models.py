from django.db import models


class Termo(models.Model):
    termo = models.CharField(max_length=100)
    definicao = models.TextField()

    def __str__(self):
        return self.termo
