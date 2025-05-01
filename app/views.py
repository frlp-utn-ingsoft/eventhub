import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Category, Event, User, Venue, refund, Ticket
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/event/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    categories = Category.objects.all()
    return render(request, "app/event/event_detail.html", {"event": event, "categories": categories, "user_is_organizer": request.user.is_organizer})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event_id = request.POST.get("id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        category_id = request.POST.get("category")
        category = None
        if category_id is not None:
            category = get_object_or_404(Category, pk=category_id)
        venue_id = request.POST.get("venue")
        venue = None
        if venue_id is not None:
            venue = get_object_or_404(Venue, pk=venue_id)
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if event_id is None:
            Event.new(title, category, venue, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=event_id)
            event.update(title, category, venue, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.all()
    venues = Venue.get_venues_by_user(user)
    return render(
        request,
        "app/event/event_form.html",
        {
            "event": event, 
            "user_is_organizer": request.user.is_organizer, 
            "categories": categories, 
            "venues": venues
        },
    )

@login_required
def category_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("name")
        description = request.POST.get("description")
        if id is None:
            Category.new(title, description, is_active=True)
        else:
            category = get_object_or_404(Category, pk=id)
            category.update(title, description, request.user, is_active=True)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # refresh last screen


@login_required
def venue_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")
        capacity = int(request.POST.get("capacity"))
        contact = request.POST.get("contact")
        if id is None:
            success, data = Venue.new(name, address, city, capacity, contact, user)
            if not success: 
                return render(
                    request,
                    "app/venue/venue_form.html",
                    {
                        "errors": data,
                        "venue": venue, 
                        "user_is_organizer": request.user.is_organizer, 
                        "venues": venues
                    },
                )
        else:
            venue = get_object_or_404(Venue, pk=id)
            venue.update(name, address, city, capacity, contact)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # refresh last screen

    venue = {}
    if id is not None:
        venue = get_object_or_404(Venue, pk=id)

    venues = Venue.get_venues_by_user(user)
    return render(
        request,
        "app/venue/venue_form.html",
        {
            "venue": venue, 
            "user_is_organizer": request.user.is_organizer, 
            "venues": venues
        },
    )


@login_required
def Refund_create(request):
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
        refund.objects.create(ticket_code=ticket_code,
                              reason=reason,
                              user=request.user)
        


        return redirect("my_refunds")
    return render(request, "refund/refund_form.html")

@login_required
def My_refunds(request):
    refunds = refund.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "refund/my_refunds.html", {"refunds": refunds})

@login_required
def Refund_edit(request, id):
    refund_obj = get_object_or_404(refund, id=id, user=request.user)

    if refund_obj.aproved:  # Ya la vio un organizer
        return redirect("my_refunds")

    if request.method == "POST":
        refund_obj.ticket_code = request.POST.get("ticket_code")
        refund_obj.reason = request.POST.get("reason")
        refund_obj.save()
        return redirect("my_refunds")

    return render(request, "refund/refund_form.html", {"refund": refund_obj})

@login_required
def Refund_delete(request, id):
    refund_obj = get_object_or_404(refund, id=id, user=request.user)
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

    refund_obj = get_object_or_404(refund, pk=pk)
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

    refund_obj = get_object_or_404(refund, pk=pk)
    if refund_obj.aproved is None:  # Verifica si es pendiente
        refund_obj.aproved = False
        refund_obj.aproval_date = timezone.now()
        refund_obj.save()
        messages.success(request, "✅ Reembolso rechazado exitosamente.")
    return redirect('refunds_admin')

class RefundRequestsAdminView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = refund
    template_name = "refund/refund_request_admin.html"
    context_object_name = "refund_requests"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_organizer

    def handle_no_permission(self):
        return redirect("events")
    
@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-buy_date')
    return render(request, "app/ticket/my_tickets.html", {"tickets": tickets})


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    user = request.user

    # Solo el dueño o el organizador del evento pueden eliminar
    if ticket.user == user or (user.is_organizer and ticket.event.organizer == user):
        if request.method == "POST":
            ticket.delete()
    return redirect("my_tickets")


@login_required
def purchase_ticket(request, event_id):
    """
    Vista para crear un nuevo Ticket usando Ticket.new()
    """
    user = request.user
    if user.is_organizer:
        return redirect("event_detail", id=event_id)

    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        qty   = int(request.POST.get("quantity", 1))
        ttype = request.POST.get("type", "GENERAL")
        success, result = Ticket.new(user, event, qty, ttype)
        if not success:
            # result es un dict de errores
            return render(request, "app/ticket/purchase_ticket.html", {
                "event": event,
                "errors": result,
                "ticket_types": dict(Ticket.TICKET_TYPES).keys()
            })
        return redirect("my_tickets")

    return render(request, "app/ticket/purchase_ticket.html", {
        "event": event,
        "ticket_types": dict(Ticket.TICKET_TYPES).keys()
    })


@login_required
def edit_ticket(request, ticket_id):
    """
    Vista para editar un Ticket existente usando ticket.update()
    """
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)

    if request.method == "POST":
        qty   = int(request.POST.get("quantity", ticket.quantity))
        ttype = request.POST.get("type", ticket.type)
        success, errors = ticket.update(qty, ttype)
        if not success:
            return render(request, "app/ticket/purchase_ticket.html", {
                "ticket": ticket,
                "event": ticket.event,
                "errors": errors,
                "ticket_types": dict(Ticket.TICKET_TYPES).keys()
            })
        return redirect("my_tickets")

    return render(request, "app/ticket/purchase_ticket.html", {
        "ticket": ticket,
        "event": ticket.event,
        "ticket_types": dict(Ticket.TICKET_TYPES).keys()
    })
