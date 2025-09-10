from rest_framework import serializers
from .models import Termo


class TermoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termo
        fields = [
            "id",
            "titulo",
            "slug",
            "decod_en",
            "decod_pt",
            "explicacao",
            "fotos",
            "videos",
            "links",
        ]
        extra_kwargs = {
            "fotos": {"required": False},
            "videos": {"required": False},
        }
