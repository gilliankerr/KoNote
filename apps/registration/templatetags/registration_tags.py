"""Template tags and filters for the registration app."""
from django import template

register = template.Library()


@register.filter
def get_field(form, field_name):
    """Get a form field by name.

    Usage: {{ form|get_field:"field_name" }}

    Returns the BoundField object for the given field name,
    or None if the field doesn't exist.
    """
    try:
        return form[field_name]
    except KeyError:
        return None
