import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Rating


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
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user_has_rated = False
    
    if request.user.is_authenticated:
        user_has_rated = event.ratings.filter(user=request.user).exists()
    
    return render(
        request,
        "app/event_detail.html",
        {
            "event": event,
            "user_is_organizer": request.user.is_organizer,
            "user_has_rated": user_has_rated
        },
    )


@login_required
def event_delete(request, event_id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=event_id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, event_id=None):
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

        if event_id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=event_id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if event_id is not None:
        event = get_object_or_404(Event, pk=event_id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def create_rating(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == "POST":
        score = int(request.POST.get("score"))
        comment = request.POST.get("comment", "")
        
        success, result = Rating.new(event, request.user, score, comment)
        
        if success:
            return redirect("event_detail", event_id=event.id)
        else:
            return render(request, "app/rating_form.html", {
                "event": event,
                "errors": result,
                "score": score,
                "comment": comment
            })
            
    return render(request, "app/rating_form.html", {"event": event})


@login_required
def edit_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)
    
    # Verificar que el usuario es el dueño de la calificación
    if rating.user != request.user:
        return redirect("event_detail", event_id=rating.event.id)
    
    if request.method == "POST":
        score = int(request.POST.get("score"))
        comment = request.POST.get("comment", "")
        
        success, result = rating.update(score, comment)
        
        if success:
            return redirect("event_detail", event_id=rating.event.id)
        else:
            return render(request, "app/rating_form.html", {
                "event": rating.event,
                "errors": result,
                "score": score,
                "comment": comment,
                "rating": rating
            })
            
    return render(request, "app/rating_form.html", {
        "event": rating.event,
        "rating": rating,
        "score": rating.score,
        "comment": rating.comment
    })


@login_required
def delete_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)
    event_id = rating.event.id
    
    # Verificar que el usuario es el dueño de la calificación o es el organizador del evento
    if rating.user != request.user and rating.event.organizer != request.user:
        return redirect("event_detail", event_id=event_id)
    
    rating.delete()
    return redirect("event_detail", event_id=event_id)
