import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Comment, Notification
from django.contrib import messages

from .models import Event, User, Rating, Category
from .forms import CategoryForm


def is_organizer(user):
    return user.is_organizer


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
    
    categories = Category.objects.filter(is_active=True)
    event_categories = []
    event = {}

    if event_id is not None:
        event = get_object_or_404(Event, pk=event_id)
        event_categories = [category.id for category in event.categories.all()]

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        categories = request.POST.getlist("categories")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if event_id is None:
            Event.new(title, description, scheduled_at, request.user, categories)
        else:
            event = get_object_or_404(Event, pk=event_id)
            event.update(title, description, scheduled_at, request.user, categories)

        return redirect("events")

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            "event_categories": event_categories,
            "user_is_organizer": request.user.is_organizer
        },
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


@login_required
def add_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        user = request.user
        title = request.POST.get("title")
        text = request.POST.get("text")
        Comment.objects.create(
            title=title,
            text=text,
            event=event,
            user=user
        )
        return redirect("event_detail", event_id=event_id)
    return redirect("event_detail", event_id=event_id)


@login_required
def delete_comment(request, event_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id=event_id)
    if comment.user == request.user or request.user.is_organizer:
        if request.method == "POST":
            comment.delete()
            return redirect("event_detail", event_id=event_id)
        return redirect("event_detail", event_id=event_id)
    else:
        return redirect("event_detail", event_id=event_id)


@login_required
def update_comment(request, event_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id=event_id)
    if comment.user == request.user or request.user.is_organizer:
        if request.method == "POST":
            title = request.POST.get("title")
            text = request.POST.get("text")
            comment.update(title, text)
            return redirect("event_detail", event_id=event_id)
    else:
        return redirect("event_detail", event_id=event_id)
    return render(request, "app/update_comment.html", {"comment": comment, "event_id": event_id})


@login_required
def categories(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'app/categories.html', {'categories': categories})


@login_required
def category_form(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"
        
        success, result = Category.new(name, description, is_active)
        
        if success:
            return redirect('categories')
        
        return render(request, 'app/category_form.html', {
            'errors': result,
            'data': {
                'name': name,
                'description': description,
                'is_active': is_active
            }
        })
        
    return render(request, 'app/category_form.html', {
        'data': {
            'is_active': True
        }
    })


@login_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"
        
        success, errors = category.update(
            name=name,
            description=description,
            is_active=is_active
        )
        
        if success:
            return redirect('categories')
            
        return render(request, 'app/category_form.html', {
            'category': category,
            'errors': errors,
            'data': {
                'name': name,
                'description': description,
                'is_active': is_active
            }
        })
    
    return render(request, 'app/category_form.html', {
        'category': category,
        'data': {
            'name': category.name,
            'description': category.description,
            'is_active': category.is_active
        }
    })


@login_required
def category_delete(request, category_id):
    if request.method == "POST":
        category = get_object_or_404(Category, id=category_id)
        category.delete()
    return redirect('categories')


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
def notification_edit(request, notification_id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=notification_id)

    if request.method == "POST":
        notification.title = request.POST.get("title")
        notification.message = request.POST.get("message")
        notification.priority = request.POST.get("priority")
        recipient_ids = request.POST.getlist("recipients")
        notification.users.set(recipient_ids)
        notification.save()
        return redirect("notification_list")

    users = User.objects.filter(is_organizer=False)
    return render(request, "notifications/form.html", {"notification": notification, "users": users})


@login_required
def notification_delete(request, notification_id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=notification_id)
    notification.delete()
    return redirect("notification_list")


@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)

    if not request.user.is_organizer and request.user not in notification.users.all():
        return redirect("notification_list")

    return render(request, "notifications/detail.html", {"notification": notification})


@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, users=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.update(is_read=True)
    return redirect('notification_list')
