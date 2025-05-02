import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render, redirect
from django.http import HttpResponseBadRequest
from django.utils import timezone


from .models import Event, User, Ticket, TicketType


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
    user = request.user
    event = get_object_or_404(Event, pk=id)
    if not user.is_organizer:
        tickets = Ticket.objects.filter(event=event, user=user).order_by("-buy_date")
    else:
        tickets = Ticket.objects.filter(event=event).order_by("-buy_date")
    return render(request, "app/event_detail.html", {"event": event, "tickets": tickets})


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
def tickets(request, event_id=None):
    user = request.user
    tickets = Ticket.objects.filter(user=user).order_by("-buy_date")
    return render(request, "app/tickets.html", {"tickets": tickets})

@login_required
def ticket_form(request, event_id=None):
    if event_id is None:
        return HttpResponseBadRequest("Falta el parámetro event_id")
    
    ticket_types = TicketType.objects.all()
    if request.method == "POST":
        user = request.user
        ticket_type_id = int(request.POST.get("ticketType"))
        quantity = int(request.POST.get("ticketQuantity"))
        event = get_object_or_404(Event, pk=event_id)
        ticket_type = get_object_or_404(TicketType, pk=ticket_type_id)
        success, result = Ticket.new( event, user, ticket_type, quantity)
        if success:
            return redirect("ticket_detail", id=result)
        else:
            errors = result
            return render(
                request,
                "app/ticket_form.html",
                {
                    "errors": errors,
                    "data": request.POST,
                    "ticket_types": ticket_types,
                    "event_id":event_id
                },
            )
    else: return render(request, "app/ticket_form.html", {"ticket_types":ticket_types, "event_id":event_id})

@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(Ticket, ticket_code=id)
    return render(request, "app/ticket_detail.html", {"ticket": ticket})

@login_required
def ticket_delete(request, id):
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, ticket_code=id)
        success, result=ticket.delete()
        if success:
            return redirect(tickets)
        else:
            return render( request, "app/ticket_detail.html", {"ticket": ticket, "errors": result})
    else:
        return redirect("tickets")

@login_required
def ticket_update(request, id):
    ticket = get_object_or_404(Ticket, ticket_code=id)
    ticket_types = TicketType.objects.all()
    if not ticket.thirty_minutes_rule():
        return render(request, "app/ticket_detail.html", {"ticket": ticket, "errors": {"error": "El ticket solo se puede modificar en los 30 minutos posteriores a su creación"}})
    if request.method == "POST":
        ticket_type_id = request.POST.get("ticket_type")
        quantity = int(request.POST.get("quantity"))
        ticket_type = get_object_or_404(TicketType, pk=ticket_type_id)
        success, result = ticket.update(ticket_type, quantity)
        if success:
            return render(request, "app/ticket_detail.html", {"ticket": ticket})
        else:
            return render(request,"app/ticket_update.html",{"errors": result,"data": request.POST, "ticket": ticket,},)
    return render(request, "app/ticket_update.html", {"ticket_types":ticket_types,"ticket": ticket})

@login_required
def ticket_types(request):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    ticket_types = TicketType.objects.all().order_by("price")
    return render(request, "app/ticket_types.html", {"ticket_types": ticket_types})

@login_required
def ticket_type_delete(request, ticket_type_id):
    if request.method == "POST":
        user = request.user
        if not user.is_organizer:
            return redirect("events")
        ticket_type = get_object_or_404(TicketType, pk=ticket_type_id)
        ticket_type.delete()
        return redirect("ticket_types")
    else:
        return redirect("ticket_types")

@login_required
def ticket_type_form(request):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    if request.method == "POST":
        name = request.POST.get("name")
        price = float(request.POST.get("price"))
        success, result = TicketType.new(name, price)
        if success:
            return redirect("ticket_types")
        else:
            errors = result
            return render(
                request,
                "app/ticket_type_form.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )        
    else: return redirect("ticket_types")
    
@login_required
def ticket_type_update(request, ticket_type_id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    ticket_type = get_object_or_404(TicketType, pk=ticket_type_id)
    if request.method == "POST":
        price = float(request.POST.get("price"))
        success, result = ticket_type.update(price)
        if success:
            return redirect("ticket_types")
        else:
            errors = result
            return render(
                request,
                "app/ticket_type_update.html",
                {
                    "errors": errors,
                    "data": request.POST,
                    "ticket_type": ticket_type,
                },
            )
    else: return redirect("ticket_types")