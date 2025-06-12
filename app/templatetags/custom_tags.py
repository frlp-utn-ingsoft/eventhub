from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key): # type: ignore
    return dictionary.get(key)


