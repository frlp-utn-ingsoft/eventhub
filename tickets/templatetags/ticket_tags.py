from django import template
from django.template.defaultfilters import floatformat

#Funciones para utilizar en los templates

register = template.Library()

@register.simple_tag
def calculate_ticket_price(ticket_type=None):
    """
    Calcula el precio base de un ticket.
    Si se proporciona un ticket_type, usa su precio, de lo contrario devuelve 0.
    """
    if ticket_type and hasattr(ticket_type, 'price'):
        return ticket_type.price
    return 0

@register.filter
def multiply(value, arg):
    """
    Multiplica el valor por el argumento.
    Uso: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value