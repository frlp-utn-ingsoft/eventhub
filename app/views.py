import datetime
from functools import wraps
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Notification, NotificationUser
from .validations.notifications import createNotificationValidations

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
def notifications(request):
    user = request.user
    
    notifications = Notification.objects.filter(users=user).order_by("-created_at")

    if user.is_organizer:
        return render(
        request,
        "app/notifications_admin.html",
        {"notifications": notifications})        

    for notification in notifications:
        link = NotificationUser.objects.filter(notification=notification, user=user).first()
        setattr(notification, 'is_read', link.is_read if link else True)
    
    new_notifications_count = Notification.objects.filter(
        notificationuser__is_read=False, 
        notificationuser__user=user).count()

    return render(
        request,
        "app/notifications.html",
        {
            "notifications": notifications,
            "new_notifications_count": new_notifications_count
        },
    )

@login_required
@organizer_required
def notification_detail(request, id):
    notification = get_object_or_404(Notification, pk=id)
    return render(request, "app/notification_detail.html", {"notification": notification})

@login_required
@organizer_required
def notification_edit(request, id):
    notification = get_object_or_404(Notification, pk=id)
    events = Event.objects.all().order_by("scheduled_at")
    users = User.objects.filter(is_organizer = False)
    errors = {}

    if request.method == "POST":
        user_id = request.POST.get("user")
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        event = get_object_or_404(Event, id=event_id)
        recipient_type = request.POST.get("recipient_type")

        users = []
        if recipient_type == "all_users":
            users = User.objects.all()
        else:
            user = get_object_or_404(User, id=user_id)
            users.append(user)
        
        validations_pass, errors = createNotificationValidations(users, event, title, message, priority)
        if validations_pass == False:
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
        
        notification = get_object_or_404(Notification, pk=id)
        notification.update(users, event, title, message, priority)

        return redirect("notifications")

    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification, 
            "events": events, 
            "users": users,
            "errors": errors
        },
    )
    
@login_required
@organizer_required
def notification_delete(request, id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=id)
        notification.delete()

    return redirect("notifications")

@login_required
@organizer_required
def notification_form(request):
    notification = {}
    errors = {}
    events = Event.objects.all().order_by("scheduled_at")
    users = User.objects.filter(is_organizer = False)

    if request.method == "POST":
        user_id = request.POST.get("user")
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        event = get_object_or_404(Event, id=event_id)
        recipient_type = request.POST.get("recipient_type")

        users = []
        if recipient_type == "all_users":
            users = User.objects.all()
        else:
            user = get_object_or_404(User, id=user_id)
            users.append(user)
        
        validations_pass, errors = createNotificationValidations(users, event, title, message, priority)
        if validations_pass == False:
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
        
        Notification.new(users, event, title, message, priority)

        return redirect("notifications")
        
    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification, 
            "events": events, 
            "users": users,
            "errors": errors
        },
    )
    
def mark_all_as_read(request):
    user = request.user

    NotificationUser.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)

    return redirect("notifications")

def mark_as_read(request, id):
    user = request.user
    notification = get_object_or_404(Notification, pk=id)
    notification.mark_as_read(user.id)

    return redirect("notifications")
