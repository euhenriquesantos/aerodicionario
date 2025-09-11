from django import template
from glossario.models import Termo, Suggestion, SuggestionApplicationLog

register = template.Library()


@register.simple_tag
def termos_count():
    return Termo.objects.count()


@register.simple_tag
def sugestoes_pendentes_count():
    return Suggestion.objects.filter(status="pending").count()


@register.simple_tag
def sugestoes_aprovadas_count():
    return Suggestion.objects.filter(status="approved").count()


@register.simple_tag
def sugestoes_rejeitadas_count():
    return Suggestion.objects.filter(status="rejected").count()


@register.simple_tag
def latest_application_logs(limit=5):
    return (
        SuggestionApplicationLog.objects.select_related("termo", "approver", "suggestion")
        .order_by("-created_at")[:limit]
    )
