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