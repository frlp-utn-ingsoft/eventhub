from django import template

register = template.Library()

@register.filter
def avg_score(ratings):
    if not ratings:
        return 0
    total = sum(rating.rating for rating in ratings)
    return round(total / len(ratings), 1) 