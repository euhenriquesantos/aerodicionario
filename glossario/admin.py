from django.contrib import admin
from .models import (
    Termo,
    TermoImage,
    TermoLink,
    TermoVideo,
    TermoSinonimo,
    Suggestion,
    SuggestionImage,
    SuggestionLink,
    SuggestionVideo,
    SuggestionApplicationLog,
    TermoHistory,
    SiteSetting,
)
from django.core.files.base import File
from django.db import transaction
import os
from django import forms
from django.utils.text import slugify
from django.contrib import messages
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils.html import strip_tags
import csv
import re
import io


class TermoImageInline(admin.StackedInline):
    model = TermoImage
    extra = 1
    fields = ("imagem", "alt_text", "title", "caption", "ordem")


class TermoLinkInline(admin.TabularInline):
    model = TermoLink
    extra = 1
    fields = ("url", "rotulo")


class TermoVideoInline(admin.TabularInline):
    model = TermoVideo
    extra = 1
    fields = ("youtube_url",)

class TermoSinonimoInline(admin.TabularInline):
    model = TermoSinonimo
    extra = 1
    fields = ("nome",)


class SuggestionLogInline(admin.TabularInline):
    model = SuggestionApplicationLog
    extra = 0
    can_delete = False
    readonly_fields = (
        "created_at",
        "approver",
        "fields_changed",
        "media_added",
        "links_added",
        "videos_added",
        "notes",
        "suggestion",
    )
    fields = readonly_fields
    verbose_name_plural = "Histórico de aplicações de sugestões"


@admin.register(Termo)
class TermoAdmin(admin.ModelAdmin):
    inlines = [TermoSinonimoInline, TermoImageInline, TermoLinkInline, TermoVideoInline, SuggestionLogInline]
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ["titulo", "decod_en", "decod_pt"]
    list_display = ("titulo", "decod_en", "decod_pt", "preview_site")
    change_list_template = "admin/glossario/termo/change_list.html"
    # filtros

    class LetraInicialFilter(admin.SimpleListFilter):
        title = "Letra inicial"
        parameter_name = "letra"

        def lookups(self, request, model_admin):
            return [(chr(c), chr(c)) for c in range(ord("A"), ord("Z") + 1)]

        def queryset(self, request, queryset):
            v = self.value()
            if v:
                return queryset.filter(titulo__istartswith=v)
            return queryset

    class HasImagemFilter(admin.SimpleListFilter):
        title = "Imagens"
        parameter_name = "has_img"

        def lookups(self, request, model_admin):
            return (("yes", "Com imagem"), ("no", "Sem imagem"))

        def queryset(self, request, queryset):
            v = self.value()
            if v == "yes":
                return queryset.filter(imagens__isnull=False).distinct()
            if v == "no":
                return queryset.filter(imagens__isnull=True)
            return queryset

    list_filter = (LetraInicialFilter, HasImagemFilter)

    class CSVImportForm(forms.Form):
        arquivo = forms.FileField(label="Arquivo CSV")

    def import_csv_view(self, request):
        opts = self.model._meta
        if request.method == "POST":
            form = self.CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded = form.cleaned_data["arquivo"]
                content = uploaded.read().decode("utf-8-sig", errors="ignore")
                report = self._process_csv_content(content)
                self.message_user(request, report, level=messages.SUCCESS)
                changelist_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
                return HttpResponseRedirect(changelist_url)
        else:
            form = self.CSVImportForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": opts,
            "title": "Importar termos de CSV",
            "form": form,
        }
        return TemplateResponse(request, "admin/glossario/termo/import_csv.html", context)

    # Auxiliar: processa conteúdo CSV e retorna relatório de importação
    def _process_csv_content(self, content: str) -> str:
        created = updated = link_count = video_count = 0
        duplicates_in_file = 0
        seen_slugs: set[str] = set()

        def split_multi(val: str) -> list[str]:
            if not val:
                return []
            parts = re.split(r"[\s;,]+", val.strip())
            return [p for p in parts if p]

        def normalize_url(u: str) -> str:
            if not u:
                return ""
            if not re.match(r"^https?://", u, re.I):
                return "https://" + u
            return u

        # Divide em linhas, encontra o cabeçalho e reconstroi um fluxo a partir dele
        lines = content.splitlines()
        header_idx = None
        for i, line in enumerate(lines[:200]):
            if "sigla ou palavra" in line.lower():
                header_idx = i
                break
        if header_idx is None:
            return "Cabeçalho não encontrado no CSV. Garanta que exista a coluna 'SIGLA OU PALAVRA'."

        sliced = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(sliced))
        field_map = { (k or "").lower().strip(): (k or "") for k in (reader.fieldnames or []) }

        def get(row, key):
            # Busca a coluna por nome normalizado
            k = field_map.get(key.lower())
            if k:
                return row.get(k, "")
            # fallback por variações
            for cand in [key, key.lower(), key.upper()]:
                if cand in row:
                    return row[cand]
            return ""

        for row in reader:
            titulo = (get(row, "SIGLA OU PALAVRA") or "").strip()
            if not titulo:
                continue
            slug = slugify(titulo)
            if slug in seen_slugs:
                duplicates_in_file += 1
            seen_slugs.add(slug)

            dec_en = (get(row, "DECODIFICAÇÃO EM INGLÊS") or "").strip()
            dec_pt = (get(row, "DECODIFICAÇÃO EM PORTUGUÊS") or "").strip()
            explic = (get(row, "EXPLICAÇÃO") or "").strip()
            raw_videos = split_multi(get(row, "VÍDEOS") or get(row, "VIDEOS"))
            raw_links = split_multi(get(row, "LINKS"))

            termo, was_created = Termo.objects.get_or_create(slug=slug, defaults={
                "titulo": titulo,
                "decod_en": dec_en,
                "decod_pt": dec_pt,
                "explicacao": explic,
            })

            if was_created:
                created += 1
            else:
                changed = False
                if titulo and termo.titulo != titulo:
                    termo.titulo = titulo; changed = True
                if dec_en and termo.decod_en != dec_en:
                    termo.decod_en = dec_en; changed = True
                if dec_pt and termo.decod_pt != dec_pt:
                    termo.decod_pt = dec_pt; changed = True
                if explic and termo.explicacao != explic:
                    termo.explicacao = explic; changed = True
                if changed:
                    termo.save(); updated += 1

            for link in raw_links:
                url = normalize_url(link)
                if not url:
                    continue
                TermoLink.objects.get_or_create(termo=termo, url=url)
                link_count += 1

            for v in raw_videos:
                url = normalize_url(v)
                if not url:
                    continue
                try:
                    TermoVideo.objects.get_or_create(termo=termo, youtube_url=url)
                    video_count += 1
                except Exception:
                    continue

        return (
            f"Importação concluída. Criados: {created}, Atualizados: {updated}, "
            f"Links adicionados: {link_count}, Vídeos adicionados: {video_count}. "
            f"Duplicatas no CSV: {duplicates_in_file}."
        )

    # Link para visualizar no site
    def preview_site(self, obj):
        try:
            from django.urls import reverse as site_reverse
            url = site_reverse("glossario:detalhes_termo", args=[obj.slug])
            return format_html("<a href='{}' target='_blank'>Ver no site ↗︎</a>", url)
        except Exception:
            return "—"

    preview_site.short_description = "Preview"
    preview_site.allow_tags = True

    # Exportação CSV com colunas básicas
    actions = ["exportar_csv"]

    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = "attachment; filename=termos.csv"
        writer = csv.writer(response)
        writer.writerow(["SIGLA OU PALAVRA", "DECODIFICAÇÃO EM INGLÊS", "DECODIFICAÇÃO EM PORTUGUÊS", "EXPLICAÇÃO"]) 
        for t in queryset:
            writer.writerow([t.titulo, t.decod_en, t.decod_pt, t.explicacao])
        return response

    exportar_csv.short_description = "Exportar termos selecionados (CSV)"

    # Histórico – salva snapshot antes de alterar
    def save_model(self, request, obj, form, change):
        from .models import TermoHistory
        if change:
            prev = Termo.objects.get(pk=obj.pk)
            TermoHistory.objects.create(
                termo=prev,
                previous_titulo=prev.titulo,
                previous_decod_en=prev.decod_en,
                previous_decod_pt=prev.decod_pt,
                previous_explicacao=prev.explicacao,
                changed_by=request.user if request.user.is_authenticated else None,
            )
        super().save_model(request, obj, form, change)

    # Ação de reverter (seleciona um histórico e reverte manualmente pela tela do histórico)

    # URL custom para reverter para o último histórico
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "importar-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="glossario_termo_import_csv",
            ),
            path(
                '<path:object_id>/revert-last/',
                self.admin_site.admin_view(self.revert_last),
                name='glossario_termo_revert_last',
            ),
            path(
                '<path:object_id>/revert-to/<int:hist_id>/',
                self.admin_site.admin_view(self.revert_to),
                name='glossario_termo_revert_to',
            ),
        ]
        return custom + urls

    def revert_last(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not obj:
            return HttpResponseRedirect('../')
        hist = obj.historico.first()
        if not hist:
            self.message_user(request, "Sem histórico para reverter.")
            return HttpResponseRedirect('../')
        obj.titulo = hist.previous_titulo
        obj.decod_en = hist.previous_decod_en
        obj.decod_pt = hist.previous_decod_pt
        obj.explicacao = hist.previous_explicacao
        obj.save()
        self.message_user(request, "Termo revertido para o último histórico.")
        return HttpResponseRedirect('../../')

    def revert_to(self, request, object_id, hist_id):
        obj = self.get_object(request, object_id)
        if not obj:
            return HttpResponseRedirect('../')
        hist = TermoHistory.objects.filter(pk=hist_id, termo=obj).first()
        if not hist:
            self.message_user(request, "Histórico não encontrado.")
            return HttpResponseRedirect('../../')
        obj.titulo = hist.previous_titulo
        obj.decod_en = hist.previous_decod_en
        obj.decod_pt = hist.previous_decod_pt
        obj.explicacao = hist.previous_explicacao
        obj.save()
        self.message_user(request, "Termo revertido para o histórico selecionado.")
        return HttpResponseRedirect('../../../')


class SuggestionImageInline(admin.StackedInline):
    model = SuggestionImage
    extra = 0


class SuggestionLinkInline(admin.TabularInline):
    model = SuggestionLink
    extra = 0


class SuggestionVideoInline(admin.TabularInline):
    model = SuggestionVideo
    extra = 0


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "termo", "titulo", "change_type", "status", "impacto", "created_at", "acoes")
    list_filter = ("status", "change_type", "created_at")
    search_fields = ("titulo", "termo__titulo", "user__username")
    inlines = [SuggestionImageInline, SuggestionLinkInline, SuggestionVideoInline]
    actions = ["aprovar", "rejeitar", "aplicar_ao_termo"]
    change_form_template = "admin/glossario/suggestion/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("moderar/", self.admin_site.admin_view(self.moderar_view), name="glossario_suggestion_moderar"),
        ]
        return custom + urls

    def moderar_view(self, request):
        # fila simples: pega o próximo id pendente ou o id especificado via GET
        from django.shortcuts import get_object_or_404, redirect
        sid = request.GET.get("id")
        act = request.GET.get("action")
        if sid:
            sug = get_object_or_404(Suggestion, pk=sid)
        else:
            sug = Suggestion.objects.filter(status="pending").order_by("created_at").first()
            if not sug:
                self.message_user(request, "Não há sugestões pendentes.")
                return HttpResponseRedirect(reverse("admin:glossario_suggestion_changelist"))

        # Aprovação via GET action (para botões inline)
        if act in {"approve", "reject"}:
            self._request_user = request.user
            if act == "approve":
                self._aplicar(sug)
                self.message_user(request, "Sugestão aprovada e aplicada.")
            else:
                sug.status = "rejected"; sug.save(update_fields=["status", "updated_at"])
                self.message_user(request, "Sugestão rejeitada.")
            return HttpResponseRedirect(reverse("admin:glossario_suggestion_changelist"))

        if request.method == "POST":
            action = request.POST.get("action")
            self._request_user = request.user
            if action == "approve":
                self._aplicar(sug)
                self.message_user(request, "Sugestão aprovada e aplicada.")
            elif action == "reject":
                sug.status = "rejected"; sug.save(update_fields=["status", "updated_at"])
                self.message_user(request, "Sugestão rejeitada.")
            # pega próxima
            nxt = Suggestion.objects.filter(status="pending").exclude(pk=sug.pk).order_by("created_at").first()
            if nxt:
                return HttpResponseRedirect(reverse("admin:glossario_suggestion_moderar") + f"?id={nxt.pk}")
            return HttpResponseRedirect(reverse("admin:glossario_suggestion_changelist"))

        ctx = {
            **self.admin_site.each_context(request),
            "title": "Moderar sugestões",
            "sug": sug,
            "opts": Suggestion._meta,
        }
        return TemplateResponse(request, "admin/glossario/suggestion/moderar.html", ctx)

    # Ações inline na listagem
    def acoes(self, obj):
        url = reverse("admin:glossario_suggestion_moderar")
        approve = f"{url}?id={obj.pk}&action=approve"
        reject = f"{url}?id={obj.pk}&action=reject"
        return format_html("<a class='button' href='{}'>Aprovar</a> <a class='button' href='{}'>Rejeitar</a>", approve, reject)
    acoes.short_description = "Ações"

    def impacto(self, obj):
        t = obj.termo
        if not t:
            return format_html("<span class='badge-status badge-approved'>Novo termo</span>")
        def diff(a, b):
            return (a or "").strip() and (a or "").strip() != (b or "").strip()
        content = any([
            diff(obj.decod_en, t.decod_en),
            diff(obj.decod_pt, t.decod_pt),
            diff(obj.explicacao, t.explicacao),
        ])
        media = obj.imagens.exists() or obj.links.exists() or obj.videos.exists()
        if content and media:
            return format_html("<span class='badge-status badge-approved'>Conteúdo + mídia</span>")
        if content:
            return format_html("<span class='badge-status badge-approved'>Conteúdo</span>")
        if media:
            return format_html("<span class='badge-status badge-pending'>Mídia</span>")
        return format_html("<span class='badge-status badge-rejected'>Sem efeito</span>")
    impacto.short_description = "Impacto"

    # Utilitário central que aplica a sugestão ao Termo
    def _aplicar(self, s: Suggestion, request=None) -> bool:
        with transaction.atomic():
            applied = False
            termo = s.termo
            if not termo:
                if not s.titulo:
                    return False
                slug = slugify(s.titulo)
                termo, _ = Termo.objects.get_or_create(slug=slug, defaults={"titulo": s.titulo})
            changed = False
            changed_fields = []
            # Helpers
            def _clean_text(v):
                return strip_tags(v).strip() if v else ""
            def _normalize_url(u: str) -> str:
                if not u:
                    return ""
                if not re.match(r"^https?://", u, re.I):
                    return "https://" + u
                return u
            from .models import YOUTUBE_REGEX
            def _yt_id(url: str):
                m = YOUTUBE_REGEX.search(url or "")
                return m.group(1) if m else None
            # Prepare changes (compare primeiro, para evitar aprovar sem efeito)
            en_val = _clean_text(s.decod_en)
            pt_val = _clean_text(s.decod_pt)
            exp_val = _clean_text(s.explicacao)
            if en_val and en_val != (termo.decod_en or ""):
                termo.decod_en = en_val; changed = True; changed_fields.append("decod_en")
            if pt_val and pt_val != (termo.decod_pt or ""):
                termo.decod_pt = pt_val; changed = True; changed_fields.append("decod_pt")
            if exp_val and exp_val != (termo.explicacao or ""):
                termo.explicacao = exp_val; changed = True; changed_fields.append("explicacao")
            if changed:
                termo.save(); applied = True

            # copiar mídias/links/vídeos
            media_added = links_added = videos_added = 0
            # Seleciona somente imagens que não existam com mesmo nome base
            existing_basenames = {os.path.basename(ti.imagem.name) for ti in termo.imagens.all()}
            for img in s.imagens.all():
                try:
                    basename = os.path.basename(img.imagem.name)
                    if basename in existing_basenames:
                        continue
                    termo_img = TermoImage(
                        termo=termo,
                        alt_text=img.alt_text,
                        title=img.title,
                        caption=img.caption,
                    )
                    img.imagem.open("rb")
                    termo_img.imagem.save(basename, File(img.imagem.file), save=True)
                    applied = True; media_added += 1
                finally:
                    try:
                        img.imagem.close()
                    except Exception:
                        pass
                # remove arquivo da sugestão e o registro, pois foi migrado
                try:
                    storage = img.imagem.storage
                    path = img.imagem.name
                    img.delete()
                    if storage.exists(path):
                        storage.delete(path)
                except Exception:
                    pass
            for l in s.links.all():
                url = _normalize_url(l.url)
                if TermoLink.objects.filter(termo=termo, url__iexact=url).exists():
                    created = False
                else:
                    TermoLink.objects.create(termo=termo, url=url, defaults={"rotulo": l.rotulo})
                    created = True
                if created:
                    links_added += 1
                applied = applied or created
            for v in s.videos.all():
                try:
                    vid = _yt_id(v.youtube_url)
                    if not vid:
                        continue
                    if TermoVideo.objects.filter(termo=termo, youtube_id=vid).exists():
                        created = False
                    else:
                        tv = TermoVideo(termo=termo, youtube_url=v.youtube_url)
                        tv.save()
                        created = True
                    if created:
                        videos_added += 1
                    applied = applied or created
                except Exception:
                    pass

            if not applied and request is not None:
                self.message_user(request, "Nenhuma mudança efetiva a aplicar (conteúdo igual e sem novas mídias/links/vídeos).", level=messages.WARNING)
                return False

            s.status = "approved"
            s.termo = termo
            s.save(update_fields=["status", "termo", "updated_at"])
            # registra log
            try:
                from .models import SuggestionApplicationLog
                SuggestionApplicationLog.objects.create(
                    suggestion=s,
                    termo=termo,
                    approver=getattr(self, "_request_user", None),
                    fields_changed=changed_fields,
                    media_added=media_added,
                    links_added=links_added,
                    videos_added=videos_added,
                    notes=s.justification or "",
                )
            except Exception:
                pass
            return applied

    @admin.action(description="Aprovar selecionadas")
    def aprovar(self, request, queryset):
        # guarda o usuário para log
        self._request_user = request.user
        total = 0
        for s in queryset:
            if self._aplicar(s, request=request):
                total += 1
        self.message_user(request, f"Aprovadas e aplicadas {total} sugestão(ões).")

    @admin.action(description="Rejeitar selecionadas")
    def rejeitar(self, request, queryset):
        queryset.update(status="rejected")
        self.message_user(request, f"{queryset.count()} sugestão(ões) rejeitadas.")

    @admin.action(description="Aplicar ao termo (criar/atualizar)")
    def aplicar_ao_termo(self, request, queryset):
        self._request_user = request.user
        applied = 0
        for s in queryset:
            if self._aplicar(s, request=request):
                applied += 1
        self.message_user(request, f"Aplicadas {applied} sugestão(ões) ao(s) termo(s).")

    # Se o admin editar uma sugestão e mudar o status para "approved",
    # aplica automaticamente.
    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            try:
                previous_status = Suggestion.objects.get(pk=obj.pk).status
            except Suggestion.DoesNotExist:
                previous_status = None
        super().save_model(request, obj, form, change)
        if obj.status == "approved" and previous_status != "approved":
            self._request_user = request.user
            self._aplicar(obj, request=request)


@admin.register(SuggestionApplicationLog)
class SuggestionApplicationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "termo",
        "suggestion",
        "approver",
        "fields_changed",
        "media_added",
        "links_added",
        "videos_added",
    )
    list_filter = ("created_at", "approver")
    search_fields = ("termo__titulo", "suggestion__titulo", "approver__username")
    readonly_fields = list_display + ("notes",)


@admin.register(TermoHistory)
class TermoHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "termo", "created_at", "changed_by")
    search_fields = ("termo__titulo", "changed_by__username")
    list_filter = ("created_at",)
    actions = ["reverter_para_este"]

    @admin.action(description="Reverter termo para este estado")
    def reverter_para_este(self, request, queryset):
        count = 0
        for h in queryset:
            t = h.termo
            t.titulo = h.previous_titulo
            t.decod_en = h.previous_decod_en
            t.decod_pt = h.previous_decod_pt
            t.explicacao = h.previous_explicacao
            t.save()
            count += 1
        self.message_user(request, f"Revertidos {count} registro(s) de termo.")


admin.site.site_header = "Aerodicionário Superadmin"
admin.site.site_title = "Aerodicionário Superadmin"
admin.site.index_title = "Gerenciamento do Aerodicionário"


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identidade", {"fields": ("site_name", "site_logo", "favicon", "primary_color", "secondary_color")}),
        ("SEO padrão", {"fields": ("default_meta_description", "meta_keywords", "meta_title_suffix", "default_og_image", "enable_indexing", "robots_txt")}),
        ("Homepage", {"fields": ("hero_title", "hero_subtitle")}),
        ("Busca e listagem", {"fields": ("items_per_page", "enable_autocomplete", "autocomplete_throttle_ms")}),
        ("Sugestões", {"fields": ("suggestions_enabled", "suggestions_require_source", "suggestions_min_justification", "suggestion_max_image_mb", "suggestion_rate_limit_seconds")}),
        ("Social", {"fields": ("social_twitter", "social_instagram", "social_youtube", "social_linkedin")}),
        ("Rodapé", {"fields": ("footer_text",)}),
        ("Landing page", {"fields": ("hero_image", "cta_primary_text", "cta_primary_url", "cta_secondary_text", "cta_secondary_url", "show_about", "about_title", "about_html", "show_features", "features_html")}),
        ("Personalização avançada", {"classes": ("collapse",), "fields": ("custom_css", "custom_js_head", "custom_js_body", "analytics_code")}),
    )

    def has_add_permission(self, request):
        # Singleton — impede múltiplos registros
        return not SiteSetting.objects.exists()
