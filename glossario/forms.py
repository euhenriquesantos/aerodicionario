from django import forms
from .models import Suggestion, Termo
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        # retorna uma lista de arquivos (ou lista vazia)
        if not files:
            return []
        return files.getlist(name)


class MultiFileField(forms.Field):
    widget = MultiFileInput

    def __init__(self, *args, max_mb=6, **kwargs):
        self.max_mb = max_mb
        super().__init__(*args, **kwargs)

    def clean(self, data):
        files = data or []
        cleaned = []
        for f in files:
            if not (getattr(f, 'content_type', '') or '').startswith('image'):
                raise ValidationError("Envie apenas arquivos de imagem.")
            if f.size > self.max_mb * 1024 * 1024:
                raise ValidationError(f"Cada imagem deve ter no máximo {self.max_mb} MB.")
            cleaned.append(f)
        return cleaned


class SuggestionForm(forms.ModelForm):
    imagens = MultiFileField(required=False, widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"}),
                             help_text="Você pode enviar múltiplas imagens (JPG/PNG/WebP).")
    links_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Uma URL por linha (inclua http(s)://)", "class": "form-control"}),
        label="Links",
        help_text="Formato: http(s)://exemplo.com — uma por linha.",
    )
    videos_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "URLs do YouTube (https://youtu.be/... ou https://www.youtube.com/watch?v=...), uma por linha", "class": "form-control"}),
        label="Vídeos (YouTube)",
        help_text="Apenas links do YouTube são aceitos. Uma URL por linha.",
    )
    source_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "Link da fonte (site, documento etc.)", "class": "form-control"}),
        label="Fonte (URL)",
        help_text="Obrigatório para correções. Sempre informe uma fonte confiável.",
    )

    change_type = forms.ChoiceField(
        label="Tipo de sugestão",
        choices=Suggestion.CHANGE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    justification = forms.CharField(
        label="Justificativa",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Explique o motivo da alteração, cite fonte se possível.", "class": "form-control"}),
    )

    class Meta:
        model = Suggestion
        fields = [
            "termo",
            "titulo",
            "decod_en",
            "decod_pt",
            "explicacao",
            "change_type",
            "justification",
            "source_url",
        ]
        widgets = {
            "termo": forms.Select(attrs={"class": "form-select"}),
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex.: AFIZ"}),
            "decod_en": forms.TextInput(attrs={"class": "form-control"}),
            "decod_pt": forms.TextInput(attrs={"class": "form-control"}),
            "explicacao": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def clean(self):
        data = super().clean()
        termo: Termo | None = data.get("termo")
        # Sanitiza campos textuais
        for key in ["titulo", "decod_en", "decod_pt", "explicacao", "justification", "links_text", "videos_text"]:
            if key in data and isinstance(data.get(key), str):
                data[key] = strip_tags(data.get(key)).strip()

        titulo = (data.get("titulo") or "").strip()
        if not termo and not titulo:
            raise forms.ValidationError("Informe um título quando não houver termo selecionado.")

        # precisa ter ao menos uma contribuição
        has_payload = any([
            titulo,
            (data.get("decod_en") or "").strip(),
            (data.get("decod_pt") or "").strip(),
            (data.get("explicacao") or "").strip(),
            bool(self.files.getlist("imagens")),
            bool((data.get("links_text") or "").strip()),
            bool((data.get("videos_text") or "").strip()),
        ])
        if not has_payload:
            raise forms.ValidationError("Inclua pelo menos um campo (definição, tradução, link, vídeo ou imagem).")

        # se for sugestão para termo existente, valide duplicidade e justificativa
        if termo:
            same_en = data.get("decod_en", "").strip() and data.get("decod_en").strip() == (termo.decod_en or "").strip()
            same_pt = data.get("decod_pt", "").strip() and data.get("decod_pt").strip() == (termo.decod_pt or "").strip()
            same_exp = data.get("explicacao", "").strip() and data.get("explicacao").strip() == (termo.explicacao or "").strip()

            if same_en or same_pt or same_exp:
                raise forms.ValidationError("Sua sugestão repete uma informação que já existe no termo.")

            # termo já tem conteúdo considerado 'completo'? então justificativa é obrigatória
            has_core = bool((termo.decod_en or termo.decod_pt or "").strip()) or bool((termo.explicacao or "").strip())
            has_media = termo.imagens.exists() or termo.links_relacionados.exists() or termo.videos.exists()
            change_type = data.get("change_type")
            requires_just = change_type in ["correction", "complement", "media"] and (has_core or has_media)
            just = (data.get("justification") or "").strip()
            if requires_just and len(just) < 15:
                raise forms.ValidationError("Descreva uma justificativa (mín. 15 caracteres) para alteração em termo já preenchido.")

            # Correção exige fonte
            if change_type == "correction":
                src = (data.get("source_url") or "").strip()
                if not src:
                    raise forms.ValidationError("Para correções, informe uma fonte (URL).")
        else:
            # criação exige ao menos título e um conteúdo (decod/explicação ou mídia)
            if not titulo:
                raise forms.ValidationError("Para criar um novo termo, informe a Sigla/Palavra.")
            if not any([(data.get("decod_en") or data.get("decod_pt") or data.get("explicacao"))] + [bool(self.files.getlist("imagens")), bool((data.get("links_text") or "").strip()), bool((data.get("videos_text") or "").strip())]):
                raise forms.ValidationError("Para criar, inclua pelo menos uma definição (EN/PT/Resumo) ou mídia/links/vídeos.")
        return data

    # clean_imagens removido — validação acontece no MultiFileField


class ProfileForm(forms.ModelForm):
    username = forms.CharField(label="Usuário", disabled=True)

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
        }
