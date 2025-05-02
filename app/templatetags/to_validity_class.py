from django import template

register = template.Library()


@register.filter
def to_validity_class(errors, field):
    if len(errors):
        if errors.get(field) is not None:
            return "is-invalid"
        return "is-valid"

    return ""
