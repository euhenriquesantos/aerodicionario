from django import template
import os

register = template.Library()


@register.simple_tag
def image_srcset(image_field):
    if not image_field:
        return ""
    storage = image_field.storage
    name = image_field.name
    root, ext = os.path.splitext(name)
    parts = []
    for w in (320, 640, 1280):
        variant = f"{root}_w{w}.webp"
        if storage.exists(variant):
            try:
                url = storage.url(variant)
                parts.append(f"{url} {w}w")
            except Exception:
                continue
    return ", ".join(parts)

