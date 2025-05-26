import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.models import Category, Event, Rating, Ticket, Venue
from app.views.rating_views import create_rating


from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
import datetime

@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    # Edición: verificar que sea el dueño del evento
    if id is not None:
        event = get_object_or_404(Event, pk=id)
        if user != event.organizer:
            messages.error(request, 'No tienes permiso para editar este evento.')
            return redirect("events")
    
    if request.method == "POST":
        event_id = request.POST.get("id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        # Validar presencia de date y time
        if not date or not time:
            messages.error(request, "Debes ingresar una fecha y una hora válidas.")
            return redirect(request.path)

        try:
            year, month, day = map(int, date.split("-"))
            hour, minutes = map(int, time.split(":"))
            scheduled_at = timezone.make_aware(
                datetime.datetime(year, month, day, hour, minutes)
            )
        except ValueError:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect(request.path)

        category_ids = list(map(int, request.POST.getlist('categories[]')))
        categories = Category.objects.filter(id__in=category_ids) if category_ids else []

        venue_id = request.POST.get("venue")
        venue = get_object_or_404(Venue, pk=venue_id) if venue_id else None
        
        if event_id is None:
            Event.new(title, description, scheduled_at, request.user, categories, venue)
        else:
            event = get_object_or_404(Event, pk=event_id)
            if user != event.organizer:
                messages.error(request, 'No tienes permiso para editar este evento.')
                return redirect("events")
            event.update(title, description, scheduled_at, request.user, categories, venue)

        return redirect("events")

    event = get_object_or_404(Event, pk=id) if id is not None else None
    categories = Category.objects.all()
    venues = Venue.get_venues_by_user(user)
    selected_categories = event.categories.all() if event else []  # type: ignore

    return render(
        request,
        "app/event/event_form.html",
        {
            "event": event, 
            "user_is_organizer": request.user.is_organizer, 
            "categories": categories,
            "selected_categories": selected_categories,
            "venues": venues
        },
    )


@login_required
def events(request):
    events = Event.objects.filter(scheduled_at__gt=timezone.now()).order_by("scheduled_at")
    return render(
        request,
        "app/event/events.html",
        {
            "events": events, 
            "user_is_organizer": request.user.is_organizer,
            "user": request.user
        },
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    categories = Category.objects.all()
    # Obtener todas las calificaciones de este evento
    ratings = Rating.objects.filter(event=event)

    # Verificar si el usuario tiene ticket para este evento
    has_ticket = Ticket.objects.filter(event=event, user=request.user).exists()

    # Llamar a la función `handle_rating` para manejar la calificación
    rating_saved = create_rating(request, event)

    # Si la calificación se guardó correctamente, actualizar las calificaciones
    if rating_saved:
        ratings = Rating.objects.filter(event=event)
    event_categories = event.categories.all() if event else []
        
    return render(request, "app/event/event_detail.html", {
        "event": event,
        'ratings': ratings,
        "categories": categories, 
        "user_is_organizer": request.user.is_organizer,
        "event_categories": event_categories,
        "has_ticket": has_ticket
    })


@login_required
def event_delete(request, id):
    user = request.user
    event = get_object_or_404(Event, id=id)
    
    if not user.is_organizer:
        return redirect("events")
    
    # Aca ponemos una restriccion que prohiba a un usuario 
    # borrar los eventos de otros usuarios organizadores
    if user != event.organizer:
        messages.error(request, 'No tienes permiso para eliminar este evento.')
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")

def filter_events(events, user, query, is_my_events, is_past_events, is_available_events):
    if is_my_events:
        events = events.filter(organizer=user)

    if not is_past_events:
        events = events.filter(scheduled_at__gt=timezone.now())

    # if is_available_events:
        # TO DO: Implementar filtro para eventos disponibles
        # events = ...

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(venue__name__icontains=query)
        )

    events = events.order_by("scheduled_at")
    return events

@login_required
def event_filter(request):
    query = request.GET.get('search', '')
    is_my_events = 'my_events' in request.GET
    is_past_events = 'past_events' in request.GET
    is_available_events = 'available_events' in request.GET
    events = Event.objects.all()

    filtered_events = filter_events(events, request.user, query, is_my_events, is_past_events, is_available_events)
    context = {
        'events': filtered_events,
        "user": request.user,
        'user_is_organizer': request.user.is_organizer
    }

    return render(request, "app/event/events.html", context)