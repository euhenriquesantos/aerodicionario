from rest_framework import serializers
from .models import Termo


class TermoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termo
        fields = ["id", "titulo", "slug", "descricao"]
