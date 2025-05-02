import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.models import Category, Event, Rating, Venue
from app.views.rating_views import create_rating


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    # Si es edición, verificar que sea el dueño del evento
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
        category_ids = list(map(int, request.POST.getlist('categories[]')))
        categories = None
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
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
            Event.new(title, categories, venue, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=event_id)
            # Verificar permisos antes de actualizar
            if user != event.organizer:
                messages.error(request, 'No tienes permiso para editar este evento.')
                return redirect("events")
            event.update(title, categories, venue, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.all()
    venues = Venue.get_venues_by_user(user)
    selected_categories = event.categories.all() if event else []
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
    events = Event.objects.all().order_by("scheduled_at")
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
        "event_categories": event_categories
        })


@login_required
def event_delete(request, id):
    user = request.user
    event = Event.objects.get(id=id)
    
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

@login_required
def event_filter(request):
    query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    events = []
    my_events = False

    if (filter_type == "my_events"):
        my_events = True
        events = Event.objects.filter(organizer=request.user)
        if query:
            events.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(venue__name__icontains=query)
            )
        events.order_by("scheduled_at")
    
    if (filter_type == "all"):
        if query:
            events = Event.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(venue__name__icontains=query)
            )
        else:
            events = Event.objects.all()

    return render(
        request,
        "app/event/events.html",
        {
            "events": events, 
            "user_is_organizer": request.user.is_organizer, 
            "my_events": my_events,
            "user": request.user
        },
    )