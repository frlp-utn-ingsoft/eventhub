import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.models import Category, Event, Rating, Ticket, Venue
from app.views.rating_views import create_rating


@login_required
def event_form(request, id=None):
    user = request.user
    event = None
    errors = []

    if not user.is_organizer:
        return redirect("events")

    # Si es edición, obtener evento y verificar permisos/estado
    if id is not None:
        event = get_object_or_404(Event, pk=id)
        if event.organizer != user:
            return redirect("events")
        if event.status in ("canceled", "finished"):
            return redirect("events")

    # POST: procesar formulario
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        date = request.POST.get("date", "").strip()
        time = request.POST.get("time", "").strip()
        venue_id = request.POST.get("venue")
        category_ids = request.POST.getlist("categories[]")
        status = request.POST.get("status")

        # Validar campos básicos
        if not title:
            errors.append("El título es obligatorio.")
        if not description:
            errors.append("La descripción es obligatoria.")
        # Validar fecha/hora
        scheduled_at = None
        if not date or not time:
            errors.append("Debes ingresar una fecha y una hora válidas.")
        else:
            try:
                y, m, d = map(int, date.split("-"))
                hh, mm = map(int, time.split(':'))
                scheduled_at = timezone.make_aware(
                    datetime.datetime(y, m, d, hh, mm)
                )
                if scheduled_at < timezone.now():
                    errors.append("La fecha y hora deben ser en el futuro.")
            except ValueError:
                errors.append("Formato de fecha u hora inválido.")

        # Obtener venue y categorías
        venue = None
        if venue_id:
            venue = get_object_or_404(Venue, pk=venue_id)
        categories = Category.objects.filter(id__in=category_ids) if category_ids else []

        # Si no hay errores de input, llamar validación de modelo
        if not errors:
            if event is None:
                ok, model_errors = Event.new(
                    title, categories, venue, description, scheduled_at, user
                )
            else:
                ok, model_errors = event.update(
                    title, categories, venue, description, scheduled_at, user, status=status
                )
            if not ok:
                # model_errors puede ser dict o mensaje
                if isinstance(model_errors, dict):
                    errors.extend(model_errors.values())
                else:
                    errors.append(model_errors)

        # Si hay errores, re-renderizar
        if errors:
            return render(request, "app/event/event_form.html", {
                "event": event,
                "user_is_organizer": user.is_organizer,
                "categories": Category.objects.all(),
                "selected_categories": categories,
                "venues": Venue.get_venues_by_user(user),
                "errors": errors,
                "form_data": {
                    "title": title,
                    "description": description,
                    "date": date,
                    "time": time,
                    "venue_id": venue_id,
                    "category_ids": category_ids,
                    "status": status,
                }
            })

        # Si todo ok, redirigir
        return redirect("events")

    # GET: mostrar formulario
    return render(request, "app/event/event_form.html", {
        "event": event,
        "user_is_organizer": user.is_organizer,
        "categories": Category.objects.all(),
        "selected_categories": event.categories.all() if event else [],
        "venues": Venue.get_venues_by_user(user),
    })

@login_required
def events(request):
    events = Event.objects.filter(scheduled_at__gt=timezone.now()).order_by("scheduled_at")
    return render(
        request,
        "app/event/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer, "user": request.user},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
   # Obtener todas las calificaciones de este evento
    ratings = Rating.objects.filter(event=event)
    
    categories = Category.objects.all()
    
        # Llamar a la función `handle_rating` para manejar la calificación
    rating_saved = create_rating(request, event)

    # Si la calificación se guardó correctamente, actualizar las calificaciones
    if rating_saved:
        ratings = Rating.objects.filter(event=event)
    event_categories = event.categories.all() if event else []

    # Verificar si el usuario tiene ticket para este evento
    has_ticket = Ticket.objects.filter(event=event, user=request.user).exists()

    # Procesar acciones de estado
    if request.method == "POST" and request.user.is_organizer and event.organizer == request.user:
        action = (
            "canceled"  if request.POST.get("cancel_event")  == "1" else
            "finished"  if request.POST.get("finish_event")  == "1" else
            None
        )
        if action:
            ok, result = event.update(
                event.title,
                list(event.categories.all()),
                event.venue,
                event.description,
                event.scheduled_at,
                request.user,
                status=action
            )
            if not ok:
                messages.error(request, str(result))
            else:
                messages.success(
                    request,
                    "Evento cancelado." if action == "canceled" else "Evento finalizado."
                )
            return redirect("event_detail", id=event.id)

    return render(
        request,
        "app/event/event_detail.html",
        {
            "event": event,
            "ratings": ratings,
            "categories": categories,
            "user_is_organizer": request.user.is_organizer,
            "event_categories": event_categories,
            "has_ticket": has_ticket,
        },
    )

@login_required
def event_delete(request, id):
    user = request.user
    event = get_object_or_404(Event, id=id)

    if not user.is_organizer:
        return redirect("events")

    # Aca ponemos una restriccion que prohiba a un usuario
    # borrar los eventos de otros usuarios organizadores
    if user != event.organizer:
        messages.error(request, "No tienes permiso para eliminar este evento.")
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
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(venue__name__icontains=query)
        )

    events = events.order_by("scheduled_at")
    return events


@login_required
def event_filter(request):
    query = request.GET.get("search", "")
    is_my_events = "my_events" in request.GET
    is_past_events = "past_events" in request.GET
    is_available_events = "available_events" in request.GET
    events = Event.objects.all()

    filtered_events = filter_events(
        events, request.user, query, is_my_events, is_past_events, is_available_events
    )
    context = {
        "events": filtered_events,
        "user": request.user,
        "user_is_organizer": request.user.is_organizer,
    }

    return render(request, "app/event/events.html", context)
