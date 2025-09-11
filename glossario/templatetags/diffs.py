from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import difflib

register = template.Library()


def _wrap_ops(opcodes, a, b):
    out = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            out.append(escape(''.join(a[i1:i2])))
        elif tag == 'delete':
            out.append(f"<del style='background:#fde2e2'>{escape(''.join(a[i1:i2]))}</del>")
        elif tag == 'insert':
            out.append(f"<ins style='background:#dcfce7'>{escape(''.join(b[j1:j2]))}</ins>")
        elif tag == 'replace':
            out.append(f"<del style='background:#fde2e2'>{escape(''.join(a[i1:i2]))}</del>")
            out.append(f"<ins style='background:#dcfce7'>{escape(''.join(b[j1:j2]))}</ins>")
    return ''.join(out)


@register.filter
def diff_html(old, new):
    """Return a simple inline diff between old and new as HTML with del/ins."""
    old = '' if old is None else str(old)
    new = '' if new is None else str(new)
    sm = difflib.SequenceMatcher(None, list(old), list(new))
    html = _wrap_ops(sm.get_opcodes(), list(old), list(new))
    return mark_safe(html)

