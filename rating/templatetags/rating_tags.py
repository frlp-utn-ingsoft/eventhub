from django import template
from ..models import Rating
from ..forms import RatingForm

register = template.Library()

@register.inclusion_tag("rating/rating_section.html", takes_context=True)
def render_rating(context, event):
    ratings = event.ratings.select_related("user").all()
    form = RatingForm()
    return {
        "event": event,
        "user": context["user"],
        "ratings": ratings,
        "form": form,
    }