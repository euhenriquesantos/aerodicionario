from django.core.exceptions import ValidationError
from django.db import models
import re
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import os


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

    class Meta:
        ordering = ["titulo"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.titulo


class TermoSinonimo(models.Model):
    termo = models.ForeignKey(Termo, related_name="sinonimos", on_delete=models.CASCADE, verbose_name="Termo")
    nome = models.CharField("Sinônimo/variante", max_length=255)

    class Meta:
        unique_together = ("termo", "nome")
        verbose_name = "Sinônimo"
        verbose_name_plural = "Sinônimos"

    def __str__(self) -> str:  # pragma: no cover
        return self.nome


def termo_image_upload_to(instance: "TermoImage", filename: str) -> str:
    return f"termos/{instance.termo.slug}/{filename}"


class TermoImage(models.Model):
    termo = models.ForeignKey(
        Termo, related_name="imagens", on_delete=models.CASCADE, verbose_name="Termo"
    )
    imagem = models.ImageField(upload_to=termo_image_upload_to, verbose_name="Imagem")
    alt_text = models.CharField("Texto alternativo (SEO)", max_length=255, blank=True)
    title = models.CharField("Título da imagem (opcional)", max_length=255, blank=True)
    caption = models.CharField("Legenda (opcional)", max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Imagem do termo"
        verbose_name_plural = "Imagens do termo"

    def __str__(self) -> str:  # pragma: no cover
        return f"Imagem de {self.termo.titulo}"

    def save(self, *args, **kwargs):  # gera variantes WebP após salvar
        super().save(*args, **kwargs)
        try:
            self._generate_variants()
        except Exception:
            pass

    def _variant_name(self, width: int) -> str:
        root, ext = os.path.splitext(self.imagem.name)
        return f"{root}_w{width}.webp"

    def _generate_variants(self):
        if not self.imagem:
            return
        path = self.imagem.name
        storage = self.imagem.storage
        with storage.open(path, "rb") as f:
            img = Image.open(f).convert("RGB")
            w, h = img.size
            for target in (320, 640, 1280):
                if w < target and h < target:
                    continue
                ratio = target / float(w)
                new_size = (target, int(h * ratio))
                resized = img.resize(new_size, Image.LANCZOS)
                buffer = BytesIO()
                resized.save(buffer, format="WEBP", quality=85)
                content = ContentFile(buffer.getvalue())
                variant_name = self._variant_name(target)
                if not storage.exists(variant_name):
                    storage.save(variant_name, content)


class TermoLink(models.Model):
    termo = models.ForeignKey(
        Termo, related_name="links_relacionados", on_delete=models.CASCADE, verbose_name="Termo"
    )
    url = models.URLField("URL")
    rotulo = models.CharField("Rótulo (opcional)", max_length=255, blank=True)

    class Meta:
        verbose_name = "Link relacionado"
        verbose_name_plural = "Links relacionados"

    def __str__(self) -> str:  # pragma: no cover
        return self.rotulo or self.url


YOUTUBE_REGEX = re.compile(
    r"""
    (?:https?:\/\/)?
    (?:
        (?:www\.)?youtube\.com\/(?:watch\?v=|embed\/|v\/)
        |
        youtu\.be\/
    )
    ([A-Za-z0-9_-]{11})
    """,
    re.VERBOSE,
)


class TermoVideo(models.Model):
    termo = models.ForeignKey(
        Termo, related_name="videos", on_delete=models.CASCADE, verbose_name="Termo"
    )
    youtube_url = models.URLField("URL do YouTube")
    youtube_id = models.CharField(max_length=20, editable=False, blank=True, verbose_name="ID do YouTube")

    def clean(self):  # Validate YouTube only
        match = YOUTUBE_REGEX.search(self.youtube_url or "")
        if not match:
            raise ValidationError({"youtube_url": "Informe um link válido do YouTube."})
        self.youtube_id = match.group(1)

    def save(self, *args, **kwargs):  # pragma: no cover
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return f"YouTube {self.youtube_id}"


class Suggestion(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendente"),
        ("approved", "Aprovada"),
        ("rejected", "Rejeitada"),
    )
    CHANGE_CHOICES = (
        ("create", "Criar novo termo"),
        ("complement", "Complementar informações"),
        ("correction", "Correção de informação"),
        ("media", "Adicionar imagens/links/vídeos"),
        ("other", "Outro"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    termo = models.ForeignKey(Termo, null=True, blank=True, on_delete=models.SET_NULL)
    titulo = models.CharField("Sigla ou palavra", max_length=255, blank=True)
    decod_en = models.CharField("Decodificação em inglês", max_length=255, blank=True)
    decod_pt = models.CharField("Decodificação em português", max_length=255, blank=True)
    explicacao = models.TextField(blank=True)
    change_type = models.CharField("Tipo de sugestão", max_length=20, choices=CHANGE_CHOICES, default="complement")
    justification = models.TextField("Justificativa", blank=True)
    source_url = models.URLField("Fonte (URL)", blank=True)
    status = models.CharField("Status", max_length=16, choices=STATUS_CHOICES, default="pending")
    admin_notes = models.TextField("Notas do administrador", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sugestão"
        verbose_name_plural = "Sugestões"

    def __str__(self) -> str:  # pragma: no cover
        if self.termo:
            return f"Sugestão para {self.termo.titulo} por {self.user}"
        return f"Nova sugestão '{self.titulo}' por {self.user}"


def suggestion_image_upload_to(instance: "SuggestionImage", filename: str) -> str:
    base = instance.suggestion.termo.slug if instance.suggestion.termo else "novo"
    return f"sugestoes/{base}/{filename}"


class SuggestionImage(models.Model):
    suggestion = models.ForeignKey(Suggestion, related_name="imagens", on_delete=models.CASCADE, verbose_name="Sugestão")
    imagem = models.ImageField(upload_to=suggestion_image_upload_to, verbose_name="Imagem")
    alt_text = models.CharField("Texto alternativo (SEO)", max_length=255, blank=True)
    title = models.CharField("Título", max_length=255, blank=True)
    caption = models.CharField("Legenda", max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["suggestion", "imagem"], name="uniq_suggestion_image_path"),
        ]

    def save(self, *args, **kwargs):  # gera variantes WebP para preview ágil
        super().save(*args, **kwargs)
        try:
            self._generate_variants()
        except Exception:
            pass

    def _variant_name(self, width: int) -> str:
        root, ext = os.path.splitext(self.imagem.name)
        return f"{root}_w{width}.webp"

    def _generate_variants(self):
        if not self.imagem:
            return
        path = self.imagem.name
        storage = self.imagem.storage
        with storage.open(path, "rb") as f:
            img = Image.open(f).convert("RGB")
            w, h = img.size
            for target in (320, 640):
                if w < target and h < target:
                    continue
                ratio = target / float(w)
                new_size = (target, int(h * ratio))
                resized = img.resize(new_size, Image.LANCZOS)
                buffer = BytesIO()
                resized.save(buffer, format="WEBP", quality=80)
                content = ContentFile(buffer.getvalue())
                variant_name = self._variant_name(target)
                if not storage.exists(variant_name):
                    storage.save(variant_name, content)


class SuggestionLink(models.Model):
    suggestion = models.ForeignKey(Suggestion, related_name="links", on_delete=models.CASCADE, verbose_name="Sugestão")
    url = models.URLField("URL")
    rotulo = models.CharField("Rótulo (opcional)", max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["suggestion", "url"], name="uniq_suggestion_link_url"),
        ]


class SuggestionVideo(models.Model):
    suggestion = models.ForeignKey(Suggestion, related_name="videos", on_delete=models.CASCADE, verbose_name="Sugestão")
    youtube_url = models.URLField("URL do YouTube")
    youtube_id = models.CharField("ID do YouTube", max_length=20, editable=False, blank=True)

    def clean(self):  # Validate YouTube
        match = YOUTUBE_REGEX.search(self.youtube_url or "")
        if not match:
            raise ValidationError({"youtube_url": "Informe um link válido do YouTube."})
        self.youtube_id = match.group(1)

    def save(self, *args, **kwargs):  # pragma: no cover
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["suggestion", "youtube_id"], name="uniq_suggestion_video_id"),
        ]


class SuggestionApplicationLog(models.Model):
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="aplicacoes")
    termo = models.ForeignKey(Termo, on_delete=models.CASCADE, related_name="logs_aplicacao")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fields_changed = models.JSONField(default=list)
    media_added = models.IntegerField(default=0)
    links_added = models.IntegerField(default=0)
    videos_added = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log de aplicação de sugestão"
        verbose_name_plural = "Logs de aplicação de sugestão"


class TermoHistory(models.Model):
    termo = models.ForeignKey(Termo, on_delete=models.CASCADE, related_name="historico")
    previous_titulo = models.CharField(max_length=255)
    previous_decod_en = models.CharField(max_length=255, blank=True)
    previous_decod_pt = models.CharField(max_length=255, blank=True)
    previous_explicacao = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Histórico de termo"
        verbose_name_plural = "Histórico de termos"

    def __str__(self) -> str:  # pragma: no cover
        return f"Histórico {self.termo.titulo} em {self.created_at:%Y-%m-%d %H:%M}"


def settings_upload_to(instance: "SiteSetting", filename: str) -> str:
    return f"branding/{filename}"


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=120, default="Aerodicionário")
    default_meta_description = models.TextField(
        blank=True,
        default="Glossário de termos e siglas da aviação para estudantes e profissionais do setor aéreo.",
    )
    default_og_image = models.ImageField(upload_to=settings_upload_to, blank=True)
    site_logo = models.ImageField(upload_to=settings_upload_to, blank=True)
    favicon = models.ImageField(upload_to=settings_upload_to, blank=True)
    primary_color = models.CharField(max_length=7, default="#0e76e6", help_text="#RRGGBB")
    secondary_color = models.CharField(max_length=7, default="#065ec0", help_text="#RRGGBB")
    meta_keywords = models.TextField(blank=True)
    meta_title_suffix = models.CharField(max_length=60, blank=True, default=" - Aerodicionário")
    enable_indexing = models.BooleanField(default=True)
    analytics_code = models.TextField(blank=True, help_text="Cole aqui scripts de analytics (ex.: gtag).")
    hero_title = models.CharField(max_length=200, blank=True, default="Seu guia de termos e siglas da aviação")
    hero_subtitle = models.CharField(max_length=240, blank=True, default="Da cabine de comando ao solo, descubra a linguagem que move o céu.")
    hero_eyebrow = models.CharField(max_length=80, blank=True, default="AERODICIONÁRIO",
                                    help_text="Texto pequeno acima do título da home")
    hero_badge_text = models.CharField(max_length=140, blank=True, default="Simples, rápido e 100% gratuito.")
    search_placeholder = models.CharField(max_length=160, blank=True, default="Buscar termos (ex.: IFR, NOTAM, APU)")
    items_per_page = models.PositiveIntegerField(default=12)
    enable_autocomplete = models.BooleanField(default=True)
    autocomplete_throttle_ms = models.PositiveIntegerField(default=1000)
    robots_txt = models.TextField(blank=True, default="User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n")
    social_twitter = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_youtube = models.URLField(blank=True)
    social_linkedin = models.URLField(blank=True)
    footer_text = models.CharField(max_length=200, blank=True)
    custom_css = models.TextField(blank=True)
    custom_js_head = models.TextField(blank=True)
    custom_js_body = models.TextField(blank=True)
    suggestions_enabled = models.BooleanField(default=True)
    suggestions_require_source = models.BooleanField(default=True)
    suggestions_min_justification = models.PositiveIntegerField(default=15)
    suggestion_max_image_mb = models.PositiveIntegerField(default=6)
    suggestion_rate_limit_seconds = models.PositiveIntegerField(default=5)

    # Landing page dinâmicas
    hero_image = models.ImageField(upload_to=settings_upload_to, blank=True)
    hero_image_alt = models.CharField(max_length=150, blank=True, default="Imagem de destaque")
    cta_primary_text = models.CharField(max_length=40, blank=True, default="Consultar Dicionário")
    cta_primary_url = models.URLField(blank=True, default="/dicionario/")
    cta_secondary_text = models.CharField(max_length=40, blank=True, default="Saiba mais")
    cta_secondary_url = models.URLField(blank=True, default="#sobre")
    show_about = models.BooleanField(default=True)
    about_title = models.CharField(max_length=120, blank=True, default="Sobre o Aerodicionário")
    about_html = models.TextField(blank=True, default="<p>O Aerodicionário reúne definições claras e objetivas para estudantes, entusiastas e profissionais do setor aéreo.</p>")
    show_features = models.BooleanField(default=True)
    features_title = models.CharField(max_length=120, blank=True, default="Por que usar o Aerodicionário?")
    features_html = models.TextField(blank=True, default="<ul><li>Conteúdo atualizado</li><li>Busca rápida</li><li>Acesso gratuito</li></ul>")
    show_how = models.BooleanField(default=True, help_text="Exibir seção 'Como funciona'")
    how_title = models.CharField(max_length=120, blank=True, default="Como funciona")
    how_html = models.TextField(blank=True)
    show_faq = models.BooleanField(default=True, help_text="Exibir seção de FAQ")
    faq_title = models.CharField(max_length=120, blank=True, default="Perguntas frequentes")
    faq_html = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configurações do site"
        verbose_name_plural = "Configurações do site"

    def __str__(self) -> str:  # pragma: no cover
        return "Configurações do site"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
