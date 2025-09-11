from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re

register = template.Library()


@register.filter
def highlight(text, query):
    if not text or not query:
        return text
    try:
        safe_text = escape(str(text))
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: f"<mark>{escape(m.group(0))}</mark>", safe_text)
        return mark_safe(highlighted)
    except re.error:
        return text
