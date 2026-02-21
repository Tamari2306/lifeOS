# Create this file at: templatetags/dict_extras.py
# inside any installed app (e.g. meals/templatetags/dict_extras.py)

from django import template

register = template.Library()


@register.filter
def dict_key(d, key):
    """Get a dictionary value by key in Django templates.
    Usage: {{ my_dict|dict_key:'some_key' }}
    """
    try:
        return d[key]
    except (KeyError, TypeError):
        return None