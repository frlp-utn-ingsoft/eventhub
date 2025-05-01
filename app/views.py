import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Ticket, RefundRequest


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
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


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
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def refund_form(request):
    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        additional_details = request.POST.get("additional_details")
        accepted_policy = request.POST.get("accepted_policy") == "on"

        #validaciones basicas
        if not ticket_code or not reason or not accepted_policy:
            return render(request, "app/refund_form.html", {"error": "Todos los campos son obligatorios.", "data": request.POST})

        RefundRequest.objects.create(
            ticket_code=ticket_code,
            reason=reason,
            additional_details=additional_details,
            user=request.user,
            accepted_policy=accepted_policy,
        )
        return redirect("events")
    return render(request, "app/refund_form.html")

@login_required
#funcion para ver las solicitudes de reembolso de los eventos que organiza el usuario
def organizer_refund_requests(request):
    # si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    
    #obtener todos los eventos del organizador loggeado
    organizer_events = Event.objects.filter(organizer=request.user)

    #obetener todos los tickets de esos eventos
    tickets = Ticket.objects.filter(event__in=organizer_events)

    #obtener los codigos de los tickets
    ticket_codes = [str(ticket.id) for ticket in tickets]  # Convertir IDs a string

    #obtener todas las solicitudes de reembolso de esos tickets
    refund_requests = RefundRequest.objects.filter(ticket_code__in=ticket_codes).select_related("user")

    #se crea un diccionario con los eventos y sus solicitudes de reembolso
    tickets_dict = {str(ticket.id): ticket for ticket in tickets}

    return render(request, "app/organizer_refund_requests.html", {"refund_requests": refund_requests, "tickets_dict": tickets_dict})

@login_required
def approve_refund_request(request, id):
    # si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    refund = get_object_or_404(RefundRequest, pk=id)
    #verificar si la solicitud de reembolso ya fue aprobada o rechazada
    refund.approval = True
    refund.save()
    return redirect("organizer_refund")

@login_required
def reject_refund_request(request, id):
    # si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    refund = get_object_or_404(RefundRequest, pk=id)
    #verificar si la solicitud de reembolso ya fue aprobada o rechazada
    refund.approval = False
    refund.save()
    return redirect("organizer_refund")

@login_required
def view_refund_request(request, id):
    # si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    refund = get_object_or_404(RefundRequest, pk=id)
    #verificar si la solicitud de reembolso ya fue aprobada o rechazada
    return render(request, "app/view_refund_request.html", {"refund": refund})