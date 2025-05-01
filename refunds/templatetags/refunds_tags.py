from django import template
from ..forms import RefundForm
from ..models import Refund

register = template.Library()

@register.inclusion_tag("refunds/refund_list.html", takes_context=True)
def render_refunds(context):
    if context["user"].is_organizer:
        refunds = Refund.objects.all().order_by("-created_at")
    else:
        refunds = Refund.objects.filter(user=context["user"]).order_by("-created_at")
    return {
        "user":     context["user"],
        "refunds": refunds,
        "form":     RefundForm(),
    }
