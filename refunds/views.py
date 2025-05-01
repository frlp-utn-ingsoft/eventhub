from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Refund
from .forms import RefundForm

from .forms import RefundForm
from .models import Refund

@login_required
def refundCreateView(request, refund_id=None):
    user = request.user
    refund = None

    if refund_id:
        if user.is_organizer:
            refund = get_object_or_404(Refund, id=refund_id)
        else:
            refund = get_object_or_404(Refund, id=refund_id, user=user)

    if request.method == "POST":
        form = RefundForm(request.POST, instance=refund)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.user = user
            refund.save()
            return redirect("/events/")
    else:
        form = RefundForm(instance=refund)

    return render(request, "refunds/refund_page.html", {"form": form, "refund": refund})



@login_required
def refundListView(request):
    user = request.user

    if not user.is_organizer:
        refunds = Refund.objects.filter(user=user).order_by("created_at")
    else:
        refunds = Refund.objects.all().order_by("created_at")
    
    return render(request, "refunds/refunds_list.html", {"refunds": refunds})

@login_required
def refundDeleteView(request, id):
    user = request.user
    refund = get_object_or_404(Refund,id=id)

    if not (user == refund.user):
        return redirect("/refunds/")

    if request.method == "POST":
        request.delete()
        return redirect("/refunds/")
    return render(request, "refunds/refund_confirm_delete.html", {"refund": refund})

@login_required
def refundConfirmActionView(request,id):
    user = request.user
    refund = get_object_or_404(Refund,id=id)

    if not user.is_organizer:
        return redirect("/refunds/")
    
    return render(request, "refunds/refund_confirm_action.html", {"refund": refund})