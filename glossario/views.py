from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers

from .models import Termo, TermoSinonimo, SiteSetting
from .serializers import TermoSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth import logout as auth_logout
from .forms import SuggestionForm, ProfileForm
from .models import Suggestion, SuggestionImage, SuggestionLink, SuggestionVideo
from django.core.paginator import Paginator


def home(request):
    """Landing page for the project."""
    return render(request, "home.html")


@cache_page(60 * 2)
def lista_termos(request):
    busca = request.GET.get("q", "").strip()
    letra = request.GET.get("letra", "").upper().strip()
    alfabeto = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

    termos = Termo.objects.all()

    if busca:
        termos = termos.filter(
            Q(titulo__icontains=busca)
            | Q(decod_en__icontains=busca)
            | Q(decod_pt__icontains=busca)
            | Q(sinonimos__nome__icontains=busca)
        ).distinct()

    if letra:
        if letra in alfabeto:
            termos = termos.filter(titulo__istartswith=letra)

    # contadores por letra
    letter_counts = {l: Termo.objects.filter(titulo__istartswith=l).count() for l in alfabeto}

    per_page = SiteSetting.get_solo().items_per_page or 12
    paginator = Paginator(termos, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "termos": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "busca": busca,
        "letra": letra,
        "alfabeto": alfabeto,
        "letter_counts": letter_counts,
    }
    return render(request, "glossario/lista.html", context)


@cache_page(60 * 5)
def detalhes_termo(request, slug):
    termo = get_object_or_404(Termo, slug=slug)
    relacionados = Termo.objects.filter(titulo__istartswith=termo.titulo[:1]).exclude(pk=termo.pk)[:6]
    return render(request, "glossario/detalhe.html", {"termo": termo, "relacionados": relacionados})


@login_required
def sugerir(request, slug=None):
    termo = None
    if slug:
        termo = get_object_or_404(Termo, slug=slug)
    # rate limit simples para POST
    if request.method == "POST":
        ip = request.META.get("REMOTE_ADDR", "")
        key = f"sug_rl:{ip}"
        if cache.get(key):
            messages.error(request, "Você está enviando sugestões muito rápido. Tente novamente em instantes.")
            return redirect("glossario:sugerir" if not termo else "glossario:sugerir_para_termo", slug=termo.slug if termo else None)
        cache.set(key, True, 5)
        form = SuggestionForm(request.POST, request.FILES)
        if form.is_valid():
            suggestion: Suggestion = form.save(commit=False)
            suggestion.user = request.user
            suggestion.save()

            # Imagens múltiplas
            for f in request.FILES.getlist("imagens"):
                SuggestionImage.objects.create(suggestion=suggestion, imagem=f)

            # Links
            links_text = form.cleaned_data.get("links_text") or ""
            seen_links = set()
            for line in [l.strip() for l in links_text.splitlines() if l.strip()]:
                # normaliza esquemas ausentes
                url = line
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url
                if url in seen_links:
                    continue
                seen_links.add(url)
                try:
                    SuggestionLink.objects.create(suggestion=suggestion, url=url)
                except Exception:
                    # ignora URLs inválidas
                    continue

            # Vídeos (YouTube)
            videos_text = form.cleaned_data.get("videos_text") or ""
            seen_vids = set()
            for line in [l.strip() for l in videos_text.splitlines() if l.strip()]:
                try:
                    # valida e extrai id (o model já faz isso, mas usamos p/deduplicar)
                    tmp = SuggestionVideo(suggestion=suggestion, youtube_url=line)
                    tmp.clean()
                    if tmp.youtube_id in seen_vids:
                        continue
                    seen_vids.add(tmp.youtube_id)
                    tmp.save()
                except Exception:
                    continue

            messages.success(request, "Obrigado! Sua sugestão foi enviada para revisão.")
            return redirect("glossario:perfil")
    else:
        initial = {"termo": termo} if termo else {}
        # inicialização por querystring (change_type/justification)
        if request.GET.get("change_type"):
            initial["change_type"] = request.GET.get("change_type")
        if request.GET.get("justification"):
            initial["justification"] = request.GET.get("justification")
        form = SuggestionForm(initial=initial)
    return render(request, "glossario/sugerir.html", {"form": form, "termo": termo})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("glossario:home")
    else:
        form = UserCreationForm()
    # aplica classes Bootstrap
    for f in form.fields.values():
        css = f.widget.attrs.get("class", "")
        f.widget.attrs["class"] = (css + " form-control").strip()
    return render(request, "registration/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Bem-vindo de volta!")
            next_url = request.GET.get("next") or request.POST.get("next") or "glossario:home"
            return redirect(next_url)
    else:
        form = AuthenticationForm(request)
    for f in form.fields.values():
        css = f.widget.attrs.get("class", "")
        f.widget.attrs["class"] = (css + " form-control").strip()
    return render(request, "registration/login.html", {"form": form})


@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect("glossario:home")


@login_required
def perfil(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado!")
            return redirect("glossario:perfil")
    else:
        form = ProfileForm(instance=request.user)

    sugestoes = Suggestion.objects.filter(user=request.user).select_related("termo")
    return render(
        request,
        "glossario/perfil.html",
        {"form": form, "sugestoes": sugestoes, "user_obj": request.user},
    )


class TermoListAPI(generics.ListAPIView):
    serializer_class = TermoSerializer

    def get_queryset(self):
        busca = self.request.query_params.get("q", "")
        qs = Termo.objects.all()
        if busca:
            qs = qs.filter(
                Q(titulo__icontains=busca)
                | Q(decod_en__icontains=busca)
                | Q(decod_pt__icontains=busca)
            )
        return qs


class TermoDetailAPI(generics.RetrieveAPIView):
    queryset = Termo.objects.all()
    serializer_class = TermoSerializer
    lookup_field = "slug"


class AutocompleteAPI(APIView):
    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        # rate limit simples por IP+q
        key = f"ac_rl:{request.META.get('REMOTE_ADDR')}:{q.lower()}"
        if cache.get(key):
            return Response({"results": []})
        cache.set(key, True, 1)
        items = []
        if q:
            base = (
                Termo.objects.filter(
                    Q(titulo__icontains=q)
                    | Q(decod_en__icontains=q)
                    | Q(decod_pt__icontains=q)
                    | Q(sinonimos__nome__icontains=q)
                ).distinct().order_by("titulo")[:30]
            )
            def rank(t: Termo):
                ql = q.lower()
                title = (t.titulo or '').lower()
                en = (t.decod_en or '').lower()
                pt = (t.decod_pt or '').lower()
                syns = ' '.join(s.nome for s in getattr(t, 'sinonimos').all()) if hasattr(t, 'sinonimos') else ''
                syns = syns.lower()
                score = 0
                if title.startswith(ql): score -= 100
                if ql in title: score -= 50
                if syns.startswith(ql): score -= 40
                if ql in syns: score -= 30
                if en.startswith(ql) or pt.startswith(ql): score -= 20
                if ql in en or ql in pt: score -= 10
                return (score, t.titulo)
            items_sorted = sorted(list(base), key=rank)[:8]
            items = [{"label": t.titulo, "slug": t.slug, "decod": t.decod_pt or t.decod_en or ""} for t in items_sorted]
        return Response({"results": items})
