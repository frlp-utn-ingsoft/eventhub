import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Ticket
from .forms import TicketForm


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
def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'app/ticket/ticket_list.html', {'tickets': tickets})



def ticket_create(request, event_id):
    
    event = get_object_or_404(Event, pk=event_id) # Busca el evento según el ID que vino en la URL

    if request.method == 'POST':
        
        form = TicketForm(request.POST) # Crea el formulario con los datos enviados
        if form.is_valid():
            # No guarda aún el ticket en la base
            ticket = form.save(commit=False)
            # Asigna el evento y el usuario actual
            ticket.event = event
            ticket.user = request.user
            # Ahora sí, guarda el ticket
            ticket.save()
            return redirect('ticket_list')  # o podés redirigir a event_detail si querés
    else:
        # GET: crea un formulario vacío
        form = TicketForm()

    # Renderiza el formulario pasando también el evento
    return render(request, 'app/ticket/ticket_form.html', {
        'form': form,
        'event': event
    })

def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)  # busca el ticket o lanza 404
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)  # llena el form con los datos nuevos
        if form.is_valid():
            form.save()             # guarda los cambios
            return redirect('ticket_list')
    else:
        form = TicketForm(instance=ticket)  # muestra el form con datos precargados
    return render(request, 'app/ticket/ticket_form.html', {
        'form': form,
        'event': ticket.event
        }) # muestra el formulario para editar

def ticket_delete (request, pk):
    ticket = get_object_or_404(Ticket, pk=pk) # busca el ticket o lanza 404
    if request.method == 'POST':
        ticket.delete() # lo borra
        return redirect('ticket_list') # redirige a la viste de listado
    return render(request, 'app/ticket/ticket_confirm_delete.html', {'ticket': ticket}) # muestra la pantalla de confirmacion





