from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from app.models import Refund
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.views.decorators.http import require_POST

@login_required
def refund_create(request):
    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        
        """
        DESCOMENTAR CUANDO SE IMPLEMENTE LA PARTE DE TICKETS

        if ticket.was_used or (timezone.now() - ticket.purchase_date).days > 30:
            return render(
                request,
                "app/refund_form.html",
                {"error": "El ticket ya fue usado o han pasado más de 30 días desde su compra."}
            )
            """
        Refund.objects.create(ticket_code=ticket_code,
                              reason=reason,
                              user=request.user)

        return redirect("my_refunds")
    return render(request, "refund/refund_form.html")

@login_required
def my_refunds(request):
    refunds = Refund.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "refund/my_refunds.html", {"refunds": refunds})

@login_required
def refund_edit(request, id):
    refund_obj = get_object_or_404(Refund, id=id, user=request.user)

    if refund_obj.aproved:  # Ya la vio un organizer
        return redirect("my_refunds")

    if request.method == "POST":
        refund_obj.ticket_code = request.POST.get("ticket_code")
        refund_obj.reason = request.POST.get("reason")
        refund_obj.save()
        return redirect("my_refunds")

    return render(request, "refund/refund_form.html", {"refund": refund_obj})

@login_required
def refund_delete(request, id):
    refund_obj = get_object_or_404(Refund, id=id, user=request.user)
    if not refund_obj.aproved:  # Ya la vio un organizer
        refund_obj.delete()

    return redirect("my_refunds")



# ORGANIZER

def is_organizer(user):
    return user.is_authenticated and user.is_organizer


from django.utils import timezone

@login_required
@require_POST
def approve_refund_request(request, pk):
    if not is_organizer(request.user):
        messages.error(request, "No tienes permisos para aprobar reembolsos.")
        return redirect('refunds_admin')

    refund_obj = get_object_or_404(Refund, pk=pk)
    if refund_obj.aproved is None:  # Verifica si es pendiente
        refund_obj.aproved = True
        refund_obj.aproval_date = timezone.now()
        refund_obj.save()
        messages.success(request, "✅ Reembolso aprobado exitosamente.")
    return redirect('refunds_admin')

@login_required
@require_POST
def reject_refund_request(request, pk):
    if not is_organizer(request.user):
        messages.error(request, "No tienes permisos para rechazar reembolsos.")
        return redirect('refunds_admin')

    refund_obj = get_object_or_404(Refund, pk=pk)
    if refund_obj.aproved is None:  # Verifica si es pendiente
        refund_obj.aproved = False
        refund_obj.aproval_date = timezone.now()
        refund_obj.save()
        messages.success(request, "✅ Reembolso rechazado exitosamente.")
    return redirect('refunds_admin')

class RefundRequestsAdminView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Refund
    template_name = "refund/refund_request_admin.html"
    context_object_name = "refund_requests"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_organizer

    def handle_no_permission(self):
        return redirect("events")
  