import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User
from django.contrib import messages
from .models import Ticket, Event, TicketForm


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
def buy_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.event = event
            ticket.save()
            messages.success(request, f'¡Ticket comprado con éxito! Tu código es: {ticket.ticket_code}')
            return redirect('app/ticket_detail', ticket_id=ticket.id)
        
    else:
        form = TicketForm()
    
    return render(request, 'app/buy_ticket.html', {
        'form': form,
        'event': event
    })

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.user != ticket.user and not (request.user.is_organizer and request.user == ticket.event.organizer):
        messages.error(request, 'No tienes permiso para ver este ticket')
        return redirect('home')
    
    return render(request, 'app/ticket_detail.html', {'ticket': ticket})

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.user != ticket.user:
        messages.error(request, 'No tienes permiso para editar este ticket')
        return redirect('home')
    
    
    time_difference = timezone.now() - ticket.buy_date
    if time_difference.total_seconds() > 1800:
        messages.error(request, 'Solo puedes editar el ticket dentro de los primeros 30 minutos después de la compra')
        return redirect('app/ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket actualizado con éxito')
            return redirect('app/ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketForm(instance=ticket)
    
    return render(request, 'app/edit_ticket.html', {
        'form': form,
        'ticket': ticket
    })

@login_required
def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user != ticket.user and not (request.user.is_organizer and request.user == ticket.event.organizer):
        messages.error(request, 'No tienes permiso para eliminar este ticket')
        return redirect('home')
    
    if request.user == ticket.user:
        time_difference = timezone.now() - ticket.buy_date
        if time_difference.total_seconds() > 1800:
            messages.error(request, 'Solo puedes eliminar el ticket dentro de los primeros 30 minutos después de la compra')
            return redirect('app/ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket eliminado con éxito')
        return redirect('app/my_tickets')
    
    return render(request, 'app/delete_ticket.html', {'ticket': ticket})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-buy_date')
    return render(request, 'app/my_tickets.html', {'tickets': tickets})