from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from app.models import Refund, Ticket
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.views.decorators.http import require_POST

@login_required
def refund_create(request):
    user = request.user
    user_tickets = Ticket.objects.filter(user=user)

    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason      = request.POST.get("reason", "").strip()

        # Validar ticket existente y perteneciente al usuario
        ticket = Ticket.objects.filter(user=user, ticket_code=ticket_code).first()
        if not ticket:
            error = "Código de ticket inválido."
        # Validar duplicado de refund
        elif Refund.objects.filter(user=user, ticket_code=ticket_code).exists():
            error = "Ya existe una solicitud de reembolso para este ticket."
        else:
            días_transcurridos = (timezone.now().date() - ticket.buy_date).days
            if días_transcurridos > 30:
                error = "No puedes solicitar reembolso de un ticket con más de 30 días de antigüedad."
            else:
                Refund.objects.create(
                    ticket_code=ticket.ticket_code,
                    reason=reason,
                    user=user,
                    event=ticket.event
                )
                return redirect("my_refunds")

        return render(request, "refund/refund_form.html", {
            "user_tickets":  user_tickets,
            "error":         error,
            "selected_code": ticket_code,
            "reason":        reason,
        })

    return render(request, "refund/refund_form.html", {
        "user_tickets": user_tickets
    })

@login_required
def my_refunds(request):
    refunds = Refund.objects.filter(user=request.user).order_by("-created_at")
    codes = {r.ticket_code for r in refunds}
    tickets = Ticket.objects.filter(ticket_code__in=codes)
    tickets_map = {t.ticket_code: t for t in tickets}
    return render(request, "refund/my_refunds.html", {"refunds": refunds, "tickets_map": tickets_map})

@login_required
def refund_edit(request, id):
    refund_obj = get_object_or_404(Refund, id=id, user=request.user)

    if refund_obj.approved:  # Ya la vio un organizer
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
    if not refund_obj.approved:  # Ya la vio un organizer
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
    if refund_obj.approved is None:  # Verifica si es pendiente
        refund_obj.approved = True
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
    if refund_obj.approved is None:  # Verifica si es pendiente
        refund_obj.approved = False
        refund_obj.aproval_date = timezone.now()
        refund_obj.save()
        messages.success(request, "✅ Reembolso rechazado exitosamente.")
    return redirect('refunds_admin')
# views.py
@login_required
def refund_requests_admin(request):
    user = request.user
    if not is_organizer(user):
        return redirect("events")
    refunds = Refund.objects.filter(event__organizer=user).order_by("-created_at")
    codes = {r.ticket_code for r in refunds}
    tickets = Ticket.objects.filter(ticket_code__in=codes)
    tickets_map = {t.ticket_code: t for t in tickets}

    return render(request, "refund/refund_request_admin.html", {
        "refund_requests": refunds,
        "tickets_map": tickets_map,
    })