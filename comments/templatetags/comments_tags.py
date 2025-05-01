from django import template
from ..forms import CommentForm

register = template.Library()

@register.inclusion_tag("comments/comments_section.html", takes_context=True)
def render_comments(context, event):
    """Dibuja lista y formulario de comentarios."""
    return {
        "event":    event,
        "user":     context["user"],
        "comments": event.comments.select_related("user"),
        "form":     CommentForm(),
    }
