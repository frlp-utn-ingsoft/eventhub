from django import template
from django.db.models import Avg
from app.models import Rating

register = template.Library()

@register.simple_tag
def average_rating(event):
    avg = Rating.objects.filter(event=event).aggregate(avg=Avg('rating'))['avg']
    return round(avg, 1) if avg is not None else None
