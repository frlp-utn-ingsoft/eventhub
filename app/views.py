import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Comment, Notification
from django.contrib import messages

def add_comment(request,id):
    event = get_object_or_404(Event, pk=id)
    if request.method == "POST":
        user = request.user
        title = request.POST.get("title")
        text = request.POST.get("text")
        Comment.objects.create(
            title=title,
            text=text,
            event=event,
            user = user
        )
        return redirect("event_detail", id=id)
    return redirect("event_detail", id=id)


def delete_comment(request,id,comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id = id)
    if comment.user == request.user or request.user.is_organizer == True:
        if request.method == "POST":
            comment.delete()
            return redirect("event_detail",id=id)
        return redirect("event_detail",id=id)
    else:
        return redirect("event_detail",id=id)
     
        
def update_comment(request,id,comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id = id)
    if comment.user == request.user or request.user.is_organizer == True:
        if request.method == "POST":
            title = request.POST.get("title")
            text = request.POST.get("text")
            comment.update(title, text)
            return redirect("event_detail",id=id)
    else:
        return redirect("event_detail",id=id)
    return render(request, "app/update_comment.html", {"comment": comment, "event_id": id})
    

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
    return render(request, "app/event_detail.html", {"event": event, "user_is_organizer": request.user.is_organizer})


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
def notification_list(request):
    if request.user.is_organizer:
        notifications = Notification.objects.all().order_by('-created_at')
        return render(request, "notifications/list.html", {"notifications": notifications, "user_is_organizer": request.user.is_organizer})
    else:
        notifications = Notification.objects.filter(users=request.user).order_by('-created_at')
        notifications_not_read = Notification.objects.filter(users=request.user, is_read=False).order_by('-created_at')
        return render(request, "notifications/list.html", {"notifications": notifications, "notifications_not_read": notifications_not_read, "user_is_organizer": request.user.is_organizer})


@login_required
def notification_create(request):
    if not request.user.is_organizer:
        return redirect("notification_list")

    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        destinatario = request.POST.get("destinatario")
        event_id = request.POST.get("event_id")
        usuario_id = request.POST.get("usuario_id")

        if not event_id:
            messages.error(request, "Debe seleccionar un evento.")
            return redirect("notification_create")

        event = get_object_or_404(Event, id=event_id)

        if destinatario == "usuario":
            if not usuario_id:
                messages.error(request, "Debe seleccionar un usuario.")
                return redirect("notification_create")

        notification = Notification.objects.create(
            title=title,
            message=message,
            event=event,
            priority=priority,
            created_at=timezone.now(),
        )

        if destinatario == "todos":
            # Obtener todos los asistentes al evento (suponiendo que existe una relación many-to-many Event <-> User)
            asistentes = event.attendees.all()
            notification.users.set(asistentes)

        elif destinatario == "usuario" and usuario_id:
            usuario = get_object_or_404(User, pk=usuario_id)
            notification.users.set([usuario])

        notification.save()
        return redirect("notification_list")

    eventos = Event.objects.all()
    usuarios = User.objects.filter(is_organizer=False)
    return render(request, "notifications/form.html", {
        "eventos": eventos,
        "usuarios": usuarios,
    })


@login_required
def notification_edit(request, id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=id)

    if request.method == "POST":
        notification.title = request.POST.get("title")
        notification.message = request.POST.get("message")
        notification.priority = request.POST.get("priority")
        recipient_ids = request.POST.getlist("recipients")
        notification.recipients.set(recipient_ids)
        notification.save()
        return redirect("notification_list")

    users = User.objects.filter(is_organizer=False)
    return render(request, "notifications/form.html", {"notification": notification, "users": users})


@login_required
def notification_delete(request, id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=id)
    notification.delete()
    return redirect("notification_list")


@login_required
def notification_detail(request, id):
    notification = get_object_or_404(Notification, pk=id)

    if not request.user.is_organizer and request.user not in notification.recipients.all():
        return redirect("notification_list")

    return render(request, "notifications/detail.html", {"notification": notification})

@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, users=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.update(is_read=True)
    return redirect('notification_list')