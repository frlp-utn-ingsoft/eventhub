import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import RefundForm
from .models import Refund

@login_required
def refundCreateView(request):
    user = request.user

    if request.method == "POST":
        form = RefundForm(request.POST)

        if form.is_valid():
           
            refund = form.save(commit=False)
            refund.user = user
            refund.save()

            return redirect("/events/")
        pass
    else:
        form = RefundForm()

    return render(request, "refunds/refund_page.html", {"form": form})

@login_required
def refundListView(request):
    logged_user = request.user

    if not logged_user.is_organizer:
        refunds = Refund.objects.filter(user=logged_user).order_by("created_at")
    else:
        refunds = Refund.objects.all().order_by("created_at")
    
    return render(request, "refunds/refunds_list.html", {"refunds": refunds})
