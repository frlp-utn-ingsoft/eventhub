import datetime
from functools import wraps
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Notification

def organizer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
        if not request.user.is_organizer:
            return redirect('events')
        return view_func(request, *args, **kwargs)
    return wrapper

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
@organizer_required
def notification_form(request):
    notification = {}
    errors = {}
    success = False
    events = Event.objects.all().order_by("scheduled_at")
    users = User.objects.filter(is_organizer = False)

    if request.method == "POST":
        user_id = request.POST.get("user")
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        event = get_object_or_404(Event, id=event_id)
        recipient = request.POST.get("recipient")

        if recipient == "all_users":
            all_users = User.objects.all()
            success, errors = Notification.new(all_users, event, title, message, priority)
        else:
            user = get_object_or_404(User, id=user_id)
            single_user = []
            single_user.append(user)
            success, errors = Notification.new(single_user, event, title, message, priority)

        if success == False:
            return render(
                request,
                "app/notification_form.html",
                {
                    "notification": { title, message, priority }, 
                    "events": events, 
                    "users": users,
                    "errors": errors
                },
            )
        
        return redirect("events")
        
    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification, 
            "events": events, 
            "users": users,
            "errors": {}
        },
    )
    
