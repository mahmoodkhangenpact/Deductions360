from django import template

register = template.Library()

@register.filter(name='getattr')
def getattr_filter(obj, attr):
    """Custom template filter to get an attribute of an object."""
    try:
        return getattr(obj, attr)
    except AttributeError:
        return None