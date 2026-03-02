from django import template

register = template.Library()


@register.filter
def is_admin_or_supervisor(user):
    """Vérifie si l'utilisateur est admin ou superviseur."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, 'operatorprofile', None)
    return profile and profile.role == 'superviseur'
