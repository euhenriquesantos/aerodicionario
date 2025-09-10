from django.shortcuts import get_object_or_404, render
from rest_framework import generics

from .models import Termo
from .serializers import TermoSerializer


def lista_termos(request):
    busca = request.GET.get("q", "")
    termos = Termo.objects.all()
    if busca:
        termos = termos.filter(titulo__icontains=busca)
    context = {"termos": termos, "busca": busca}
    return render(request, "glossario/lista.html", context)


def detalhes_termo(request, slug):
    termo = get_object_or_404(Termo, slug=slug)
    return render(request, "glossario/detalhe.html", {"termo": termo})


class TermoListAPI(generics.ListAPIView):
    serializer_class = TermoSerializer

    def get_queryset(self):
        busca = self.request.query_params.get("q", "")
        qs = Termo.objects.all()
        if busca:
            qs = qs.filter(titulo__icontains=busca)
        return qs


class TermoDetailAPI(generics.RetrieveAPIView):
    queryset = Termo.objects.all()
    serializer_class = TermoSerializer
    lookup_field = "slug"
