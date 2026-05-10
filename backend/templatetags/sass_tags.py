from django import template
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def sass_src(path):
    if path.endswith(".scss"):
        path = f"{path[:-5]}.css"
    return static(path)
