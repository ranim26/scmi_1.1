from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Retourne le nom de fichier sans le chemin."""
    return os.path.basename(value)