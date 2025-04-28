import datetime
from django.contrib.auth import authenticate, login,get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Category, Notification


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
        category_id = request.POST.get("category")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        category = get_object_or_404(Category, pk=category_id)

        if id is None:
            success, errors = Event.new(title, description, scheduled_at, request.user, category)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, category)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.filter(is_active=True)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categories": categories},
    )


def categorias(request):
    category_list = Category.objects.all()
    return render(request, "app/categories.html", 
                    {"categorys": category_list, "user_is_organizer": request.user.is_organizer})

def category_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        category = Category.objects.create(name=name, description=description)

        return redirect('categorias')

    return render(request, 'app/category_form.html')

def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name and description:
            category.name = name
            category.description = description
            category.save()
            return redirect('categorias') 
        else:
            return render(request, 'app/category_edit.html', {
                'category': category,
                'error': 'Todos los campos son obligatorios.'
            })

    return render(request, 'app/category_edit.html', {'category': category})

def category_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("categorias")

    if request.method == "POST":
        category = get_object_or_404(Category, pk=id)
        category.delete()
        return redirect("categorias")

    return redirect("categorias")

# notificacion
User = get_user_model()

def notification_form(request, id=None):
    if not request.user.is_organizer:
        return redirect("notification")
    
    notification = None
    if id is not None:
        notification = get_object_or_404(Notification, pk=id)
    
    if request.method == "POST":
        # Campos
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        user_ids = request.POST.getlist("users")
        
        event = get_object_or_404(Event, pk=event_id)
        print("user_ids:",title )

        users = User.objects.filter(id__in=user_ids)
        
        if id is None:  # Crear nueva notificación
            success, errors = Notification.new(
                title=title,
                message=message,
                priority=priority,
                users=users,
                event=event
            )
            
            if not success:
                return render(request, "app/notification_form.html", {
                    "events": Event.objects.all(),
                    "users": User.objects.all(),
                    "errors": errors,
                    "notification": notification,
                })
        else:  # Actualizar notificación existente
            # Asegúrate de que notification existe antes de intentar actualizarlo
            if notification:
                notification.update(
                    title,
                    message,
                    priority,
                    users,
                    event
                )
            else:
                # Si por alguna razón no existe, manejamos el error
                return render(request, "app/notification_form.html", {
                    "events": Event.objects.all(),
                    "users": User.objects.all(),
                    "errors": ["La notificación que intentas actualizar no existe."],
                })
        
        return redirect("notification")
    
    # GET request
    return render(request, "app/notification_form.html", {
        "notification": notification,
        "events": Event.objects.all(),
        "users": User.objects.all(),
        "user_is_organizer": request.user.is_organizer,
    })

@login_required
def notification(request):
    # Verifica si el usuario es un organizador
    if not request.user.is_organizer:
        # Si no es organizador, muestra un mensaje de error y redirige al inicio
        return redirect("home")
    
    # Obtener todos los eventos para el filtro
    events = Event.objects.all()

    # Configurar los filtros
    event_filter = request.GET.get('event', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('search', '')
    
    # Consulta base de notificaciones  
    notifications = Notification.objects.all().order_by("-created_at")
    
    # Aplicar filtros si están presentes
    if search_query:
        notifications = notifications.filter(title__icontains=search_query)
    
    if event_filter and event_filter != 'all':
        notifications = notifications.filter(event__id=event_filter)
    
    if priority_filter and priority_filter != 'all':
        notifications = notifications.filter(priority=priority_filter)
    
    return render(
        request,
        "app/notifications.html",
        {
            "notifications": notifications,
            "events": events,
            "has_notifications": notifications.exists(),
            "current_event_filter": event_filter,
            "current_priority_filter": priority_filter,
            "search_query": search_query,
        },
    )

def notification_detail(request, id):
 
    # Verifica si el usuario es un organizador
    if not request.user.is_organizer:

        return redirect("home")
    
    notification = get_object_or_404(Notification, id=id)
    
    return render(
        request,
        "app/notification_detail.html",
        {
            "notification": notification,
        },
    )

